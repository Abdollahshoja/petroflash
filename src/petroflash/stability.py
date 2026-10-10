"""Multi-start, damped fixed-point TPD stationarity search for PR with explicit alpha selection.

This is a baseline local search, not a certified global minimizer. A negative
evaluated TPD is a witness even if that start subsequently fails to converge.
"""

from dataclasses import dataclass
from math import exp, fsum, isfinite, log

from .pr_phase import evaluate_pr_phase
from .pr_pure import _number, component_pr_parameters, validate_alpha_model
from .tpd import _composition, tangent_plane_distance


@dataclass(frozen=True, slots=True)
class StabilityStart:
    label: str
    converged: bool
    iterations: int
    minimum_tpd: float | None
    witness_composition: tuple[float, ...] | None
    stationarity_residual: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class StabilityResult:
    status: str
    reference_z: float
    minimum_tpd: float | None
    witness_composition: tuple[float, ...] | None
    starts: tuple[StabilityStart, ...]
    tpd_tolerance: float


def _softmax(log_values):
    shift = max(log_values)
    weights = tuple(exp(v-shift) for v in log_values)
    total = fsum(weights)
    if not isfinite(total) or total <= 0 or any(v == 0 for v in weights):
        raise ArithmeticError('Trial composition exceeds the floating-point range.')
    result = tuple(v/total for v in weights)
    if any(v == 0 for v in result):
        raise ArithmeticError("Normalized trial composition underflowed.")
    return result


def search_pr_stability(mixture, conditions, *, kij, max_iterations=200,
                        damping=0.5, stationarity_tolerance=1e-8,
                        tpd_tolerance=1e-8, alpha_model="PR1976"):
    """Search normalized TPD stationarity from feed, Wilson +/- and rich starts.

    Convergence checks the projected chemical-potential residual, not merely
    iteration step size. No-negative results are local search outcomes only.
    Zero-feed species are excluded from all generated trial compositions.
    Model validation and reference-evaluation errors propagate to the caller.
    """
    alpha_model = validate_alpha_model(alpha_model)
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise TypeError('max_iterations must be an integer.')
    if max_iterations < 1:
        raise ValueError('max_iterations must be positive.')
    damping = _number(damping, 'damping', positive=True)
    tolerance = _number(stationarity_tolerance, 'stationarity_tolerance', positive=True)
    tpd_tolerance = _number(tpd_tolerance, 'tpd_tolerance', positive=True)
    if damping > 1:
        raise ValueError('damping must lie in (0, 1].')
    z = _composition(mixture.mole_fractions, 'feed composition')
    if len(z) != len(mixture.components):
        raise ValueError('Composition must match the component count.')
    active = tuple(i for i, value in enumerate(z) if value > 0)
    pure = tuple(component_pr_parameters(c, conditions, alpha_model=alpha_model) for c in mixture.components)
    common = dict(a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure),
        kij=tuple(tuple(row) for row in kij), temperature_k=conditions.temperature_k,
        pressure_pa=conditions.pressure_pa)
    reference = evaluate_pr_phase(mole_fractions=z, **common)
    # A near tie in the reference may define different tangent planes.
    if len(reference.preferred_indices) != 1:
        return StabilityResult('inconclusive', reference.preferred_candidates[0].z,
            None, None, (), tpd_tolerance)
    ref = reference.preferred_candidates[0]
    d = tuple(log(z[i])+ref.ln_phi[i] for i in active)

    def full(values):
        result = [0.0]*len(z)
        for i, value in zip(active, values):
            result[i] = value
        return tuple(result)

    logz = tuple(log(z[i]) for i in active)
    seeds = [('feed', tuple(z[i] for i in active))]
    failed_seeds = []
    try:
        logk = tuple(log(mixture.components[i].critical_pressure.value)
            -log(conditions.pressure_pa)
            +5.373*(1+mixture.components[i].acentric_factor.value)
            *(1-mixture.components[i].critical_temperature.value/conditions.temperature_k)
            for i in active)
        for label, sign in (('Wilson vapor-like', 1), ('Wilson liquid-like', -1)):
            try:
                seeds.append((label, _softmax(tuple(v+sign*k for v, k in zip(logz, logk)))))
            except (ValueError, ArithmeticError) as error:
                failed_seeds.append(StabilityStart(label, False, 0, None, None, None, str(error)))
    except (ValueError, ArithmeticError) as error:
        failed_seeds.append(StabilityStart('Wilson seeds', False, 0, None, None, None, str(error)))
    for position, index in enumerate(active):
        values = tuple(0.1*z[i]+(0.9 if j == position else 0)
                       for j, i in enumerate(active))
        seeds.append((f'rich in {mixture.components[index].name}', _softmax(tuple(log(v) for v in values))))

    records = []
    for label, initial in seeds:
        current = initial
        minimum, witness, residual = None, None, None
        reason, converged, count = 'iteration limit', False, 0
        for count in range(1, max_iterations+1):
            try:
                w = full(current)
                trial = evaluate_pr_phase(mole_fractions=w, **common)
                # Exact minimum for the trial Gibbs envelope; retain all roots
                # in the phase evaluator, but use the lowest here.
                state = min(trial.candidates, key=lambda q: q.g_residual_rt)
                value = tangent_plane_distance(reference_mole_fractions=z,
                    trial_mole_fractions=w, reference_ln_phi=ref.ln_phi,
                    trial_ln_phi=state.ln_phi)
                if minimum is None or value < minimum:
                    minimum, witness = value, w
                gradients = tuple(log(current[j])+state.ln_phi[i]-d[j]
                                  for j, i in enumerate(active))
                average = fsum(current[j]*gradients[j] for j in range(len(active)))
                residual = max(abs(g-average) for g in gradients)
                if residual <= tolerance:
                    converged, reason = True, 'projected stationarity converged'
                    break
                target_logits = tuple(d[j]-state.ln_phi[i] for j, i in enumerate(active))
                next_logits = tuple((1-damping)*log(current[j])+damping*target_logits[j]
                                    for j in range(len(active)))
                current = _softmax(next_logits)
            except (TypeError, ValueError, ArithmeticError) as error:
                reason = f'numerical failure: {error}'
                break
        records.append(StabilityStart(label, converged, count, minimum, witness, residual, reason))
    records.extend(failed_seeds)
    valid = tuple(record for record in records if record.minimum_tpd is not None)
    best = min(valid, key=lambda r: r.minimum_tpd) if valid else None
    if best is not None and best.minimum_tpd < -tpd_tolerance:
        status = 'unstable'
    elif all(record.converged for record in records):
        status = 'no_negative_tpd_found'
    else:
        status = 'inconclusive'
    return StabilityResult(status, ref.z, best.minimum_tpd if best else None,
        best.witness_composition if best else None, tuple(records), tpd_tolerance)
