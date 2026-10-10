"""CMU documented feed; compare PetroFlash against third-party Thermo.
The source provides inputs, not a published numerical answer for this example.
Run from repository root: python tools/benchmark_web_cmu.py
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as S
import math
import thermo
from thermo import ChemicalConstantsPackage, PropertyCorrelationsPackage, HeatCapacityGas
from thermo import CEOSGas, CEOSLiquid, PRMIX, FlashVL
from petroflash.flash import flash_tp
from petroflash.conditions import TPConditions
from petroflash.pr_pure import component_pr_parameters

SOURCE='https://kitchingroup.cheme.cmu.edu/differentiable-flowsheets/docs/unit-operations-chemical.html'
R=8.31446261815324

class RoundedPRMIX(PRMIX):
    """Explicit coefficient alignment, only in this validation tool."""
    c1=0.45724
    c2=0.07780
    c1R2=c1*R*R
    c2R=c2*R
    c1R2_c2R=c1*R/c2


def main():
    names=['methane','ethane','propane']
    tcs=[190.6,305.4,369.8]; pcs=[4.6e6,4.9e6,4.2e6]; omegas=[.011,.099,.152]
    feed=[.4,.3,.3]; T=250.; P=2e6; kk=[[0.]*3 for _ in names]
    cs=tuple(S(name=n,formula=f,critical_temperature=S(value=t),
        critical_pressure=S(value=p),acentric_factor=S(value=o))
        for n,f,t,p,o in zip(names,['CH4','C2H6','C3H8'],tcs,pcs,omegas))
    tp=TPConditions(T,P)
    engine=asdict(flash_tp(S(components=cs,mole_fractions=tuple(feed)),tp,kij=kk))
    constants=ChemicalConstantsPackage(Tcs=tcs,Pcs=pcs,omegas=omegas,MWs=[16.04,30.07,44.10])
    # Constant ideal-gas heat capacities are scaffolding for FlashVL.
    # They do not enter fugacity-based isothermal TP phase equilibrium.
    cps=[HeatCapacityGas(poly_fit=(50.,1000.,[30.])) for _ in names]
    correlations=PropertyCorrelationsPackage(constants=constants,HeatCapacityGases=cps,skip_missing=True)
    report=dict(source=SOURCE,access_date='2026-10-10',source_has_numerical_answer=False,
        description='Documented EOSFlash feed; independently computed answers, not quoted source outputs.',
        assumptions=['All kij explicitly zero','No volume translation','PR1976 alpha',
                     'Same printed critical properties in both solvers'],
        inputs=dict(names=names,T_K=T,P_Pa=P,feed=feed,Tcs=tcs,Pcs=pcs,omegas=omegas,kij=kk),
        thermo_version=thermo.__version__,python=sys.version,engine=engine,comparisons=[])
    for label,cls in [('thermo_default',PRMIX),('thermo_aligned_coefficients',RoundedPRMIX)]:
        kwargs=dict(Tcs=tcs,Pcs=pcs,omegas=omegas,kijs=kk)
        gas=CEOSGas(cls,kwargs,HeatCapacityGases=cps)
        liquid=CEOSLiquid(cls,kwargs,HeatCapacityGases=cps)
        flasher=FlashVL(constants,correlations,gas=gas,liquid=liquid)
        flasher.PT_SS_TOL=1e-18
        res=flasher.flash(T=T,P=P,zs=feed)
        item=dict(label=label,coefficients=[cls.c1,cls.c2],phase_count=res.phase_count,beta=res.VF)
        if res.gas is not None and res.liquid_count==1 and engine['status']=='two_phase':
            x=res.liquid0.zs; y=res.gas.zs
            item.update(liquid_composition=x,vapor_composition=y,liquid_z=res.liquid0.Z(),vapor_z=res.gas.Z())
            item['differences']={k:abs(engine[k]-item[k]) for k in ['beta','liquid_z','vapor_z']}
            for k in ['liquid_composition','vapor_composition']:
                item['differences'][k]=max(abs(a-b) for a,b in zip(engine[k],item[k]))
            item['fugacity_residual']=max(abs(math.log(a/b)) for a,b in zip(res.liquid0.fugacities(),res.gas.fugacities()))
            item['material_residual']=max(abs(z-(1-res.VF)*a-res.VF*b) for z,a,b in zip(feed,x,y))
            if cls is RoundedPRMIX:
                eos=cls(Tcs=tcs,Pcs=pcs,omegas=omegas,kijs=kk,T=T,P=P,zs=feed)
                pure=[component_pr_parameters(c,tp) for c in cs]
                item['pure_parameter_relative_error']=max(abs(a.a_t/b-1) for a,b in zip(pure,eos.a_alphas))
                item['b_relative_error']=max(abs(a.b/b-1) for a,b in zip(pure,eos.bs))
                passed=(max(item['differences'].values())<=2e-6 and
                    item['fugacity_residual']<=1e-8 and item['material_residual']<=1e-10 and
                    engine['fugacity_residual']<=1e-8 and engine['material_residual']<=1e-10 and
                    engine['normalization_residual']<=1e-10 and
                    item['pure_parameter_relative_error']<1e-12 and item['b_relative_error']<1e-12)
                item['verdict']='PASS' if passed else 'FAIL'
            else:
                item['verdict']='MODEL_COEFFICIENT_SENSITIVITY'
        else:
            item['verdict']='UNRESOLVED'
        report['comparisons'].append(item)
        print(label, item['verdict'], 'beta:',item['beta'])
    report['loaded_source_hashes']={n:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
        for n,m in sys.modules.copy().items() if n.startswith('petroflash.') and getattr(m,'__file__',None)}
    report['tool_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out=Path('validation-results/web-cmu')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out.mkdir(parents=True)
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print('Report:',(out/'report.json').resolve())
    return 0 if report['comparisons'][-1]['verdict']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
