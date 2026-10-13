"""Presentation helpers shared by the PetroFlash desktop interface and tests."""

from __future__ import annotations


PROPERTY_FIELDS = (
    ("critical_temperature", "دمای بحرانی"),
    ("critical_pressure", "فشار بحرانی"),
    ("acentric_factor", "ضریب بی‌مرکزی"),
    ("molar_mass", "جرم مولی"),
)


def component_property_rows(component):
    """Return every stored EOS property and its provenance for a component."""
    rows = []
    for field, label in PROPERTY_FIELDS:
        record = getattr(component, field)
        rows.append({
            "component": component.name,
            "cas": getattr(component, "cas_number", ""),
            "formula": getattr(component, "formula", ""),
            "field": field,
            "property": label,
            "value": format(record.value, ".12g"),
            "unit": record.unit,
            "source": record.source,
            "method": record.method,
            "data_kind": getattr(record.data_kind, "value", record.data_kind),
            "uncertainty": ("نامشخص" if record.uncertainty is None
                            else format(record.uncertainty, ".8g")),
            "uncertainty_text": ("not reported" if record.uncertainty is None
                                 else format(record.uncertainty, ".8g")),
            "reference": record.reference,
            "notes": record.notes,
        })
    return tuple(rows)


def format_flash_result(result, mixture, conditions=None):
    """Format accepted fields in LTR text; keep Persian UI labels separate."""
    lines = ["PetroFlash TP flash", "Model: Peng-Robinson (PR1976)",
             "Binary interaction parameters: kij = 0 (assumed, not fitted)"]
    if conditions is not None:
        lines.extend((
            f"Temperature: {conditions.temperature_k:.10g} K ({conditions.temperature_k - 273.15:.10g} C)",
            f"Absolute pressure: {conditions.pressure_pa:.10g} Pa ({conditions.pressure_pa / 1e5:.10g} bar)",
        ))
    lines.append("Feed: " + ", ".join(
        f"{name}={percent:.8g} mol%"
        for name, percent in zip(mixture.names, mixture.mole_percentages)
    ))
    lines.append(f"Status: {result.status}")
    lines.append(result.message)
    stability = getattr(result, "feed_stability", None)
    if stability is not None:
        lines.append(f"Feed stability search: {stability.status}")
        minimum = getattr(stability, "minimum_tpd", None)
        if minimum is not None:
            lines.append(f"Minimum evaluated TPD/(RT): {minimum:.10g}")

    if result.status == "two_phase":
        required = (result.beta, result.liquid_composition,
                    result.vapor_composition, result.liquid_z, result.vapor_z)
        if any(value is None for value in required):
            lines.append("Incomplete output: phase split is not displayed.")
            return "\n".join(lines)
        lines.extend((
            f"Vapor mole fraction, beta: {result.beta:.12g}",
            f"Liquid mole fraction: {1.0-result.beta:.12g}",
            f"Liquid Z: {result.liquid_z:.12g}",
            f"Vapor Z: {result.vapor_z:.12g}",
            "",
            "Compositions (mole fractions):",
            f"{'Component':<20} {'Feed z':>13} {'Liquid x':>13} {'Vapor y':>13}",
        ))
        for name, z, x, y in zip(
            mixture.names, mixture.mole_fractions,
            result.liquid_composition, result.vapor_composition,
        ):
            lines.append(f"{name:<20} {z:>13.8g} {x:>13.8g} {y:>13.8g}")
        for label, value in (
            ("Log-fugacity residual", result.fugacity_residual),
            ("Material-balance residual", result.material_residual),
            ("Normalization residual", result.normalization_residual),
            ("Gibbs change/(RT)", result.gibbs_change_rt),
            ("Estimated Gibbs resolution/(RT)", getattr(result, "gibbs_resolution_rt", None)),
        ):
            if value is not None:
                lines.append(f"{label}: {value:.10g}")
        lines.append(f"Iterations in accepted attempt: {result.iterations}")
        phase_checks = getattr(result, "phase_stability", ())
        if phase_checks:
            lines.append("Post-flash local searches: " + ", ".join(q.status for q in phase_checks))
        lines.append("Local checks do not certify global stability or experimental validity.")
    elif result.status == "single_phase_candidate":
        lines.append("No vapor fraction or liquid/vapor label has been assigned.")
        lines.append("A local search found no negative TPD; this is not a global stability certificate.")
    else:
        lines.append("No accepted phase split is available.")
        for attempt in getattr(result, "attempts", ()):
            lines.append(f"- {attempt}")
    return "\n".join(lines)
