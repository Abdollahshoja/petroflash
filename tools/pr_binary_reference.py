"""Independent PR1976 binary numerical reference, with no PetroFlash imports.

NumPy polynomial roots and SciPy bounded simultaneous fugacity equations.
Designed for light-first methane/n-butane VLE. A failed solve does not imply
single phase. Composition grids cannot certify global stability.
"""

import numpy as np
from scipy.optimize import least_squares

R = 8.31446261815324


class BinaryPRReference:
    def __init__(self, properties, temperature_k, pressure_pa, kij=0.0):
        self.T, self.P = float(temperature_k), float(pressure_pa)
        tc = np.array([c['Tc_K'] for c in properties])
        pc = np.array([c['Pc_Pa'] for c in properties])
        omega = np.array([c['omega'] for c in properties])
        if len(tc) != 2:
            raise ValueError('This independent reference is binary only.')
        m = .37464+1.54226*omega-.26992*omega**2
        a = .45724*(R*tc)**2/pc*(1+m*(1-np.sqrt(self.T/tc)))**2
        self.b = .0778*R*tc/pc
        self.aij = np.sqrt(a[:, None]*a[None, :])*(1-np.array([[0, kij], [kij, 0]]))

    def states(self, methane_fraction):
        x = np.array([methane_fraction, 1-methane_fraction], dtype=float)
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

    def best(self, fraction):
        return min(self.states(fraction), key=lambda q: q['g'])

    def tpd_grid(self, feed_fraction, points=121):
        z = np.array([feed_fraction, 1-feed_fraction])
        if np.any(z <= 0):
            raise ValueError('Reference grid requires both feed species present.')
        ref = self.best(feed_fraction)
        d = np.log(z)+ref['lnphi']
        grid = np.unique(np.r_[np.linspace(0, 1, points), feed_fraction])
        minimum, witness = float('inf'), None
        for fraction in grid:
            w = np.array([fraction, 1-fraction])
            state = self.best(float(fraction))
            value = float(sum(w[i]*(np.log(w[i])+state['lnphi'][i]-d[i])
                              for i in range(2) if w[i] > 0))
            if value < minimum:
                minimum, witness = value, float(fraction)
        return dict(minimum_tpd=minimum, witness_methane=witness, samples=len(grid),
                    reference_z=ref['z'])

    def flash(self, feed_fraction):
        zf = float(feed_fraction)
        # Exclude the trivial x=y=z root and enforce a physical lever rule.
        margin = 1e-9
        lo = np.array([1e-12, zf+margin])
        hi = np.array([zf-margin, 1-1e-12])
        if np.any(lo >= hi):
            return dict(status='unresolved', reason='Feed too near a pure endpoint.')
        def residual(pair):
            x, y = pair
            l = self.states(x)[0]
            v = self.states(y)[-1]
            return np.log([x, 1-x])+l['lnphi']-np.log([y, 1-y])-v['lnphi']
        candidates = []
        errors = []
        for u, v in ((.2, .8), (.8, .2), (.05, .95), (.5, .5), (.95, .95)):
            initial = lo+(hi-lo)*[u, v]
            try:
                solution = least_squares(residual, initial, bounds=(lo, hi),
                    xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=400)
                x, y = map(float, solution.x)
                error = float(max(abs(residual(solution.x))))
                beta = (zf-x)/(y-x)
                l, vap = self.states(x)[0], self.states(y)[-1]
                dg = (1-beta)*l['g']+beta*vap['g']-self.best(zf)['g']
                if error > 1e-8 or y-x < 1e-6 or not 0 < beta < 1 or dg >= -1e-10:
                    continue
                if l['g']-self.best(x)['g'] > 1e-8 or vap['g']-self.best(y)['g'] > 1e-8:
                    continue
                candidates.append(dict(status='two_phase', beta=beta, x_methane=x,
                    y_methane=y, z_liquid=l['z'], z_vapor=vap['z'],
                    fugacity_residual=error, gibbs_change=dg))
            except (ValueError, ArithmeticError, np.linalg.LinAlgError) as error:
                errors.append(str(error))
        if not candidates:
            return dict(status='unresolved', reason='No accepted two-phase reference solve.',
                        errors=errors)
        result = min(candidates, key=lambda q: q['gibbs_change'])
        result['liquid_tpd_grid'] = self.tpd_grid(result['x_methane'])
        result['vapor_tpd_grid'] = self.tpd_grid(result['y_methane'])
        if min(result['liquid_tpd_grid']['minimum_tpd'],
               result['vapor_tpd_grid']['minimum_tpd']) < -1e-7:
            return dict(status='unresolved', reason='Independent phase TPD grid found instability.')
        return result
