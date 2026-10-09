"""Run a binary PR numerical verification campaign against the SAME database.

Run from repo root: python tools/validate_tp_flash.py
Outputs a JSON audit trail and Markdown summary; no solver files are changed.
Optional numerical-reference dependencies: numpy and scipy.
"""

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

try:
    import numpy
    import scipy
    if __package__:
        from .pr_binary_reference import BinaryPRReference
    else:
        from pr_binary_reference import BinaryPRReference
except ImportError as error:
    raise SystemExit(f'Reference dependencies unavailable: {error}\n'
                     f'Install with: "{sys.executable}" -m pip install numpy scipy')

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.flash import flash_tp
import petroflash.flash as flash_module


def git_value(*args):
    try:
        return subprocess.check_output(['git', *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'unavailable'


def compare(engine, reference, grid):
    if engine.get('status') == 'error':
        return 'UNRESOLVED', {}, 'PetroFlash raised an error.'
    if engine['status'] == 'two_phase':
        if reference['status'] != 'two_phase':
            return 'UNRESOLVED', {}, 'Independent two-phase solve unavailable.'
        errors = dict(beta=abs(engine['beta']-reference['beta']),
            x=abs(engine['liquid_composition'][0]-reference['x_methane']),
            y=abs(engine['vapor_composition'][0]-reference['y_methane']),
            z_liquid=abs(engine['liquid_z']-reference['z_liquid']),
            z_vapor=abs(engine['vapor_z']-reference['z_vapor']))
        checks = (max(errors.values()) <= 2e-6 and engine['fugacity_residual'] <= 1e-8
                  and engine['material_residual'] <= 1e-10
                  and engine['normalization_residual'] <= 1e-10
                  and engine['gibbs_change_rt'] < 0)
        return ('PASS' if checks else 'FAIL'), errors, 'Two-phase numerical cross-check.'
    if engine['status'] == 'single_phase_candidate':
        if reference['status'] == 'two_phase' or grid['minimum_tpd'] < -1e-7:
            return 'FAIL', {}, 'Independent calculation contradicts the no-split candidate.'
        return 'LIMITED', {}, 'No contradiction on the grid; not a global stability certificate.'
    return 'UNRESOLVED', {}, 'PetroFlash did not accept a phase split.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='data/components.json')
    parser.add_argument('--output', default='validation-results')
    args = parser.parse_args()
    database_path = Path(args.database)
    db = ComponentDatabase.from_file(database_path)
    names = ['methane', 'n-butane']
    components = db.select(names)
    properties = [dict(name=c.name, cas=c.cas_number, Tc_K=c.critical_temperature.value,
        Pc_Pa=c.critical_pressure.value, omega=c.acentric_factor.value) for c in components]
    cases = [dict(id=f'T{t:g}_P{p:g}_z{z:g}_k{k:g}', T=t, bar=p, z=z, kij=k)
             for t, p, z, k in (
                (250, 1, .5, 0), (250, 5, .5, 0), (250, 20, .5, 0),
                (250, 50, .5, 0), (250, 100, .5, 0),
                (300, 1, .5, 0), (300, 20, .5, 0), (300, 80, .5, 0),
                (450, 1, .5, 0), (450, 200, .5, 0),
                (250, 20, .1, 0), (250, 20, .9, 0),
                (350, 50, .5, 0), (250, 20, .5, .03))]
    print('Finding reference tie-line for composition-boundary tests...', flush=True)
    anchor = BinaryPRReference(properties, 250, 2e6).flash(.5)
    skipped = []
    if anchor['status'] == 'two_phase':
        x, y = anchor['x_methane'], anchor['y_methane']
        width = y-x
        for label, z in (('near_bubble_inside', x+1e-4*width),
                         ('near_dew_inside', y-1e-4*width),
                         ('bubble_outside', x-1e-4*width),
                         ('dew_outside', y+1e-4*width)):
            if 0 < z < 1:
                cases.append(dict(id=label, T=250, bar=20, z=z, kij=0))
            else:
                skipped.append(label+': composition outside [0,1]')
    else:
        skipped.append('All boundary cases: independent anchor tie-line unresolved.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = Path(args.output)/stamp
    folder.mkdir(parents=True, exist_ok=False)
    report = dict(kind='numerical_verification_not_experimental_validation',
        created_utc=stamp, python=sys.version, platform=platform.platform(),
        numpy=numpy.__version__, scipy=scipy.__version__, git_head=git_value('rev-parse', 'HEAD'),
        git_status=git_value('status', '--short'), database=str(database_path.resolve()),
        database_sha256=hashlib.sha256(database_path.read_bytes()).hexdigest(),
        flash_source=str(Path(flash_module.__file__).resolve()),
        loaded_source_hashes={name: dict(path=str(Path(module.__file__).resolve()),
            sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
            for name, module in sorted(sys.modules.items())
            if (name.startswith('petroflash.') or name in ('pr_binary_reference', __name__))
            and getattr(module, '__file__', None) and Path(module.__file__).is_file()},
        constants=dict(R=8.31446261815324, omega_a=.45724, omega_b=.0778,
                       alpha='PR1976 quadratic m; no volume translation'),
        properties=properties, anchor=anchor, skipped_cases=skipped, cases=[])
    for number, case in enumerate(cases, 1):
        print(f'[{number}/{len(cases)}] {case["id"]}', end=' ... ', flush=True)
        mix = Mixture.from_mole_percentages(db, names, [100*case['z'], 100*(1-case['z'])])
        tp = TPConditions(case['T'], case['bar']*1e5)
        kk = ((0, case['kij']), (case['kij'], 0))
        start = time.perf_counter()
        try:
            engine = asdict(flash_tp(mix, tp, kij=kk))
        except Exception as error:
            engine = dict(status='error', error=f'{type(error).__name__}: {error}')
        seconds = time.perf_counter()-start
        mixture_fractions = tuple(mix.mole_fractions)
        try:
            ref_model = BinaryPRReference(properties, case['T'], case['bar']*1e5, case['kij'])
            grid = ref_model.tpd_grid(case['z'])
            reference = ref_model.flash(case['z'])
            verdict, differences, note = compare(engine, reference, grid)
        except Exception as error:
            grid, reference = {}, dict(status='error', error=f'{type(error).__name__}: {error}')
            verdict, differences, note = 'UNRESOLVED', {}, 'Independent reference failed.'
        report['cases'].append(dict(input=case, actual_feed_mole_fractions=mixture_fractions, petroflash=engine, reference=reference,
            independent_tpd_grid=grid, verdict=verdict, differences=differences,
            petroflash_seconds=seconds, note=note))
        print(f'{engine["status"]} | {verdict}', flush=True)
        # Checkpoint after every case; failures are retained, never omitted.
        (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    report['counts'] = dict(Counter(c['verdict'] for c in report['cases']))
    (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# PetroFlash binary numerical verification', '',
        'Same database properties and PR1976 settings; this is not experimental validation.', '',
        'PASS: matching two-phase results. LIMITED: no grid contradiction, not proof of stability.',
        'FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.', '',
        '| Case | Engine | Verdict | beta | max comparison error | seconds |',
        '|---|---|---|---:|---:|---:|']
    for item in report['cases']:
        errors = item['differences']
        lines.append(f'| {item["input"]["id"]} | {item["petroflash"]["status"]} | '
            f'{item["verdict"]} | {item["petroflash"].get("beta")} | '
            f'{max(errors.values()) if errors else "n/a"} | {item["petroflash_seconds"]:.6f} |')
    lines += ['', 'Counts: '+str(report['counts']), '', 'Skipped: '+str(skipped), '',
        'Boundary cases vary feed composition at fixed T/P along a reference binary tie-line.',
        'The campaign does not establish critical-region or multicomponent reliability.',
        'Times are single-run measurements, not a rigorous speed benchmark.']
    (folder/'summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Counts:', report['counts'])
    print('Report:', (folder/'report.json').resolve())
    print('Summary:', (folder/'summary.md').resolve())
    return 1 if report['counts'].get('FAIL') else (2 if skipped or report['counts'].get('UNRESOLVED') else 0)


if __name__ == '__main__':
    raise SystemExit(main())
