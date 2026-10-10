"""Published calculated benchmark; uses printed input properties, not central DB.
Run: python tools/benchmark_whitson_problem18.py
No claim of experimental validation or exact reproduction of hidden inputs.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from types import SimpleNamespace as S
try:
    import numpy
    import scipy
    from pr_multicomponent_reference import MulticomponentPRReference
except ImportError as error:
    raise SystemExit(f'{error}\nInstall reference dependencies: "{sys.executable}" -m pip install numpy scipy')
from petroflash.conditions import TPConditions
from petroflash.flash import flash_tp
from petroflash.pr_pure import component_pr_parameters

PSI_PA=6894.757293168


def git_value(*args):
    try:
        return subprocess.check_output(['git',*args],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        return 'unavailable'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-file',default='data/benchmarks/whitson_problem18.json')
    parser.add_argument('--output',default='validation-results/whitson-problem18')
    args=parser.parse_args()
    source=Path(args.case_file)
    data=json.loads(source.read_text(encoding='utf-8-sig'))
    cs=tuple(S(name=n,formula=f,critical_temperature=S(value=t*5/9),
        critical_pressure=S(value=p*PSI_PA),acentric_factor=S(value=o))
        for n,f,t,p,o in zip(data['names'],data['formulas'],data['critical_temperature_rankine'],
                           data['critical_pressure_psia'],data['omega']))
    props=[dict(name=c.name,Tc_K=c.critical_temperature.value,Pc_Pa=c.critical_pressure.value,
                omega=c.acentric_factor.value) for c in cs]
    mix=S(components=cs,mole_fractions=tuple(data['feed']))
    kk=data['kij']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=Path(args.output)/stamp
    folder.mkdir(parents=True,exist_ok=False)
    report=dict(kind=data['kind'],source=data['source'],case_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        python=sys.version,platform=platform.platform(),numpy=numpy.__version__,scipy=scipy.__version__,
        git_head=git_value('rev-parse','HEAD'),git_status=git_value('status','--short'),inputs=data,
        properties_si=props,psi_to_pa=PSI_PA,notes=data['notes'],cases=[])
    for published in data['cases']:
        pressure=published['pressure_psia']
        print(f'Published example: {pressure:g} psia, {data["temperature_f"]:g} F',flush=True)
        item=dict(published=published)
        temperature=(data['temperature_f']+459.67)*5/9
        tp=TPConditions(temperature,pressure*PSI_PA)
        try:
            engine=asdict(flash_tp(mix,tp,kij=kk,alpha_model=data['alpha_model']))
            reference=MulticomponentPRReference(props,temperature,tp.pressure_pa,kk,
                alpha_model=data['alpha_model']).flash(mix.mole_fractions)
            item.update(temperature_k=temperature,engine=engine,reference=reference,
                pure_parameters=[asdict(component_pr_parameters(c,tp,alpha_model=data['alpha_model'])) for c in cs])
            if engine['status']==reference['status']=='two_phase':
                diffs={k:abs(engine[k]-reference[k]) for k in ('beta','liquid_z','vapor_z')}
                for k in ('liquid_composition','vapor_composition'):
                    diffs[k]=max(abs(a-b) for a,b in zip(engine[k],reference[k]))
                checks=(max(diffs.values())<=2e-6 and engine['fugacity_residual']<=1e-8
                    and engine['material_residual']<=1e-10 and engine['normalization_residual']<=1e-10
                    and engine['gibbs_change_rt'] < -engine['gibbs_resolution_rt'])
                item['numerical_verdict']='PASS' if checks else 'FAIL'
                item['independent_differences']=diffs
                bookdiff=dict(beta=abs(engine['beta']-published['beta']))
                for k in ('liquid_composition','vapor_composition'):
                    bookdiff[k]=max(abs(a-b) for a,b in zip(engine[k],published[k]))
                # Compare at PRINTED output rounding, rather than enlarging the
                # acceptance limit until a desired literature result passes.
                composition_half_unit=.5*10**(-published['composition_printed_decimals'])
                matched=bookdiff['beta']<=.5e-6 and all(bookdiff[k]<=composition_half_unit
                    for k in ('liquid_composition','vapor_composition'))
                item['printed_output_verdict']='MATCHES_PRINTED_PRECISION' if matched else 'BOOK_DIFFERENCE'
                item['printed_output_differences']=bookdiff
                item['printed_precision_limits']=dict(beta=.5e-6,composition=composition_half_unit)
            else:
                item['numerical_verdict']='UNRESOLVED'
                item['printed_output_verdict']='UNRESOLVED'
            sensitivities=[]
            for label,temp,model in (
                ('book_step_temperature_F_plus_460',(data['temperature_f']+460)*5/9,data['alpha_model']),
                ('original_PR1976_exact_temperature',temperature,'PR1976')):
                result=asdict(flash_tp(mix,TPConditions(temp,tp.pressure_pa),kij=kk,alpha_model=model))
                sensitivities.append(dict(label=label,temperature_k=temp,alpha_model=model,result=result))
            item['sensitivities']=sensitivities
        except (ValueError,ArithmeticError,RuntimeError) as error:
            item.update(numerical_verdict='UNRESOLVED',printed_output_verdict='UNRESOLVED',error=str(error))
        report['cases'].append(item)
        (folder/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
        print(item['numerical_verdict'],'|',item['printed_output_verdict'],flush=True)
    report['loaded_source_hashes']={name:dict(path=str(Path(module.__file__).resolve()),
        sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
        for name,module in sorted(sys.modules.items()) if (name.startswith('petroflash.') or
        name in ('pr_multicomponent_reference',__name__)) and getattr(module,'__file__',None)
        and Path(module.__file__).is_file()}
    (folder/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    lines=['# Whitson Appendix B Problem 18','',
        'Published calculated results, not experimental data. Exact F conversion for main cases.',
        'Printed input properties; explicit Eq.4.22 for omega > 0.4; no volume translation.',
        'BOOK_DIFFERENCE is retained at the printed output precision; no fitted inputs.','',
        '| psia | numerical | published comparison | book beta | engine beta | absolute beta difference |',
        '|---:|---|---|---:|---:|---:|']
    for c in report['cases']:
        lines.append(f'| {c["published"]["pressure_psia"]:g} | {c["numerical_verdict"]} | '
            f'{c["printed_output_verdict"]} | {c["published"]["beta"]} | '
            f'{c.get("engine",{}).get("beta")} | {c.get("printed_output_differences",{}).get("beta")} |')
    lines+=['','Possible sources of book differences include rounded or undocumented input settings;',
        'the current evidence does not identify a unique cause. See temperature/alpha sensitivities in JSON.',
        'Matching an independent implementation of the same model does not establish experimental accuracy.']
    (folder/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Report:',(folder/'report.json').resolve())
    print('Summary:',(folder/'summary.md').resolve())
    if any(c['numerical_verdict']=='FAIL' for c in report['cases']):return 1
    if any(c['numerical_verdict']!='PASS' or c['printed_output_verdict']!='MATCHES_PRINTED_PRECISION'
           for c in report['cases']):return 2
    return 0

if __name__=='__main__':
    raise SystemExit(main())
