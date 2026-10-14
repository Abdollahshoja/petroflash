"""Compare committed PetroFlash revisions without changing the working tree.

Uses only the Python standard library. Run from the repository root:
python tools/benchmark_flash.py --base f76fccb --head HEAD --rounds 3
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib
import io
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile


def build_cases():
    cases = []
    names = ['methane', 'ethane', 'propane', 'n-butane', 'n-pentane', 'n-hexane']
    rng = random.Random(42)
    def add(label, components, percentages, temperature, pressure, kij=0.0):
        cases.append(dict(id=label, names=components, percentages=percentages,
                          temperature_k=temperature, pressure_pa=pressure, kij=kij))
    for index in range(20):
        raw = [rng.uniform(0.05, 0.35) for _ in names]
        total = sum(raw)
        add(f'six-component-{index+1:02}', names, [100*v/total for v in raw], 300, 5e6)
    for pressure in (1e5, 2e5, 3e5, 5e6):
        add(f'propane-butane-{pressure/1e5:g}-bar', ['propane', 'n-butane'],
            [60, 40], 268.15, pressure)
    for kij in (0.0, 0.02, -0.02):
        add(f'methane-butane-kij-{kij:g}', ['methane', 'n-butane'],
            [50, 50], 250, 2e6, kij)
    add('reference-six-component', names, [40, 15, 15, 10, 10, 10], 300, 5e6)
    add('zero-feed-ethane', ['methane', 'ethane', 'n-butane'], [50, 0, 50], 250, 2e6)
    return cases


def exact(value):
    # Hex encoding distinguishes exact floats, including the sign of zero.
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('Nonfinite float in flash output.')
        return {'__float_hex__': value.hex()}
    if isinstance(value, dict):
        return {key: exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact(item) for item in value]
    return value


def clear_caches():
    for module in ('pr_mixing', 'pr_phase', 'pr_pure', 'tpd'):
        loaded = importlib.import_module('petroflash.' + module)
        for obj in vars(loaded).values():
            if getattr(obj, '__module__', None) == loaded.__name__:
                clear = getattr(obj, 'cache_clear', None)
                if clear is not None:
                    clear()


def worker(args):
    snapshot = Path(args.snapshot).resolve()
    sys.path.insert(0, str(snapshot / 'src'))
    import petroflash
    from petroflash.database import ComponentDatabase
    from petroflash.mixture import Mixture
    from petroflash.conditions import TPConditions
    from petroflash.flash import flash_tp
    if Path(petroflash.__file__).resolve().parent != snapshot / 'src' / 'petroflash':
        raise RuntimeError('Imported PetroFlash from an unexpected location.')
    database = ComponentDatabase.from_file(snapshot / 'data' / 'components.json')
    cases = json.loads(Path(args.cases_file).read_text(encoding='utf-8'))
    inputs = []
    for case in cases:
        mixture = Mixture.from_mole_percentages(database, case['names'], case['percentages'])
        conditions = TPConditions(case['temperature_k'], case['pressure_pa'])
        n = len(case['names'])
        kij = tuple(tuple(0.0 if i == j else case['kij'] for j in range(n))
                    for i in range(n))
        inputs.append((mixture, conditions, kij))
    # Warm imports/interpreter outside measured intervals; caches cleared below.
    mixture, conditions, kij = inputs[0]
    flash_tp(mixture, conditions, kij=kij)
    output, cold_ms = [], []
    for mixture, conditions, kij in inputs:
        clear_caches()
        start = time.perf_counter_ns()
        result = flash_tp(mixture, conditions, kij=kij)
        cold_ms.append((time.perf_counter_ns()-start)/1e6)
        output.append(asdict(result))
    index = next(i for i, case in enumerate(cases) if case['id'] == 'reference-six-component')
    mixture, conditions, kij = inputs[index]
    clear_caches()
    expected = exact(asdict(flash_tp(mixture, conditions, kij=kij)))
    warm_ms = []
    for _ in range(args.warm_repeats):
        start = time.perf_counter_ns()
        result = flash_tp(mixture, conditions, kij=kij)
        warm_ms.append((time.perf_counter_ns()-start)/1e6)
        if exact(asdict(result)) != expected:
            raise RuntimeError('Repeated calls produced different outputs.')
    if expected != exact(output[index]):
        raise RuntimeError('Cold and warm outputs differ.')
    Path(args.worker_output).write_text(json.dumps(dict(
        cold_ms=cold_ms, warm_reference_ms=warm_ms, exact_results=exact(output),
        statuses=dict(Counter(item['status'] for item in output)),
    )), encoding='utf-8')


def git(root, *command):
    result = subprocess.run(['git', '-C', str(root), *command], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def snapshot(root, sha, target):
    data = git(root, 'archive', '--format=zip', sha, 'src/petroflash', 'data/components.json')
    target.mkdir()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            destination = (target / item.filename).resolve()
            if not destination.is_relative_to(target.resolve()):
                raise RuntimeError('Unsafe path in Git archive.')
        archive.extractall(target)


def differences(a, b, path='results'):
    if type(a) is not type(b):
        return [path + ': type differs']
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [path + ': fields differ']
        return [difference for key in a for difference in differences(a[key], b[key], path+'.'+key)]
    if isinstance(a, list):
        if len(a) != len(b):
            return [path + ': length differs']
        return [difference for i, pair in enumerate(zip(a, b))
                for difference in differences(*pair, path=f'{path}[{i}]')]
    return [] if a == b else [path + f': {a!r} != {b!r}']


def run(args):
    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError('Report already exists; choose another --output path.')
    root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel').decode().strip())
    refs = {key: git(root, 'rev-parse', '--verify', value+'^{commit}').decode().strip()
            for key, value in [('base', args.base), ('head', args.head)]}
    changes = git(root, 'status', '--porcelain', '--', 'src/petroflash', 'data/components.json')
    if changes.strip():
        raise RuntimeError('Commit or review pending source/data changes first. Benchmark uses committed revisions.')
    cases = build_cases()
    records = {'base': [], 'head': []}
    with tempfile.TemporaryDirectory(prefix='petroflash-benchmark-') as temporary:
        temp = Path(temporary)
        for key, sha in refs.items():
            snapshot(root, sha, temp/key)
        bank_hashes = {key: hashlib.sha256((temp/key/'data/components.json').read_bytes()).hexdigest()
                       for key in refs}
        if len(set(bank_hashes.values())) != 1:
            raise RuntimeError('Component datasets differ; performance-only comparison requires the same dataset.')
        cases_file = temp / 'cases.json'
        cases_file.write_text(json.dumps(cases), encoding='utf-8')
        for round_index in range(args.rounds):
            order = ('base', 'head') if round_index % 2 == 0 else ('head', 'base')
            for key in order:
                print(f'Round {round_index+1}/{args.rounds}: {key} {refs[key][:7]}', flush=True)
                worker_output = temp / f'{key}-{round_index}.json'
                command = [sys.executable, '-I', str(Path(__file__).resolve()), '--worker',
                           '--snapshot', str(temp/key), '--cases-file', str(cases_file),
                           '--worker-output', str(worker_output),
                           '--warm-repeats', str(args.warm_repeats)]
                child = subprocess.run(command, cwd=temp/key, capture_output=True, text=True)
                if child.returncode:
                    raise RuntimeError(child.stderr.strip() or child.stdout.strip())
                records[key].append(json.loads(worker_output.read_text(encoding='utf-8')))
    reference = records['base'][0]['exact_results']
    mismatches = []
    for key, rounds in records.items():
        for index, record in enumerate(rounds):
            mismatches.extend(f'{key} round {index+1}: '+item
                              for item in differences(reference, record['exact_results']))
    summary = {}
    for key, rounds in records.items():
        cold_totals = [sum(record['cold_ms']) for record in rounds]
        warm = [value for record in rounds for value in record['warm_reference_ms']]
        summary[key] = dict(commit=refs[key], cold_batch_ms=cold_totals,
                            cold_batch_median_ms=statistics.median(cold_totals),
                            warm_reference_median_ms=statistics.median(warm),
                            statuses=rounds[0]['statuses'])
    speedups = {}
    for field in ('cold_batch_median_ms', 'warm_reference_median_ms'):
        before, after = summary['base'][field], summary['head'][field]
        speedups[field] = dict(ratio=before/after, time_reduction_percent=100*(1-after/before))
    report = dict(schema_version=1, utc_time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform()),
                  dataset_sha256=bank_hashes['base'], cases=cases, rounds=args.rounds,
                  warm_repeats=args.warm_repeats, timings=summary, speedups=speedups,
                  exact_output_match=not mismatches, mismatch_count=len(mismatches),
                  first_mismatches=mismatches[:20], measurements=records,
                  scope='Flash calls only; excludes import, input construction, GUI and I/O. '
                        'Finite regression cases, not experimental or global-stability validation.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Exact output match: {not mismatches} ({len(cases)} cases, {args.rounds} rounds)')
    for field, label in [('cold_batch_median_ms', 'Cold batch (29 cases)'),
                         ('warm_reference_median_ms', 'Warm reference (one flash)')]:
        print(f'{label}: {summary["base"][field]:.3f} -> {summary["head"][field]:.3f} ms; '
              f'speedup {speedups[field]["ratio"]:.2f}x')
    print('Report:', output)
    return 2 if mismatches else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='f76fccb')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--warm-repeats', type=int, default=10)
    parser.add_argument('--output', default='benchmark-results/flash-comparison.json')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--snapshot', help=argparse.SUPPRESS)
    parser.add_argument('--cases-file', help=argparse.SUPPRESS)
    parser.add_argument('--worker-output', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.rounds < 1 or args.warm_repeats < 1:
        parser.error('rounds and warm-repeats must be positive')
    try:
        if args.worker:
            worker(args)
            return 0
        return run(args)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
