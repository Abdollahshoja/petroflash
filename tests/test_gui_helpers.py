"""Headless tests for property visibility and safe result presentation."""

import unittest
from types import SimpleNamespace as S

from petroflash.gui_helpers import component_property_rows, format_flash_result


def record(value, unit, name):
    return S(value=value, unit=unit, source=f"source-{name}",
             method=f"method-{name}", data_kind="evaluated",
             uncertainty=None, reference=f"https://example.test/{name}",
             notes=f"notes-{name}")


class TestGUIHelpers(unittest.TestCase):
    def setUp(self):
        self.component = S(
            name="methane",
            cas_number="74-82-8", formula="CH4",
            critical_temperature=record(190.564, "K", "tc"),
            critical_pressure=record(4599200, "Pa", "pc"),
            acentric_factor=record(0.01142, "1", "omega"),
            molar_mass=record(0.01604, "kg/mol", "mw"),
        )

    def test_all_component_properties_and_provenance_are_available(self):
        rows = component_property_rows(self.component)
        self.assertEqual(len(rows), 4)
        self.assertEqual([row["unit"] for row in rows], ["K", "Pa", "1", "kg/mol"])
        self.assertEqual(rows[0]["source"], "source-tc")
        self.assertEqual(rows[0]["reference"], "https://example.test/tc")
        self.assertEqual(rows[0]["notes"], "notes-tc")
        self.assertEqual(rows[0]["uncertainty"], "نامشخص")
        self.assertEqual(rows[0]["cas"], "74-82-8")
        self.assertEqual(rows[0]["formula"], "CH4")
        self.assertEqual(rows[0]["uncertainty_text"], "not reported")

    def test_two_phase_result_shows_phase_compositions_and_residuals(self):
        mixture = S(names=("methane", "ethane"), mole_percentages=(50.0, 50.0),
                    mole_fractions=(0.5, 0.5))
        result = S(
            status="two_phase", message="passed local checks", beta=0.4,
            liquid_composition=(0.2, 0.8), vapor_composition=(0.95, 0.05),
            liquid_z=0.08, vapor_z=0.91, fugacity_residual=1e-9,
            material_residual=1e-16, normalization_residual=1e-13,
            gibbs_change_rt=-0.2, gibbs_resolution_rt=1e-13, iterations=8,
            feed_stability=S(status="unstable", minimum_tpd=-0.5),
            phase_stability=(S(status="no_negative_tpd_found"),
                             S(status="no_negative_tpd_found")),
            attempts=(),
        )
        text = format_flash_result(result, mixture, S(temperature_k=250.0, pressure_pa=2e6))
        self.assertIn("Vapor mole fraction, beta: 0.4", text)
        self.assertIn("Liquid x", text)
        self.assertIn("methane", text)
        self.assertIn("Material-balance residual", text)
        self.assertIn("global stability", text)
        self.assertIn("kij = 0 (assumed, not fitted)", text)
        self.assertIn("20 bar", text)
        self.assertTrue(text.isascii())

    def test_single_phase_candidate_does_not_invent_beta(self):
        mixture = S(names=("methane",), mole_percentages=(100.0,), mole_fractions=(1.0,))
        result = S(status="single_phase_candidate", message="local candidate",
                   feed_stability=S(status="no_negative_tpd_found", minimum_tpd=0.0),
                   attempts=())
        text = format_flash_result(result, mixture)
        self.assertIn("No vapor fraction or liquid/vapor label has been assigned", text)
        self.assertNotIn("Vapor mole fraction, beta:", text)

    def test_inconclusive_result_shows_failure_reasons_without_split(self):
        mixture = S(names=("methane",), mole_percentages=(100.0,), mole_fractions=(1.0,))
        result = S(status="inconclusive", message="no accepted split",
                   feed_stability=S(status="unstable", minimum_tpd=-0.1),
                   attempts=("attempt failed",))
        text = format_flash_result(result, mixture)
        self.assertIn("No accepted phase split is available", text)
        self.assertIn("attempt failed", text)
        self.assertNotIn("Vapor mole fraction, beta:", text)


if __name__ == "__main__":
    unittest.main()
