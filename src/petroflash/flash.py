"""Baseline PR1976 TP vapor-liquid flash for simple hydrocarbons.

Uses local stability searches, bracketed RR and safeguarded log-K updates.
No global stability certificate, multiphase model or critical-region guarantee.
"""

from dataclasses import dataclass
from math import exp, fsum, isfinite, log
import re
from sys import float_info
from types import SimpleNamespace

from .pr_phase import evaluate_pr_phase
from .pr_pure import _number, component_pr_parameters
from .rachford_rice import solve_rachford_rice
from .stability import StabilityResult, search_pr_stability
from .tpd import _composition


@dataclass(frozen=True, slots=True)
class FlashResult:
    status: str
    message: str
    feed_stability: StabilityResult
    beta: float | None = None
    liquid_composition: tuple[float, ...] | None = None
    vapor_composition: tuple[float, ...] | None = None
    liquid_z: float | None = None
    vapor_z: float | None = None
    fugacity_residual: float | None = None
    material_residual: float | None = None
    normalization_residual: float | None = None
    gibbs_change_rt: float | None = None
    iterations: int = 0
    phase_stability: tuple[StabilityResult, ...] = ()
    attempts: tuple[str, ...] = ()
    gibbs_resolution_rt: float | None = None


def _gibbs(x, ln_phi):
    return fsum(v*(log(v)+p) for v, p in zip(x, ln_phi) if v > 0)


def _gibbs_assessment(z, x, y, beta, ref_phi, liquid_phi, vapor_phi):
    """Return Gibbs change and an engineering estimate of numerical resolution.

    This is NOT an interval-arithmetic error bound or global stability proof.
    A 64-epsilon scale allowance covers cancellation in extensive Gibbs terms;
    a composition-normalization allowance prevents accepting ill-resolved
    small differences. Root, fugacity and local stability checks remain separate.
    """
    terms = [-(zi*(log(zi)+p)) for zi,p in zip(z,ref_phi) if zi>0]
    terms += [(1-beta)*xi*(log(xi)+p) for xi,p in zip(x,liquid_phi) if xi>0]
    terms += [beta*yi*(log(yi)+p) for yi,p in zip(y,vapor_phi) if yi>0]
    delta = fsum(terms)
    scale = max(1.0, fsum(abs(v) for v in terms))
    normalization = max(abs(fsum(z)-1), abs(fsum(x)-1), abs(fsum(y)-1))
    resolution = (64*float_info.epsilon+8*normalization)*scale
    return delta, resolution


def _logsumexp(values):
    peak = max(values)
    return peak+log(fsum(exp(v-peak) for v in values))


def _center_seed(logk, z):
    """Scale initial K to bracket RR; never modify a converged K this way."""
    active = tuple(i for i, v in enumerate(z) if v > 0)
    low = -_logsumexp(tuple(log(z[i])+logk[i] for i in active))
    high = _logsumexp(tuple(log(z[i])-logk[i] for i in active))
    if high-low <= 1e-12:
        raise ValueError('Initial K is trivial or has insufficient spread.')
    shift = (low+high)/2
    return tuple(logk[i]+shift if z[i] > 0 else 0.0 for i in range(len(z)))


def flash_tp(mixture, conditions, *, kij, max_iterations=100,
             fugacity_tolerance=1e-8, stability_max_iterations=200):
    """Return two_phase, single_phase_candidate or inconclusive.

    A single-phase candidate has no assigned liquid/vapor label or beta.
    Two-phase output passes mass balance, fugacity, nontriviality, Gibbs
    decrease and local phase stability checks. Such checks are not global
    proofs. Smaller Z is labelled liquid under the simple-hydrocarbon VLE
    scope; water/nonhydrocarbon feeds are rejected by this initial interface.
    """
    for name, value in (('max_iterations', max_iterations),
                        ('stability_max_iterations', stability_max_iterations)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f'{name} must be an integer.')
        if value < 1:
            raise ValueError(f'{name} must be positive.')
    tolerance = _number(fugacity_tolerance, 'fugacity_tolerance', positive=True)
    z = _composition(mixture.mole_fractions, 'feed composition')
    if len(z) != len(mixture.components):
        raise ValueError('Composition must match components.')
    active = tuple(i for i, value in enumerate(z) if value > 0)
    for i in active:
        formula = getattr(mixture.components[i], 'formula', '')
        if re.fullmatch(r'C\d*H\d*', formula) is None:
            raise ValueError('This initial TP flash supports simple hydrocarbon feeds only.')
    kk = tuple(tuple(row) for row in kij)
    feed_search = search_pr_stability(mixture, conditions, kij=kk,
                                      max_iterations=stability_max_iterations)
    if feed_search.status == 'inconclusive':
        return FlashResult('inconclusive', 'Feed stability search was inconclusive.', feed_search)
    if feed_search.status == 'no_negative_tpd_found':
        return FlashResult('single_phase_candidate',
            'No negative TPD was found. Local-search candidate only; no vapor/liquid label assigned.',
            feed_search)
    pure = tuple(component_pr_parameters(c, conditions) for c in mixture.components)
    common = dict(a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure), kij=kk,
                  temperature_k=conditions.temperature_k, pressure_pa=conditions.pressure_pa)
    reference = evaluate_pr_phase(mole_fractions=z, **common).preferred_candidates[0]

    def evaluate(logk, branch):
        k = tuple(exp(v) for v in logk)
        if not all(isfinite(v) and v > 0 for v in k):
            raise ArithmeticError('K values exceed the numerical range.')
        beta = solve_rachford_rice(z, k, residual_tolerance=1e-14)
        if not 1e-10 < beta < 1-1e-10:
            raise ValueError('Phase fraction is at an endpoint; not an interior split.')
        x = tuple(zi/((1-beta)+beta*ki) for zi, ki in zip(z, k))
        y = tuple(ki*xi for ki, xi in zip(k, x))
        if max(abs(fsum(x)-1), abs(fsum(y)-1)) > 1e-10:
            raise ArithmeticError('RR phase compositions fail normalization; no renormalization applied.')
        if max(abs(x[i]-y[i]) for i in active) < 1e-7:
            raise ValueError('Trivial split: the two phase compositions coincide.')
        xl = evaluate_pr_phase(mole_fractions=x, **common)
        yv = evaluate_pr_phase(mole_fractions=y, **common)
        l, v = xl.candidates[branch[0]], yv.candidates[branch[1]]
        residuals = tuple(l.ln_phi[i]-v.ln_phi[i]-logk[i] if i in active else 0.0
                          for i in range(len(z)))
        norm = max(abs(residuals[i]) for i in active)
        return beta, x, y, l, v, residuals, norm, xl, yv

    attempts = []
    seeds = []
    try:
        wilson = tuple(log(c.critical_pressure.value)-log(conditions.pressure_pa)
            +5.373*(1+c.acentric_factor.value)*(1-c.critical_temperature.value/conditions.temperature_k)
            if z[i] > 0 else 0.0 for i, c in enumerate(mixture.components))
        seeds.append(('Wilson', _center_seed(wilson, z)))
    except (ValueError, ArithmeticError) as error:
        attempts.append(f'Wilson seed: {error}')
    for record in feed_search.starts:
        if record.minimum_tpd is None or record.minimum_tpd >= -feed_search.tpd_tolerance:
            continue
        w = record.witness_composition
        for sign, label in ((1, 'trial/feed'), (-1, 'feed/trial')):
            try:
                seed = _center_seed(tuple(sign*(log(w[i])-log(z[i])) if z[i] > 0 else 0.0
                                          for i in range(len(z))), z)
                if not any(max(abs(a-b) for a, b in zip(seed, old)) < 1e-6 for _, old in seeds):
                    seeds.append((record.label+' '+label, seed))
            except (ValueError, ArithmeticError) as error:
                attempts.append(f'{record.label} seed: {error}')

    for label, seed in seeds:
        # Different consistent root choices may lead to different solutions.
        for branch in ((0, -1), (0, 0), (-1, -1), (-1, 0)):
            try:
                logk = seed
                state = evaluate(logk, branch)
                for iteration in range(1, max_iterations+1):
                    beta, x, y, l, v, residuals, norm, xl, yv = state
                    if norm <= tolerance:
                        break
                    if iteration == max_iterations:
                        raise ArithmeticError('Flash iteration limit reached.')
                    # Damped SSI with backtracking: preserve a physical RR
                    # bracket and require an actual fugacity-residual decrease.
                    step = 1.0
                    for _ in range(24):
                        proposal = tuple(a+step*r for a, r in zip(logk, residuals))
                        try:
                            trial = evaluate(proposal, branch)
                            if trial[6] < norm:
                                logk, state = proposal, trial
                                break
                        except (ValueError, ArithmeticError, RuntimeError):
                            pass
                        step *= 0.5
                    else:
                        raise ArithmeticError('No decreasing feasible log-K step was found.')
                if l.g_residual_rt-xl.minimum_g_residual_rt > 1e-8 or \
                   v.g_residual_rt-yv.minimum_g_residual_rt > 1e-8:
                    raise ArithmeticError('A phase root is not Gibbs-preferred at its composition.')
                material = max(abs(z[i]-(1-beta)*x[i]-beta*y[i]) for i in range(len(z)))
                normalization = max(abs(fsum(x)-1), abs(fsum(y)-1))
                gibbs_change, gibbs_resolution = _gibbs_assessment(
                    z, x, y, beta, reference.ln_phi, l.ln_phi, v.ln_phi)
                details = (f'beta={beta:.16g}; fugacity={norm:.6g}; '
                    f'material={material:.6g}; normalization={normalization:.6g}; '
                    f'dG_RT={gibbs_change:.16g}; Gibbs_resolution_RT={gibbs_resolution:.6g}')
                if material > 1e-10:
                    raise ArithmeticError('Component material balance failed: '+details)
                if normalization > 1e-10:
                    raise ArithmeticError('Phase normalization failed: '+details)
                if gibbs_change >= -gibbs_resolution:
                    reason = ('Gibbs increase detected' if gibbs_change > gibbs_resolution
                              else 'Gibbs decrease is numerically unresolved')
                    raise ArithmeticError(reason+': '+details)
                if abs(l.z-v.z) < 1e-7:
                    raise ArithmeticError('Phase density ordering is ambiguous in this baseline solver.')
                if l.z > v.z:
                    x, y, l, v, beta = y, x, v, l, 1-beta
                phases = tuple(search_pr_stability(SimpleNamespace(
                    components=mixture.components, mole_fractions=composition), conditions,
                    kij=kk, max_iterations=stability_max_iterations) for composition in (x, y))
                if any(q.status != 'no_negative_tpd_found' for q in phases):
                    raise ArithmeticError('Post-flash local phase stability checks did not pass.')
                return FlashResult('two_phase',
                    'Two-phase solution passed local checks; global stability is not certified.',
                    feed_search, beta, x, y, l.z, v.z, norm, material, normalization,
                    gibbs_change, iteration, phases, tuple(attempts), gibbs_resolution)
            except (ValueError, ArithmeticError, RuntimeError) as error:
                attempts.append(f'{label}, roots {branch}: {error}')
    return FlashResult('inconclusive',
        'Feed is unstable but no validated two-phase split was obtained.',
        feed_search, attempts=tuple(attempts))
