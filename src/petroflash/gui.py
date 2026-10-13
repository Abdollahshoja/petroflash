"""Tkinter desktop interface for component selection and PR1976 TP flash."""

from __future__ import annotations

import argparse
import queue
import threading

from .conditions import TPConditions
from .database import ComponentDatabase
from .flash import flash_tp
from .gui_helpers import component_property_rows, format_flash_result
from .mixture import Mixture
from .pr_mixing import zero_kij

THERMODYNAMIC_MODELS = {"Peng-Robinson (PR1976)": flash_tp}


class PetroFlashGUI:
    """Small desktop form that delegates all calculations to PetroFlash."""

    def __init__(self, root, database):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.database = database
        self.all_names = tuple(database.names())
        self.visible_names = ()
        self.selected_names = ()
        self.filtering_components = False
        self.percent_by_name = {}
        self.percent_vars = {}
        self.property_by_iid = {}
        self.results_queue = queue.Queue()
        self.busy = False

        root.option_add("*Font", ("Tahoma", 10))
        style = ttk.Style(root)
        style.configure("Treeview", rowheight=27, font=("Tahoma", 10))
        style.configure("Treeview.Heading", font=("Tahoma", 10, "bold"))

        root.title("PetroFlash | TP Flash | PR1976 | GUI v2")
        root.geometry("1420x900")
        root.minsize(1080, 720)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        shell = ttk.Frame(root, padding=10)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=3)
        shell.rowconfigure(3, weight=2)

        ttk.Label(
            shell,
            text="مواد را انتخاب کنید؛ پس از انتخاب، خواص ثبت‌شدهٔ هر ماده در جدول نمایش داده می‌شود.",
            wraplength=1300,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        workspace = ttk.Panedwindow(shell, orient=tk.HORIZONTAL)
        workspace.grid(row=1, column=0, sticky="nsew")
        selection = ttk.LabelFrame(workspace, text="انتخاب مواد", padding=8)
        properties = ttk.LabelFrame(workspace, text="خواص مواد انتخاب‌شده", padding=8)
        workspace.add(selection, weight=1)
        workspace.add(properties, weight=4)
        self._build_component_selector(selection)
        self._build_property_table(properties)

        input_panel = ttk.LabelFrame(shell, text="ترکیب خوراک و شرایط", padding=8)
        input_panel.grid(row=2, column=0, sticky="ew", pady=(8, 8))
        input_panel.columnconfigure(0, weight=3)
        input_panel.columnconfigure(1, weight=2)
        self._build_composition_editor(input_panel)
        self._build_conditions(input_panel)

        results = ttk.LabelFrame(shell, text="نتایج محاسبه", padding=8)
        results.grid(row=3, column=0, sticky="nsew")
        results.rowconfigure(1, weight=1)
        results.columnconfigure(0, weight=1)
        self.result_status = self.tk.StringVar(value="آمادهٔ محاسبه")
        ttk.Label(results, textvariable=self.result_status, anchor="e").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5)
        )
        self.results_text = tk.Text(results, wrap="word", height=12, state="disabled", font=("Consolas", 11))
        result_scroll = ttk.Scrollbar(results, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=result_scroll.set)
        self.results_text.grid(row=1, column=0, sticky="nsew")
        result_scroll.grid(row=1, column=1, sticky="ns")
        self._set_results("Select components and enter mole percentages, temperature and absolute pressure.")

    def _build_component_selector(self, parent):
        tk, ttk = self.tk, self.ttk
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        ttk.Label(parent, text="جست‌وجوی نام یا شناسهٔ ماده").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search = ttk.Entry(parent, textvariable=self.search_var)
        search.grid(row=1, column=0, sticky="ew", pady=(3, 6))
        self.search_var.trace_add("write", self._filter_components)
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.component_list = tk.Listbox(list_frame, selectmode=tk.EXTENDED, exportselection=False)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.component_list.yview)
        self.component_list.configure(yscrollcommand=scroll.set)
        self.component_list.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.component_list.bind("<<ListboxSelect>>", self._selection_changed)
        self._filter_components()
        ttk.Label(parent, text="انتخاب چند ماده\nCtrl + Click / Shift + Click", wraplength=230).grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )

    def _selected_visible_names(self):
        return tuple(self.visible_names[i] for i in self.component_list.curselection())

    def _filter_components(self, *_):
        if not hasattr(self, "component_list"):
            return
        # Keep selected components that are temporarily hidden by the search.
        selected = (set(self.selected_names) - set(self.visible_names))
        selected.update(self._selected_visible_names())
        query = self.search_var.get().strip().casefold()
        tk = self.tk
        names = []
        self.filtering_components = True
        self.component_list.delete(0, tk.END)
        for name in self.all_names:
            component = self.database.get(name)
            label = f"{component.name} | {component.cas_number}"
            if query and query not in name.casefold() and query not in component.cas_number.casefold():
                continue
            index = len(names)
            names.append(name)
            self.component_list.insert(tk.END, label)
            if name in selected:
                self.component_list.selection_set(index)
        self.visible_names = tuple(names)
        self.filtering_components = False

    def _selection_changed(self, _event=None):
        if self.filtering_components:
            return
        for name, variable in self.percent_vars.items():
            self.percent_by_name[name] = variable.get()
        hidden_selected = set(self.selected_names) - set(self.visible_names)
        self.selected_names = tuple(
            name for name in self.all_names
            if name in hidden_selected or name in self._selected_visible_names()
        )
        self._render_properties()
        self._render_composition_rows()

    def _build_property_table(self, parent):
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(2, weight=1)
        columns = ("component", "cas", "formula", "property", "value", "unit")
        self.property_tree = ttk.Treeview(parent, columns=columns, show="headings", height=9)
        headings = {
            "component": ("ماده", 145), "cas": ("CAS", 110),
            "formula": ("فرمول", 80), "property": ("خاصیت", 150),
            "value": ("مقدار", 130), "unit": ("واحد", 90),
        }
        for column, (label, width) in headings.items():
            self.property_tree.heading(column, text=label)
            self.property_tree.column(column, width=width, minwidth=75, stretch=True)
        vscroll = ttk.Scrollbar(parent, orient=self.tk.VERTICAL, command=self.property_tree.yview)
        hscroll = ttk.Scrollbar(parent, orient=self.tk.HORIZONTAL, command=self.property_tree.xview)
        self.property_tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.property_tree.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        self.property_tree.bind("<<TreeviewSelect>>", self._show_property_details)

        detail_frame = ttk.LabelFrame(parent, text="منبع، روش، عدم‌قطعیت و یادداشت — برای مشاهده روی هر خاصیت کلیک کنید", padding=4)
        detail_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)
        self.property_details = self.tk.Text(detail_frame, wrap="word", height=6, state="disabled", font=("Consolas", 10))
        dscroll = ttk.Scrollbar(detail_frame, orient=self.tk.VERTICAL, command=self.property_details.yview)
        self.property_details.configure(yscrollcommand=dscroll.set)
        self.property_details.grid(row=0, column=0, sticky="nsew")
        dscroll.grid(row=0, column=1, sticky="ns")

    def _render_properties(self):
        for iid in self.property_tree.get_children():
            self.property_tree.delete(iid)
        self.property_by_iid.clear()
        for name in self.selected_names:
            component = self.database.get(name)
            for row in component_property_rows(component):
                iid = self.property_tree.insert("", "end", values=(
                    row["component"], row["cas"], row["formula"],
                    row["property"], row["value"], row["unit"],
                ))
                self.property_by_iid[iid] = row
        children = self.property_tree.get_children()
        if children:
            self.property_tree.selection_set(children[0])
            self._show_property_details()
        else:
            self._set_text(self.property_details, "ماده‌ای انتخاب نشده است.")

    def _show_property_details(self, _event=None):
        selection = self.property_tree.selection()
        if not selection:
            return
        row = self.property_by_iid.get(selection[0])
        if row is None:
            return
        detail = "\n".join((
            f"Component: {row['component']} | CAS: {row['cas']} | Formula: {row['formula']}",
            f"Property: {row['field']} = {row['value']} {row['unit']}",
            f"Source: {row['source']} | Method: {row['method']}",
            f"Data classification: {row['data_kind']} | Uncertainty: {row['uncertainty_text']}",
            f"Reference: {row['reference']}", f"Notes: {row['notes']}",
        ))
        self._set_text(self.property_details, detail)

    def _build_composition_editor(self, parent):
        ttk = self.ttk
        frame = ttk.LabelFrame(parent, text="درصد مولی خوراک", padding=5)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        canvas = self.tk.Canvas(frame, height=128, highlightthickness=0)
        scroll = ttk.Scrollbar(frame, orient=self.tk.VERTICAL, command=canvas.yview)
        self.composition_rows = ttk.Frame(canvas)
        self.composition_rows.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.composition_rows, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self._render_composition_rows()

    def _render_composition_rows(self):
        if not hasattr(self, "composition_rows"):
            return
        for child in self.composition_rows.winfo_children():
            child.destroy()
        self.percent_vars = {}
        ttk = self.ttk
        if not self.selected_names:
            ttk.Label(self.composition_rows, text="ابتدا مواد را از فهرست انتخاب کنید.").grid(
                row=0, column=0, sticky="w", padx=4, pady=4
            )
            return
        ttk.Label(self.composition_rows, text="ماده").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(self.composition_rows, text="درصد مولی (%)").grid(row=0, column=1, sticky="w", padx=4)
        for row_number, name in enumerate(self.selected_names, 1):
            ttk.Label(self.composition_rows, text=name).grid(row=row_number, column=0, sticky="w", padx=4, pady=2)
            variable = self.tk.StringVar(value=self.percent_by_name.get(name, ""))
            entry = ttk.Entry(self.composition_rows, textvariable=variable, width=16)
            entry.grid(row=row_number, column=1, sticky="w", padx=4, pady=2)
            variable.trace_add("write", lambda *_args, n=name, v=variable: self.percent_by_name.__setitem__(n, v.get()))
            self.percent_vars[name] = variable

    def _build_conditions(self, parent):
        ttk = self.ttk
        frame = ttk.LabelFrame(parent, text="شرایط و مدل", padding=5)
        frame.grid(row=0, column=1, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="دما").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.temperature_var = self.tk.StringVar()
        ttk.Entry(frame, textvariable=self.temperature_var, width=14).grid(row=0, column=1, sticky="ew", padx=4)
        self.temperature_unit = self.tk.StringVar(value="K")
        ttk.Combobox(frame, textvariable=self.temperature_unit, values=("K", "C"), state="readonly", width=6).grid(
            row=0, column=2, sticky="w", padx=4
        )
        ttk.Label(frame, text="فشار مطلق").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.pressure_var = self.tk.StringVar()
        ttk.Entry(frame, textvariable=self.pressure_var, width=14).grid(row=1, column=1, sticky="ew", padx=4)
        self.pressure_unit = self.tk.StringVar(value="bar")
        ttk.Combobox(frame, textvariable=self.pressure_unit, values=("bar", "Pa"), state="readonly", width=6).grid(
            row=1, column=2, sticky="w", padx=4
        )
        ttk.Label(frame, text="مدل ترمودینامیکی").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.thermo_model_var = self.tk.StringVar(value="Peng-Robinson (PR1976)")
        self.thermo_model_box = ttk.Combobox(
            frame, textvariable=self.thermo_model_var, values=tuple(THERMODYNAMIC_MODELS),
            state="disabled", width=28,
        )
        self.thermo_model_box.grid(row=2, column=1, columnspan=2, sticky="ew", padx=4)
        ttk.Label(frame, text="فعلاً فقط مدل پنگ–رابینسون پیاده‌سازی شده است.").grid(
            row=3, column=0, columnspan=3, sticky="w", padx=4, pady=3
        )
        ttk.Label(frame, text="kij = 0  (assumed; no binary-parameter dataset)").grid(
            row=4, column=0, columnspan=3, sticky="w", padx=4, pady=3
        )
        ttk.Label(
            frame,
            text="فلش فعلی برای هیدروکربن‌های ساده و تعادل بخار–مایع است؛ فشار باید مطلق باشد.",
            wraplength=420,
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=3)
        self.calculate_button = ttk.Button(frame, text="محاسبهٔ فلش", command=self._calculate)
        self.calculate_button.grid(row=5, column=2, sticky="e", padx=4, pady=3)

    def _set_text(self, widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", self.tk.END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _set_results(self, value):
        self._set_text(self.results_text, value)

    def _calculate(self):
        if self.busy:
            return
        try:
            names = self.selected_names
            if not names:
                raise ValueError("ابتدا دست‌کم یک ماده انتخاب کنید.")
            calculation = THERMODYNAMIC_MODELS[self.thermo_model_var.get()]
            percentages = []
            for name in names:
                raw = self.percent_vars[name].get().strip()
                if not raw:
                    raise ValueError(f"درصد مولی {name} وارد نشده است.")
                percentages.append(float(raw))
            mixture = Mixture.from_mole_percentages(self.database, names, percentages)
            conditions = TPConditions.from_units(
                float(self.temperature_var.get()), float(self.pressure_var.get()),
                temperature_unit=self.temperature_unit.get(), pressure_unit=self.pressure_unit.get(),
            )
            kij = zero_kij(len(mixture.components))
        except (TypeError, ValueError, KeyError) as error:
            self.result_status.set("ورودی نامعتبر")
            self._set_results(str(error))
            return

        self.busy = True
        self.calculate_button.configure(state="disabled")
        self.result_status.set("محاسبه در حال انجام است")
        self._set_results("Calculating...\nModel: Peng-Robinson (PR1976)\nBinary interaction parameters: kij = 0 (assumed).")

        def worker():
            try:
                result = calculation(mixture, conditions, kij=kij)
            except Exception as error:  # Surface numerical/model failures without hiding them.
                self.results_queue.put((False, f"{type(error).__name__}: {error}"))
            else:
                self.results_queue.put((True, (result, mixture, conditions)))

        threading.Thread(target=worker, name="petroflash-flash", daemon=True).start()
        self.root.after(100, self._poll_results)

    def _poll_results(self):
        try:
            succeeded, payload = self.results_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_results)
            return
        self.busy = False
        self.calculate_button.configure(state="normal")
        if not succeeded:
            self.result_status.set("خطای محاسباتی")
            self._set_results(payload)
            return
        result, mixture, conditions = payload
        self.result_status.set({
            "two_phase": "دو فاز — جواب پذیرفته‌شده با کنترل‌های محلی",
            "single_phase_candidate": "نامزد تک‌فاز — برچسب مایع یا بخار تعیین نشده است",
            "inconclusive": "نامعین — تقسیم فازی پذیرفته‌شده‌ای به دست نیامد",
        }.get(result.status, "وضعیت ناشناخته"))
        self._set_results(format_flash_result(result, mixture, conditions))


def main(argv=None):
    parser = argparse.ArgumentParser(description="PetroFlash graphical TP flash interface")
    parser.add_argument("--database", default="data/components.json", help="Path to component JSON database")
    args = parser.parse_args(argv)
    try:
        database = ComponentDatabase.from_file(args.database)
    except (OSError, TypeError, ValueError, KeyError) as error:
        raise SystemExit(f"Database error: {error}") from error
    try:
        import tkinter as tk
    except ImportError as error:
        raise SystemExit("Tkinter is unavailable in this Python installation.") from error
    root = tk.Tk()
    PetroFlashGUI(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()
