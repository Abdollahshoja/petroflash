"""Run a boundary and critical-vicinity PR numerical stress campaign against the SAME database.

Run from repo root: python tools/stress_tp_flash.py
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
        from .pr_multicomponent_reference import MulticomponentPRReference
    else:
        from pr_multicomponent_reference import MulticomponentPRReference
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
    names=['methane','n-butane']
    components=db.select(names)
    properties=[dict(name=c.name,cas=c.cas_number,Tc_K=c.critical_temperature.value,
        Pc_Pa=c.critical_pressure.value,omega=c.acentric_factor.value) for c in components]
    kk=[[0.,0.],[0.,0.]]
    cases=[]
    for t,pressures in ((300,(60,80,100,120,140,160)),
                       (350,(40,60,80,100,120,140)),
                       (400,(20,40,60,80,100,120))):
        for p in pressures:
            cases.append(dict(id=f'pressure_scan_T{t}_P{p}',names=names,z=[.5,.5],
                              T=t,bar=p,kij=kk,group='pressure_scan'))
    print('Calculating independent binary anchor for boundary stress...',flush=True)
    anchor=MulticomponentPRReference(properties,250,2e6,kk).flash([.5,.5])
    skipped=[]
    if anchor['status']=='two_phase':
        x,y=anchor['liquid_composition'][0],anchor['vapor_composition'][0]
        for epsilon in (1e-2,1e-4,1e-6,1e-8):
            for label,z in (('bubble_inside',x+epsilon*(y-x)),
                            ('dew_inside',y-epsilon*(y-x)),
                            ('bubble_outside',x-epsilon*(y-x)),
                            ('dew_outside',y+epsilon*(y-x))):
                if 0<z<1:
                    cases.append(dict(id=f'{label}_eps{epsilon:g}',names=names,z=[z,1-z],
                        T=250,bar=20,kij=kk,group='composition_boundary',epsilon=epsilon))
                else:
                    skipped.append(f'{label}_eps{epsilon:g}: invalid composition')
    else:
        skipped.append('Composition boundary cases: independent anchor unavailable.')
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
            if (name.startswith('petroflash.') or name in ('pr_multicomponent_reference', __name__))
            and getattr(module, '__file__', None) and Path(module.__file__).is_file()},
        constants=dict(R=8.31446261815324, omega_a=.45724, omega_b=.0778,
                       alpha='PR1976 quadratic m; no volume translation'),
        anchor=anchor, skipped_cases=skipped, cases=[])
    for number, case in enumerate(cases, 1):
        print(f'[{number}/{len(cases)}] {case["id"]}', end=' ... ', flush=True)
        names=case['names']
        components=db.select(names)
        properties=[dict(name=c.name,cas=c.cas_number,Tc_K=c.critical_temperature.value,
            Pc_Pa=c.critical_pressure.value,omega=c.acentric_factor.value) for c in components]
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
        separation=None
        if engine['status']=='two_phase':
            separation=dict(composition_gap=max(abs(x-y) for x,y in zip(engine['liquid_composition'],engine['vapor_composition'])),
                z_gap=abs(engine['liquid_z']-engine['vapor_z']))
        report['cases'].append(dict(phase_separation=separation,input=case, properties=properties, actual_feed_mole_fractions=mixture_fractions, petroflash=engine, reference=reference,
            independent_tpd_grid=grid, verdict=verdict, differences=differences,
            petroflash_seconds=seconds, note=note))
        print(f'{engine["status"]} | {verdict}', flush=True)
        # Checkpoint after every case; failures are retained, never omitted.
        (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    # Independent root diagnostics near nominal PURE methane critical data.
    # This is a cubic-root test, not a located critical point of the mixture.
    from petroflash.pr_pure import component_pr_parameters
    from petroflash.pr_roots import solve_pr_roots
    methane=db.get('methane')
    root_cases=[]
    for tr in (.999,1.,1.001):
        for pr in (.999,1.,1.001):
            tp=TPConditions(tr*methane.critical_temperature.value,pr*methane.critical_pressure.value)
            pure=component_pr_parameters(methane,tp)
            A,B=pure.A,pure.B
            rr=numpy.roots([1,B-1,A-2*B-3*B*B,-A*B+B*B+B**3])
            expected=sorted(float(r.real) for r in rr if abs(r.imag)<1e-9 and r.real>B)
            item=dict(temperature_ratio=tr,pressure_ratio=pr,A=A,B=B,independent_roots=expected)
            try:
                actual=solve_pr_roots(A=A,B=B)
                item['engine_roots']=list(actual.admissible_roots)
                error=max((abs(a-b) for a,b in zip(actual.admissible_roots,expected)),default=0.)
                item['maximum_difference']=error
                item['verdict']='PASS' if len(expected)==len(actual.admissible_roots) and error<=1e-7 else 'FAIL'
            except ArithmeticError as error:
                item['verdict']='UNRESOLVED';item['reason']=str(error)
            root_cases.append(item)
    report['pure_methane_root_checks']=root_cases
    report['root_counts']=dict(Counter(c['verdict'] for c in root_cases))
    report['counts'] = dict(Counter(c['verdict'] for c in report['cases']))
    (folder/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# PetroFlash boundary and critical-vicinity numerical stress tests', '',
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
        'Binary pressure sweeps and composition-boundary distances down to 1e-8 of the tie-line width.',
        'Pure methane root tests are near nominal critical data; no mixture critical point is located.',
        'Root diagnostic counts: '+str(report['root_counts']),
        'UNRESOLVED entries are retained; do not relax tolerances merely to obtain PASS.',
        'Finite tests do not certify global stability, critical-region reliability or experimental accuracy.',
        'Times are single-run measurements, not a rigorous speed benchmark.']
    (folder/'summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Counts:', report['counts'])
    print('Report:', (folder/'report.json').resolve())
    print('Summary:', (folder/'summary.md').resolve())
    print('Pure methane root checks:',report['root_counts'])
    return 1 if report['counts'].get('FAIL') or report['root_counts'].get('FAIL') else (2 if skipped or report['counts'].get('UNRESOLVED') or report['root_counts'].get('UNRESOLVED') else 0)


if __name__ == '__main__':
    raise SystemExit(main())
