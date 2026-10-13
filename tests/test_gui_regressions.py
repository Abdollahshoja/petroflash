"""Layout contract checks without a display, and screenshot-input regressions."""

from pathlib import Path
from types import SimpleNamespace
import unittest

from petroflash.database import ComponentDatabase
from petroflash.conditions import TPConditions
from petroflash.mixture import Mixture
from petroflash.pr_mixing import zero_kij
from petroflash.flash import flash_tp
from petroflash.gui import PetroFlashGUI, THERMODYNAMIC_MODELS
from petroflash.gui_helpers import format_flash_result


class Widget:
    def __init__(self, parent=None, **options):
        self.options = options
        self.grid_options = {}

    def grid(self, **options):
        self.grid_options = options

    def configure(self, **options):
        self.options.update(options)

    def columnconfigure(self, *args, **kwargs): pass
    def rowconfigure(self, *args, **kwargs): pass
    def heading(self, *args, **kwargs): pass
    def column(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass
    def yview(self, *args): pass
    def xview(self, *args): pass
    def set(self, *args): pass


class Variable:
    def __init__(self, value=None): self.value = value
    def get(self): return self.value


class Toolkit:
    """Capture widget construction and geometry, without pretending to render."""
    def __init__(self): self.created = []

    def __getattr__(self, kind):
        def build(parent=None, **options):
            widget = Widget(parent, **options)
            self.created.append((kind, widget))
            return widget
        return build


class TestGUILayout(unittest.TestCase):
    def setUp(self):
        self.app = PetroFlashGUI.__new__(PetroFlashGUI)
        self.app.ttk = Toolkit()
        self.app.tk = SimpleNamespace(
            VERTICAL="vertical", HORIZONTAL="horizontal",
            Text=Widget, StringVar=Variable,
        )

    def test_horizontal_scrollbar_does_not_cover_table(self):
        self.app._build_property_table(Widget())
        horizontal = next(w for kind, w in self.app.ttk.created
                          if kind == "Scrollbar" and w.options["orient"] == "horizontal")
        details = next(w for kind, w in self.app.ttk.created if kind == "LabelFrame")
        self.assertGreater(horizontal.grid_options["row"], self.app.property_tree.grid_options["row"])
        self.assertGreater(details.grid_options["row"], horizontal.grid_options["row"])

    def test_only_implemented_model_is_preselected_and_disabled(self):
        self.app._build_conditions(Widget())
        self.assertEqual(self.app.thermo_model_var.get(), "Peng-Robinson (PR1976)")
        self.assertEqual(self.app.thermo_model_box.options["state"], "disabled")
        self.assertEqual(len(THERMODYNAMIC_MODELS), 1)
        self.assertIs(THERMODYNAMIC_MODELS[self.app.thermo_model_var.get()], flash_tp)
        self.assertFalse(any(kind == "Checkbutton" for kind, w in self.app.ttk.created))


class TestScreenshotFeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = ComponentDatabase.from_file(Path(__file__).resolve().parents[1] / "data/components.json")

    def run_case(self, pressure_bar):
        mixture = Mixture.from_mole_percentages(
            self.db, ["ethane", "n-butane", "isobutane"], [30, 20, 50]
        )
        conditions = TPConditions.from_units(-10, pressure_bar, temperature_unit="C", pressure_unit="bar")
        result = flash_tp(mixture, conditions, kij=zero_kij(3))
        return mixture, conditions, result

    def test_screenshot_100_bar_is_only_a_single_phase_candidate(self):
        mixture, conditions, result = self.run_case(100)
        self.assertEqual(conditions.temperature_k, 263.15)
        self.assertEqual(conditions.pressure_pa, 1e7)
        self.assertEqual(result.status, "single_phase_candidate")
        self.assertIsNone(result.beta)
        self.assertNotIn("Vapor mole fraction, beta:", format_flash_result(result, mixture, conditions))

    def test_same_feed_at_2_bar_matches_independent_pr_reference(self):
        mixture, conditions, result = self.run_case(2)
        self.assertEqual(result.status, "two_phase")
        # Independent simultaneous least-squares PR reference at commit 4f30a9f.
        self.assertAlmostEqual(result.beta, 0.49398360470763825, delta=1e-7)
        for z, x, y in zip(mixture.mole_fractions, result.liquid_composition, result.vapor_composition):
            self.assertAlmostEqual(z, (1-result.beta)*x+result.beta*y, delta=1e-10)
        text = format_flash_result(result, mixture, conditions)
        self.assertIn("2 bar", text)
        self.assertIn("Vapor mole fraction, beta:", text)


if __name__ == "__main__":
    unittest.main()
