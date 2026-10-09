"""Independent multicomponent PR1976 reference. No PetroFlash imports.
Simultaneous bounded least squares for phase compositions and vapor fraction.
Finite composition sampling is a diagnostic, not a global stability proof.
"""
import numpy as np
from math import fsum
from scipy.optimize import least_squares, brentq
from scipy.special import softmax, expit
R = 8.31446261815324

class MulticomponentPRReference:
    def __init__(self, properties, temperature_k, pressure_pa, kij):
        self.T, self.P = float(temperature_k), float(pressure_pa)
        self.n = len(properties)
        tc = np.array([c['Tc_K'] for c in properties])
        pc = np.array([c['Pc_Pa'] for c in properties])
        omega = np.array([c['omega'] for c in properties])
        m = .37464+1.54226*omega-.26992*omega**2
        a = .45724*(R*tc)**2/pc*(1+m*(1-np.sqrt(self.T/tc)))**2
        self.b = .0778*R*tc/pc
        self.aij = np.sqrt(a[:,None]*a[None,:])*(1-np.array(kij))
        self.logkw = np.log(pc/self.P)+5.373*(1+omega)*(1-tc/self.T)

    def states(self, composition):
        x = np.array(composition, dtype=float)
        if not np.all((x >= 0) & (x <= 1)):
            raise ValueError('Composition outside [0, 1].')
        am, bm = x@self.aij@x, x@self.b
        A, B = am*self.P/(R*self.T)**2, bm*self.P/(R*self.T)
        roots = np.roots([1, B-1, A-2*B-3*B**2, -A*B+B**2+B**3])
        real = sorted(float(q.real) for q in roots
                      if abs(q.imag) <= 1e-10*max(1, abs(q.real)) and q.real > B)
        if not real:
            raise ArithmeticError('Independent cubic has no admissible resolved real root.')
        output = []
        for z in real:
            lnphi = self.b/bm*(z-1)-np.log(z-B)-A/(2*np.sqrt(2)*B)*(
                2*(self.aij@x)/am-self.b/bm)*np.log(
                    (z+(1+np.sqrt(2))*B)/(z+(1-np.sqrt(2))*B))
            if not np.all(np.isfinite(lnphi)):
                raise ArithmeticError('Nonfinite independent ln(phi).')
            ideal = sum(v*np.log(v) for v in x if v > 0)
            output.append(dict(z=z, lnphi=lnphi, g=float(ideal+x@lnphi)))
        return output

    def best(self, composition):
        return min(self.states(composition), key=lambda q: q['g'])

    def tpd_sample(self, composition):
        z = np.asarray(composition, dtype=float)
        d = np.log(z)+self.best(z)['lnphi']
        # Fixed seed ensures reproducibility; include faces and pure endpoints.
        rng = np.random.default_rng(20261010)
        trials = [z, *np.eye(self.n), *rng.dirichlet(np.ones(self.n), 128),
                  *rng.dirichlet(np.full(self.n,.15), 128)]
        for i in range(self.n):
            trials.append(.1*z+.9*np.eye(self.n)[i])
        minimum, witness = float('inf'), None
        for w in trials:
            state = self.best(w)
            active = w > 0
            tpd = float(np.sum(w[active]*(np.log(w[active])+state['lnphi'][active]-d[active])))
            if tpd < minimum:
                minimum, witness = tpd, w.tolist()
        return dict(minimum_tpd=minimum, witness_composition=witness, samples=len(trials))

    def flash(self, composition):
        z = np.asarray(composition,dtype=float)
        if np.any(z <= 0):
            raise ValueError('Reference requires positive active feed fractions.')
        def unpack(u):
            return softmax(np.r_[u[:self.n-1],0]), softmax(np.r_[u[self.n-1:-1],0]), float(expit(u[-1]))
        def residual(u):
            x,y,beta = unpack(u)
            l,v = self.states(x)[0],self.states(y)[-1]
            fug = np.log(x)+l['lnphi']-np.log(y)-v['lnphi']
            balance = ((1-beta)*x+beta*y-z)[:-1]
            return np.r_[fug,10*balance]
        seeds=[]
        for scale in (1., .5, 1.5, 2.):
            lk=scale*self.logkw
            # Center only the initial K seed to obtain a lever-rule bracket.
            lower=-np.log(np.sum(z*np.exp(lk)))
            upper=np.log(np.sum(z*np.exp(-lk)))
            k=np.exp(lk+(lower+upper)/2)
            f=lambda b: float(np.sum(z*(k-1)/(1+b*(k-1))))
            if f(0)>0 and f(1)<0:
                beta=brentq(f,0,1,xtol=1e-14)
                x=z/(1+beta*(k-1));y=k*x
                seeds.append(np.r_[np.log(x[:-1]/x[-1]),np.log(y[:-1]/y[-1]),np.log(beta/(1-beta))])
        accepted=[]; attempts=[]
        for seed in seeds:
            try:
                sol=least_squares(residual,np.clip(seed,-39,39),bounds=(-40,40),
                    xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=500)
                x,y,beta=unpack(sol.x)
                l,v=self.states(x)[0],self.states(y)[-1]
                fug=float(max(abs(residual(sol.x)[:self.n])))
                mass=float(max(abs((1-beta)*x+beta*y-z)))
                feed_g=self.best(z)['g']
                dg=fsum([(1-beta)*l['g'],beta*v['g'],-feed_g])
                scale=max(1.,(1-beta)*float(np.sum(np.abs(x*(np.log(x)+l['lnphi']))))
                    +beta*float(np.sum(np.abs(y*(np.log(y)+v['lnphi']))))
                    +float(np.sum(np.abs(z*(np.log(z)+self.best(z)['lnphi'])))))
                normalization=max(abs(float(sum(x))-1),abs(float(sum(y))-1),abs(float(sum(z))-1))
                resolution=(64*np.finfo(float).eps+8*normalization)*scale
                attempts.append(dict(fugacity_residual=fug,material_residual=mass,nfev=sol.nfev, gibbs_change=dg, gibbs_resolution=resolution, beta=beta))
                if (fug>1e-8 or mass>1e-10 or max(abs(x-y))<1e-6 or
                    not 1e-9<beta<1-1e-9 or dg>=-resolution or abs(l['z']-v['z'])<1e-7):
                    continue
                if l['g']-self.best(x)['g']>1e-8 or v['g']-self.best(y)['g']>1e-8:
                    continue
                if l['z']>v['z']:
                    x,y,l,v,beta=y,x,v,l,1-beta
                accepted.append(dict(status='two_phase',beta=beta,liquid_composition=x.tolist(),
                    vapor_composition=y.tolist(),liquid_z=l['z'],vapor_z=v['z'],
                    fugacity_residual=fug,material_residual=mass,gibbs_change=dg,gibbs_resolution=resolution))
            except (ValueError,ArithmeticError,np.linalg.LinAlgError) as error:
                attempts.append(dict(error=str(error)))
        if not accepted:
            return dict(status='unresolved',attempts=attempts,reason='No accepted independent phase split; this does not establish single phase.')
        q=min(accepted,key=lambda q:q['gibbs_change'])
        q['liquid_tpd_sample']=self.tpd_sample(q['liquid_composition'])
        q['vapor_tpd_sample']=self.tpd_sample(q['vapor_composition'])
        if min(q['liquid_tpd_sample']['minimum_tpd'],q['vapor_tpd_sample']['minimum_tpd']) < -1e-7:
            return dict(status='unresolved',reason='Sampled phase instability.',candidate=q)
        q['attempts']=attempts
        return q
