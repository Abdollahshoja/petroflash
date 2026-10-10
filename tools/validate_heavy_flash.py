"""Verify C7-C20 hydrocarbon flashes against an independently implemented PR solver.

Run from repo root: python tools/validate_heavy_flash.py
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
        from .heavy_pr_reference import MulticomponentPRReference
    else:
        from heavy_pr_reference import MulticomponentPRReference
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
    if engine['status']=='two_phase':
        if reference['status']!='two_phase':
            return 'UNRESOLVED', {}, 'Independent split unavailable.'
        errors={k: abs(engine[k]-reference[k]) for k in ('beta','liquid_z','vapor_z')}
        for k in ('liquid_composition','vapor_composition'):
            errors[k]=max(abs(a-b) for a,b in zip(engine[k],reference[k]))
        ok=(max(errors.values())<=2e-6 and engine['fugacity_residual']<=1e-8
            and engine['material_residual']<=1e-10 and engine['normalization_residual']<=1e-10
            and engine['gibbs_change_rt']<0)
        return ('PASS' if ok else 'FAIL'), errors, 'Independent simultaneous-equation cross-check.'
    if engine['status']=='single_phase_candidate':
        if reference['status']=='two_phase' or grid['minimum_tpd'] < -1e-7:
            return 'FAIL', {}, 'Independent calculation contradicts no-split candidate.'
        return 'LIMITED', {}, 'Finite sampling found no contradiction; not a stability certificate.'
    return 'UNRESOLVED', {}, 'No accepted engine solution.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='data/components.json')
    parser.add_argument('--output', default='validation-results')
    args = parser.parse_args()
    database_path = Path(args.database)
    db = ComponentDatabase.from_file(database_path)
    required = ('n-heptane', 'n-decane', 'n-tridecane', 'n-hexadecane', 'n-eicosane')
    missing = [name for name in required if name not in db.names()]
    if missing:
        parser.exit(1, 'Apply the dataset 0.5.0 package first. Missing: '+', '.join(missing)+'\n')
    cases=[]
    for label,names,z in (
        ('light_C7_C10', ['methane','n-heptane','n-decane'], [.60,.25,.15]),
        ('light_C13_C20', ['methane','n-tridecane','n-eicosane'], [.60,.25,.15]),
        ('broad_C1_C20', ['methane','ethane','propane','n-heptane','n-decane','n-tridecane','n-hexadecane','n-eicosane'], [.40,.15,.10,.10,.08,.07,.05,.05]),
        ('trace_C20', ['methane','n-heptane','n-eicosane'], [.699,.300,.001])):
        for t,p in ((350,10),(400,30),(450,80)):
            n=len(names)
            cases.append(dict(id=f'{label}_T{t}_P{p}',names=names,z=z,T=t,bar=p,
                              kij=[[0.0]*n for _ in range(n)]))
    case=dict(cases[6]);case['id']='broad_C1_C20_synthetic_kij'
    case['kij']=[[0 if i==j else .02 for j in range(8)] for i in range(8)]
    cases.append(case)
    case=dict(cases[6]);case['id']='broad_C1_C20_reversed_order'
    case['names']=list(reversed(case['names']));case['z']=list(reversed(case['z']))
    cases.append(case)
    skipped=[]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = Path(args.output)/'heavy-c7-c20'/stamp
    folder.mkdir(parents=True, exist_ok=False)
    report = dict(kind='numerical_verification_not_experimental_validation',
        created_utc=stamp, python=sys.version, platform=platform.platform(),
        numpy=numpy.__version__, scipy=scipy.__version__, git_head=git_value('rev-parse', 'HEAD'),
        git_status=git_value('status', '--short'), database=str(database_path.resolve()),
        database_sha256=hashlib.sha256(database_path.read_bytes()).hexdigest(),
        dataset_version=db.dataset_version,
        scope='PR1976 numerical verification; no experimental or solid-phase validation',
        flash_source=str(Path(flash_module.__file__).resolve()),
        loaded_source_hashes={name: dict(path=str(Path(module.__file__).resolve()),
            sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
            for name, module in sorted(sys.modules.items())
            if (name.startswith('petroflash.') or name in ('heavy_pr_reference', __name__))
            and getattr(module, '__file__', None) and Path(module.__file__).is_file()},
        constants=dict(R=8.31446261815324, omega_a=.45724, omega_b=.0778,
                       alpha='PR1976 quadratic m; no volume translation'),
        skipped_cases=skipped, cases=[])
    for number, case in enumerate(cases, 1):
        print(f'[{number}/{len(cases)}] {case["id"]}', end=' ... ', flush=True)
        names=case['names']
        components=db.select(names)
        properties=[dict(name=c.name,cas=c.cas_number,Tc_K=c.critical_temperature.value,
            Pc_Pa=c.critical_pressure.value,omega=c.acentric_factor.value,
            records={field:asdict(getattr(c,field)) for field in
                ('critical_temperature','critical_pressure','acentric_factor','molar_mass')}) for c in components]
        mix = Mixture.from_mole_percentages(db,names,[100*v for v in case['z']])
        tp = TPConditions(case['T'], case['bar']*1e5)
        kk = case['kij']
        start = time.perf_counter()
        try:
            engine = asdict(flash_tp(mix, tp, kij=kk))
        except Exception as error:
            engine = dict(status='error', error=f'{type(error).__name__}: {error}')
        seconds = time.perf_counter()-start
        mixture_fractions = tuple(mix.mole_fractions)
        try:
            ref_model = MulticomponentPRReference(properties, case['T'], case['bar']*1e5, case['kij'])
            grid = ref_model.tpd_sample(mixture_fractions)
            reference = ref_model.flash(mixture_fractions)
            verdict, differences, note = compare(engine, reference, grid)
        except Exception as error:
            grid, reference = {}, dict(status='error', error=f'{type(error).__name__}: {error}')
            verdict, differences, note = 'UNRESOLVED', {}, 'Independent reference failed.'
        report['cases'].append(dict(input=case, properties=properties, actual_feed_mole_fractions=mixture_fractions, petroflash=engine, reference=reference,
            independent_tpd_grid=grid, verdict=verdict, differences=differences,
            petroflash_seconds=seconds, note=note))
        print(f'{engine["status"]} | {verdict}', flush=True)
        # Checkpoint after every case; failures are retained, never omitted.
        (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    original=next(c for c in report['cases'] if c['input']['id']=='broad_C1_C20_T350_P10')
    reversed_case=next(c for c in report['cases'] if c['input']['id']=='broad_C1_C20_reversed_order')
    a,b=original['petroflash'],reversed_case['petroflash']
    if a['status']==b['status']=='two_phase':
        error=max(abs(a['beta']-b['beta']),
            *(abs(x-y) for x,y in zip(a['liquid_composition'],reversed(b['liquid_composition']))),
            *(abs(x-y) for x,y in zip(a['vapor_composition'],reversed(b['vapor_composition']))))
        report['component_order_check']=dict(maximum_error=error,passed=error<=2e-6)
        if error>2e-6:
            reversed_case['verdict']='FAIL'
            reversed_case['note']='Component permutation changed the physical result.'
    else:
        report['component_order_check']=dict(passed=False,reason='Two-phase permutation comparison unavailable.')
        reversed_case['verdict']='UNRESOLVED'
    report['counts'] = dict(Counter(c['verdict'] for c in report['cases']))
    (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# PetroFlash heavy-hydrocarbon numerical verification', '',
        'Same database properties and PR1976 settings; this is not experimental validation.', '',
        'PASS: matching two-phase results. LIMITED: no sampling contradiction, not proof of stability.',
        'FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.', '',
        '| Case | Engine | Verdict | beta | max comparison error | seconds |',
        '|---|---|---|---:|---:|---:|']
    for item in report['cases']:
        errors = item['differences']
        lines.append(f'| {item["input"]["id"]} | {item["petroflash"]["status"]} | '
            f'{item["verdict"]} | {item["petroflash"].get("beta")} | '
            f'{max(errors.values()) if errors else "n/a"} | {item["petroflash_seconds"]:.6f} |')
    lines += ['', 'Counts: '+str(report['counts']), '', 'Skipped: '+str(skipped), '',
        'Positive feed fractions; three and eight components, trace C20, synthetic kij and order reversal. Fixed-seed TPD sampling.',
        'Finite tests do not certify global stability, critical-region reliability or experimental accuracy.',
        'Times are single-run measurements, not a rigorous speed benchmark.']
    (folder/'summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Counts:', report['counts'])
    print('Report:', (folder/'report.json').resolve())
    print('Summary:', (folder/'summary.md').resolve())
    return 1 if report['counts'].get('FAIL') else (2 if skipped or report['counts'].get('UNRESOLVED') else 0)


if __name__ == '__main__':
    raise SystemExit(main())
