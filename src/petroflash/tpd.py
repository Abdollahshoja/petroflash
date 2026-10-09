"""Dimensionless tangent-plane distance at one specified trial composition.

No minimization is performed; nonnegative sampled TPD does not prove stability.
Reference and trial coefficients must use the same T, absolute P and EOS model.
"""

from dataclasses import dataclass
from math import fsum, log, isfinite

from .pr_phase import PRPhaseEvaluation, evaluate_pr_phase, evaluate_mixture_pr_phase
from .pr_pure import _number, component_pr_parameters


def _composition(values, name):
    result = tuple(_number(v, name) for v in values)
    if not result or any(v < 0 or v > 1 for v in result):
        raise ValueError(f'{name} must be nonempty and lie in [0, 1].')
    if abs(fsum(result)-1) > 1e-10:
        raise ValueError(f'{name} must sum to one; no normalization performed.')
    return result


def _compositions(reference, trial):
    z = _composition(reference, 'reference composition')
    w = _composition(trial, 'trial composition')
    if len(z) != len(w):
        raise ValueError('Reference and trial must have the same component order and length.')
    if any(zi == 0 and wi > 0 for zi, wi in zip(z, w)):
        raise ValueError('A trial cannot introduce a component absent from the feed.')
    return z, w


def tangent_plane_distance(*, reference_mole_fractions, trial_mole_fractions,
                           reference_ln_phi, trial_ln_phi):
    """TPD/(RT) = sum w_i [ln(w_i)+ln(phi_i(w))-ln(z_i)-ln(phi_i(z))].

    On the closed composition simplex, w_i=0 contributes zero. If z_i=0,
    w_i must also be zero (nonreactive feed support restriction).
    No clipping of compositions, logarithms or small negative TPD is performed.
    This algebraic interface does not verify the provenance of supplied ln(phi).
    """
    z, w = _compositions(reference_mole_fractions, trial_mole_fractions)
    ref = tuple(_number(v, 'reference ln_phi') for v in reference_ln_phi)
    trial = tuple(_number(v, 'trial ln_phi') for v in trial_ln_phi)
    if len(ref) != len(z) or len(trial) != len(z):
        raise ValueError('Both ln_phi vectors must match the composition length.')
    try:
        result = fsum(wi*(log(wi)-log(zi)+pi-ri)
                      for zi, wi, pi, ri in zip(z, w, trial, ref) if wi > 0)
    except (OverflowError, ValueError):
        raise ValueError('TPD evaluation exceeds the numerical range.') from None
    if not isfinite(result):
        raise ValueError('TPD must be finite.')
    return result


@dataclass(frozen=True, slots=True)
class PRTPDTrial:
    """TPD values for every admissible root at one specified trial composition."""

    trial_evaluation: PRPhaseEvaluation
    tpd_values: tuple[float, ...]
    minimum_tpd: float


def evaluate_pr_tpd(*, reference_mole_fractions, trial_mole_fractions,
                    reference_ln_phi, a_t, b, kij, temperature_k, pressure_pa):
    """Evaluate every trial root against one supplied reference tangent plane."""
    z, w = _compositions(reference_mole_fractions, trial_mole_fractions)
    ref = tuple(reference_ln_phi)
    evaluation = evaluate_pr_phase(mole_fractions=w, a_t=a_t, b=b, kij=kij,
                                   temperature_k=temperature_k, pressure_pa=pressure_pa)
    values = tuple(tangent_plane_distance(reference_mole_fractions=z,
        trial_mole_fractions=w, reference_ln_phi=ref, trial_ln_phi=state.ln_phi)
        for state in evaluation.candidates)
    return PRTPDTrial(evaluation, values, min(values))


def evaluate_mixture_pr_tpd(mixture, conditions, *, trial_mole_fractions, kij,
                            reference_root_index=None):
    """Use real feed objects; reference root defaults to the unique preferred one.

    If reference roots tie, require an explicit index rather than choosing
    arbitrarily. An explicit nonpreferred index is allowed for diagnostics;
    negative TPD then concerns that selected reference, not another root.
    """
    z, w = _compositions(mixture.mole_fractions, trial_mole_fractions)
    kk = tuple(tuple(row) for row in kij)
    reference = evaluate_mixture_pr_phase(mixture, conditions, kij=kk)
    if reference_root_index is None:
        if len(reference.preferred_indices) != 1:
            raise ValueError('Reference Gibbs roots tie; specify reference_root_index.')
        index = reference.preferred_indices[0]
    else:
        if isinstance(reference_root_index, bool) or not isinstance(reference_root_index, int):
            raise TypeError('reference_root_index must be an integer.')
        index = reference_root_index
        if not 0 <= index < len(reference.candidates):
            raise ValueError('reference_root_index is outside the candidate range.')
    pure = tuple(component_pr_parameters(c, conditions) for c in mixture.components)
    return evaluate_pr_tpd(reference_mole_fractions=z, trial_mole_fractions=w,
        reference_ln_phi=reference.candidates[index].ln_phi,
        a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure), kij=kk,
        temperature_k=conditions.temperature_k, pressure_pa=conditions.pressure_pa)
