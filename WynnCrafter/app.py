from __future__ import annotations

import argparse
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from crafter_engine import (
    CrafterData,
    CraftSelection,
    WEAPON_TYPES,
    build_copy_long,
    build_copy_short,
    format_craft_summary,
    format_ingredient_summary,
    format_recipe_summary,
    format_warnings,
)
from crafter_optimizer import (
    CONSTRAINT_OPERATORS,
    METRIC_DISPLAY_OPTIONS,
    ROLL_MODE_OPTIONS,
    CrafterOptimizer,
    OptimizationConstraint,
    OptimizationObjective,
    coerce_optimization_objective,
    format_number,
    make_optimization_objective,
    resolve_metric_key,
)


WINDOW_SIZE = "1600x1040"
SEARCH_MODE_OPTIONS = {
    "Exact (filtered pool)": "exact",
    "MCTS (filtered pool)": "mcts",
}
SEARCH_MODE_LABELS = tuple(SEARCH_MODE_OPTIONS.keys())


class SearchableCombobox(ttk.Frame):
    def __init__(self, master: tk.Misc, values: list[str] | tuple[str, ...], textvariable: tk.StringVar, **kwargs: Any) -> None:
        width = int(kwargs.pop("width", 20))
        super().__init__(master, **kwargs)
        self.all_values = list(dict.fromkeys(values))
        self.filtered_values = list(self.all_values)
        self.textvariable = textvariable
        self._popup: tk.Toplevel | None = None
        self._popup_frame: tk.Frame | None = None
        self._listbox: tk.Listbox | None = None
        self._scrollbar: ttk.Scrollbar | None = None
        self._close_job: str | None = None
        self._variable_trace = self.textvariable.trace_add("write", self._on_variable_changed)

        self.columnconfigure(0, weight=1)
        self.entry = ttk.Entry(self, textvariable=self.textvariable, width=width)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.button = ttk.Button(self, text="v", width=2, command=self._toggle_popup)
        self.button.grid(row=0, column=1, sticky="ns", padx=(4, 0))

        self.entry.bind("<KeyRelease>", self._on_key_release, add="+")
        self.entry.bind("<Down>", self._on_down_key, add="+")
        self.entry.bind("<Up>", self._on_up_key, add="+")
        self.entry.bind("<Return>", self._on_return_key, add="+")
        self.entry.bind("<Escape>", self._on_escape_key, add="+")
        self.entry.bind("<FocusOut>", self._schedule_popup_close, add="+")
        self.button.bind("<FocusOut>", self._schedule_popup_close, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")

    def get(self) -> str:
        return self.textvariable.get()

    def set_values(self, values: list[str] | tuple[str, ...]) -> None:
        self.all_values = list(dict.fromkeys(values))
        self._refresh_filtered_values()
        self._update_popup_contents()

    def _on_destroy(self, _event: tk.Event) -> None:
        if self.textvariable and self._variable_trace:
            try:
                self.textvariable.trace_remove("write", self._variable_trace)
            except tk.TclError:
                pass
            self._variable_trace = ""
        self._hide_popup()

    def _on_variable_changed(self, *_args: Any) -> None:
        self._refresh_filtered_values()
        self._update_popup_contents()

    def _refresh_filtered_values(self) -> None:
        query = self.get().strip().lower()
        if not query:
            self.filtered_values = list(self.all_values[:500])
            return
        self.filtered_values = [
            value
            for value in self.all_values
            if query in value.lower()
        ][:500]

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in {"Up", "Down", "Left", "Right", "Escape", "Return", "Tab"}:
            return
        self._refresh_filtered_values()
        if self.filtered_values:
            self._show_popup()
        else:
            self._hide_popup()

    def _on_down_key(self, _event: tk.Event) -> str:
        self._refresh_filtered_values()
        if not self.filtered_values:
            return "break"
        self._show_popup()
        self._move_listbox_selection(1)
        return "break"

    def _on_up_key(self, _event: tk.Event) -> str:
        if self._popup is None or self._listbox is None or not self._popup.winfo_exists():
            return "break"
        self._move_listbox_selection(-1)
        return "break"

    def _on_return_key(self, _event: tk.Event) -> str:
        self._refresh_filtered_values()
        if self._popup is not None and self._listbox is not None and self._popup.winfo_exists():
            self._select_listbox_value()
            return "break"
        if self.filtered_values:
            self._apply_selection(self.filtered_values[0])
            return "break"
        return "break"

    def _on_escape_key(self, _event: tk.Event) -> str:
        self._hide_popup()
        return "break"

    def _toggle_popup(self) -> None:
        self._refresh_filtered_values()
        if self._popup is not None and self._popup.winfo_exists():
            self._hide_popup()
            return
        self._show_popup()

    def _ensure_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            return
        self._popup = tk.Toplevel(self)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.transient(self.winfo_toplevel())
        self._popup_frame = tk.Frame(self._popup, bd=1, highlightthickness=1)
        self._popup_frame.pack(fill=tk.BOTH, expand=True)
        self._listbox = tk.Listbox(
            self._popup_frame,
            activestyle="none",
            exportselection=False,
            relief=tk.FLAT,
            highlightthickness=0,
        )
        self._scrollbar = ttk.Scrollbar(self._popup_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=self._scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.bind("<ButtonRelease-1>", self._on_listbox_click, add="+")
        self._listbox.bind("<Return>", self._on_listbox_return, add="+")
        self._listbox.bind("<Escape>", self._on_listbox_escape, add="+")
        self._listbox.bind("<FocusOut>", self._schedule_popup_close, add="+")

    def _show_popup(self) -> None:
        self._refresh_filtered_values()
        if not self.filtered_values:
            self._hide_popup()
            return
        self._ensure_popup()
        if self._popup is None or self._listbox is None:
            return
        self._update_popup_contents()
        width = max(self.winfo_width(), 180)
        visible_rows = min(max(1, len(self.filtered_values)), 12)
        height = max(140, visible_rows * 22)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self._popup.geometry(f"{width}x{height}+{x}+{y}")
        self._popup.deiconify()
        self._popup.lift()

    def _hide_popup(self) -> None:
        if self._close_job is not None:
            try:
                self.after_cancel(self._close_job)
            except tk.TclError:
                pass
            self._close_job = None
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.withdraw()

    def _update_popup_contents(self) -> None:
        if self._listbox is None or not self._listbox.winfo_exists():
            return
        current_selection = self.get().strip().lower()
        self._listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self._listbox.insert(tk.END, value)
        if not self.filtered_values:
            self._hide_popup()
            return
        preferred_index = 0
        for index, value in enumerate(self.filtered_values):
            if value.lower() == current_selection:
                preferred_index = index
                break
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(preferred_index)
        self._listbox.activate(preferred_index)
        self._listbox.see(preferred_index)

    def _move_listbox_selection(self, delta: int) -> None:
        if self._listbox is None or not self._listbox.winfo_exists() or not self.filtered_values:
            return
        selection = self._listbox.curselection()
        current_index = selection[0] if selection else 0
        next_index = max(0, min(len(self.filtered_values) - 1, current_index + delta))
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(next_index)
        self._listbox.activate(next_index)
        self._listbox.see(next_index)

    def _select_listbox_value(self) -> None:
        if self._listbox is None or not self._listbox.winfo_exists():
            return
        selection = self._listbox.curselection()
        if not selection:
            if self.filtered_values:
                self._apply_selection(self.filtered_values[0])
            return
        index = selection[0]
        if 0 <= index < len(self.filtered_values):
            self._apply_selection(self.filtered_values[index])

    def _apply_selection(self, value: str) -> None:
        self.textvariable.set(value)
        self.entry.icursor(tk.END)
        self.entry.focus_set()
        self._hide_popup()
        self.event_generate("<<SearchableComboboxSelected>>")

    def _on_listbox_click(self, _event: tk.Event) -> None:
        self._select_listbox_value()

    def _on_listbox_return(self, _event: tk.Event) -> str:
        self._select_listbox_value()
        return "break"

    def _on_listbox_escape(self, _event: tk.Event) -> str:
        self._hide_popup()
        self.entry.focus_set()
        return "break"

    def _schedule_popup_close(self, _event: tk.Event | None = None) -> None:
        if self._close_job is not None:
            try:
                self.after_cancel(self._close_job)
            except tk.TclError:
                pass
        self._close_job = self.after(120, self._close_popup_if_needed)

    def _close_popup_if_needed(self) -> None:
        self._close_job = None
        focus_widget = self.focus_get()
        if focus_widget is None:
            self._hide_popup()
            return
        current: tk.Misc | None = focus_widget
        while current is not None:
            if current in {self, self.entry, self.button, self._popup, self._popup_frame, self._listbox, self._scrollbar}:
                return
            current = getattr(current, "master", None)
        self._hide_popup()


class WynnCrafterApp(tk.Tk):
    def __init__(self, data: CrafterData) -> None:
        super().__init__()
        self.data = data
        self.optimizer = CrafterOptimizer(data)
        self.current_result = None
        self.pending_recalc: str | None = None
        self._suspend_updates = False
        self.generated_options = []
        self.optimizer_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.optimizer_thread: threading.Thread | None = None
        self.search_stop_event = threading.Event()

        self.title("WynnCrafter")
        self.geometry(WINDOW_SIZE)
        self.minsize(1220, 760)

        self.recipe_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.hash_var = tk.StringVar()
        self.attack_speed_var = tk.StringVar(value="NORMAL")
        self.mat_vars = [tk.IntVar(value=3), tk.IntVar(value=3)]
        self.ingredient_vars = [tk.StringVar(value="No Ingredient") for _ in range(6)]
        self.material_label_vars = [
            tk.StringVar(value="Material 1 Tier"),
            tk.StringVar(value="Material 2 Tier"),
        ]
        self.status_var = tk.StringVar(value="Ready.")
        self.generator_status_var = tk.StringVar(
            value=(
                "Selected ingredients are locked. Empty ingredient slots are optimized with a filtered candidate "
                "pool per slot; Exact exhausts that pool and MCTS samples it."
            )
        )
        self.search_mode_var = tk.StringVar(value=SEARCH_MODE_LABELS[0])
        self.roll_mode_var = tk.StringVar(value="Average")
        self.top_n_var = tk.StringVar(value="5")
        self.objective_rows: list[dict[str, object]] = []
        self.constraint_rows: list[dict[str, object]] = []

        self.attack_speed_buttons: list[ttk.Radiobutton] = []

        self._configure_style()
        self._build_ui()
        self._apply_selection(self.data.default_selection(), recalculate=False)
        self._recalculate()
        self.add_objective_row("Health", "1")
        self.add_constraint_row()
        self.after(150, self._poll_optimizer_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", padding=4)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabelframe", padding=10)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        title = ttk.Label(root, text="WynnCrafter", style="Title.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        controls_shell = ttk.Frame(root)
        controls_shell.grid(row=1, column=0, sticky="ns", padx=(0, 12))
        controls_shell.columnconfigure(0, weight=1)
        controls_shell.rowconfigure(0, weight=1)

        self.controls_canvas = tk.Canvas(
            controls_shell,
            highlightthickness=0,
            borderwidth=0,
            width=470,
        )
        controls_scrollbar = ttk.Scrollbar(
            controls_shell,
            orient=tk.VERTICAL,
            command=self.controls_canvas.yview,
        )
        self.controls_canvas.configure(yscrollcommand=controls_scrollbar.set)
        self.controls_canvas.grid(row=0, column=0, sticky="ns")
        controls_scrollbar.grid(row=0, column=1, sticky="ns")

        controls = ttk.Frame(self.controls_canvas)
        controls.columnconfigure(0, weight=1)
        self._controls_canvas_window = self.controls_canvas.create_window(
            (0, 0),
            window=controls,
            anchor="nw",
        )
        controls.bind("<Configure>", self._update_controls_scrollregion, add="+")
        self.controls_canvas.bind("<Configure>", self._sync_controls_canvas_width, add="+")

        outputs = ttk.Frame(root)
        outputs.grid(row=1, column=1, sticky="nsew")

        outputs.columnconfigure(0, weight=1)
        outputs.rowconfigure(1, weight=1)

        self._build_controls(controls)
        self._build_outputs(outputs)

        status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.after_idle(self._update_controls_scrollregion)

    def _update_controls_scrollregion(self, _event=None) -> None:
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def _sync_controls_canvas_width(self, event: tk.Event) -> None:
        self.controls_canvas.itemconfigure(self._controls_canvas_window, width=event.width)

    def _build_controls(self, parent: ttk.Frame) -> None:
        recipe_frame = ttk.LabelFrame(parent, text="Recipe", style="Section.TLabelframe")
        recipe_frame.grid(row=0, column=0, sticky="ew")
        recipe_frame.columnconfigure(1, weight=1)

        ttk.Label(recipe_frame, text="Type").grid(row=0, column=0, sticky="w")
        recipe_combo = SearchableCombobox(
            recipe_frame,
            textvariable=self.recipe_var,
            values=self.data.recipe_type_names,
            width=26,
        )
        recipe_combo.grid(row=0, column=1, sticky="ew")
        self._bind_recipe_widget(recipe_combo)

        ttk.Label(recipe_frame, text="Level").grid(row=1, column=0, sticky="w")
        level_combo = SearchableCombobox(
            recipe_frame,
            textvariable=self.level_var,
            values=self.data.level_ranges,
            width=26,
        )
        level_combo.grid(row=1, column=1, sticky="ew")
        self._bind_recipe_widget(level_combo)

        ttk.Label(recipe_frame, text="Hash").grid(row=2, column=0, sticky="w")
        hash_entry = ttk.Entry(recipe_frame, textvariable=self.hash_var, width=26)
        hash_entry.grid(row=2, column=1, sticky="ew")
        hash_entry.bind("<Return>", self._load_hash)

        load_hash = ttk.Button(recipe_frame, text="Load Hash", command=self._load_hash)
        load_hash.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        material_frame = ttk.LabelFrame(parent, text="Materials", style="Section.TLabelframe")
        material_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        for row, label_var in enumerate(self.material_label_vars):
            ttk.Label(material_frame, textvariable=label_var).grid(row=row * 2, column=0, columnspan=3, sticky="w")
            for col, tier in enumerate((1, 2, 3)):
                button = ttk.Radiobutton(
                    material_frame,
                    text=str(tier),
                    value=tier,
                    variable=self.mat_vars[row],
                    command=self._schedule_recalculate,
                )
                button.grid(row=row * 2 + 1, column=col, sticky="w")

        attack_frame = ttk.LabelFrame(parent, text="Attack Speed", style="Section.TLabelframe")
        attack_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        for col, speed in enumerate(("SLOW", "NORMAL", "FAST")):
            button = ttk.Radiobutton(
                attack_frame,
                text=speed.title(),
                value=speed,
                variable=self.attack_speed_var,
                command=self._schedule_recalculate,
            )
            button.grid(row=0, column=col, sticky="w")
            self.attack_speed_buttons.append(button)

        ingredient_frame = ttk.LabelFrame(parent, text="Ingredients", style="Section.TLabelframe")
        ingredient_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        ingredient_frame.columnconfigure(1, weight=1)

        for idx, ingredient_var in enumerate(self.ingredient_vars, start=1):
            ttk.Label(ingredient_frame, text=f"Ing {idx}").grid(row=idx - 1, column=0, sticky="w")
            combo = SearchableCombobox(
                ingredient_frame,
                textvariable=ingredient_var,
                values=self.data.ingredient_display_names,
                width=34,
            )
            combo.grid(row=idx - 1, column=1, sticky="ew", pady=2)
            combo.bind("<<SearchableComboboxSelected>>", self._schedule_recalculate)
            combo.entry.bind("<FocusOut>", self._schedule_recalculate, add="+")
            combo.entry.bind("<KeyRelease>", self._schedule_recalculate, add="+")

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        for col in range(4):
            button_frame.columnconfigure(col, weight=1)

        ttk.Button(button_frame, text="Reset", command=self._reset).grid(row=0, column=0, sticky="ew")
        ttk.Button(button_frame, text="Copy Hash", command=self._copy_hash).grid(row=0, column=1, sticky="ew")
        ttk.Button(button_frame, text="Copy Short", command=self._copy_short).grid(row=0, column=2, sticky="ew")
        ttk.Button(button_frame, text="Copy Long", command=self._copy_long).grid(row=0, column=3, sticky="ew")

        self._build_generator_controls(parent)

    def _build_generator_controls(self, parent: ttk.Frame) -> None:
        generator_frame = ttk.LabelFrame(parent, text="Generator", style="Section.TLabelframe")
        generator_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        generator_frame.columnconfigure(1, weight=1)

        ttk.Label(generator_frame, text="Optimize For").grid(row=0, column=0, sticky="nw")
        objectives_frame = ttk.Frame(generator_frame)
        objectives_frame.grid(row=0, column=1, sticky="ew")
        objectives_frame.columnconfigure(0, weight=1)
        ttk.Label(objectives_frame, text="Metric").grid(row=0, column=0, sticky="w")
        ttk.Label(objectives_frame, text="Weight").grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.objectives_container = ttk.Frame(objectives_frame)
        self.objectives_container.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Button(objectives_frame, text="Add Objective", command=self.add_objective_row).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(6, 0),
        )

        ttk.Label(generator_frame, text="Roll Mode").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(
            generator_frame,
            textvariable=self.roll_mode_var,
            state="readonly",
            values=tuple(ROLL_MODE_OPTIONS.keys()),
            width=26,
        ).grid(row=1, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(generator_frame, text="Search Mode").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(
            generator_frame,
            textvariable=self.search_mode_var,
            state="readonly",
            values=SEARCH_MODE_LABELS,
            width=26,
        ).grid(row=2, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(generator_frame, text="Top Results").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(generator_frame, textvariable=self.top_n_var, width=8).grid(row=3, column=1, sticky="w", pady=(8, 0))

        constraints_frame = ttk.Frame(generator_frame)
        constraints_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        constraints_frame.columnconfigure(0, weight=1)
        ttk.Label(constraints_frame, text="Constraints").grid(row=0, column=0, sticky="w")
        self.constraints_container = ttk.Frame(constraints_frame)
        self.constraints_container.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        generator_buttons = ttk.Frame(generator_frame)
        generator_buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(generator_buttons, text="Add Constraint", command=self.add_constraint_row).pack(side=tk.LEFT)
        self.generate_button = ttk.Button(generator_buttons, text="Generate Options", command=self.start_generation)
        self.generate_button.pack(side=tk.LEFT, padx=(8, 0))
        self.stop_generation_button = ttk.Button(
            generator_buttons,
            text="Stop Search",
            command=self.stop_generation,
            state=tk.DISABLED,
        )
        self.stop_generation_button.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(
            generator_frame,
            textvariable=self.generator_status_var,
            wraplength=360,
            justify=tk.LEFT,
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_outputs(self, parent: ttk.Frame) -> None:
        warning_frame = ttk.LabelFrame(parent, text="Warnings", style="Section.TLabelframe")
        warning_frame.grid(row=0, column=0, sticky="ew")
        warning_frame.columnconfigure(0, weight=1)

        self.warning_text = ScrolledText(warning_frame, height=6, wrap="word")
        self.warning_text.grid(row=0, column=0, sticky="nsew")
        self.warning_text.configure(state="disabled")

        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        summary_tab = ttk.Frame(notebook)
        summary_tab.columnconfigure(0, weight=1)
        summary_tab.rowconfigure(0, weight=1)
        notebook.add(summary_tab, text="Craft")

        self.summary_text = ScrolledText(summary_tab, wrap="word")
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_text.configure(state="disabled")

        ingredient_tab = ttk.Frame(notebook)
        ingredient_tab.columnconfigure(0, weight=1)
        ingredient_tab.rowconfigure(0, weight=1)
        notebook.add(ingredient_tab, text="Ingredients")

        self.ingredient_text = ScrolledText(ingredient_tab, wrap="word")
        self.ingredient_text.grid(row=0, column=0, sticky="nsew")
        self.ingredient_text.configure(state="disabled")

        generator_tab = ttk.Frame(notebook)
        generator_tab.columnconfigure(0, weight=1)
        generator_tab.rowconfigure(1, weight=1)
        generator_tab.rowconfigure(2, weight=1)
        notebook.add(generator_tab, text="Generator")

        generator_header = ttk.Frame(generator_tab)
        generator_header.grid(row=0, column=0, sticky="ew")
        ttk.Label(generator_header, text="Top generated crafts").pack(side=tk.LEFT)
        ttk.Button(
            generator_header,
            text="Apply Selected Option",
            command=self.apply_selected_generated_option,
        ).pack(side=tk.RIGHT)

        self.generated_tree = ttk.Treeview(
            generator_tab,
            columns=("rank", "score", "summary"),
            show="headings",
            height=8,
        )
        self.generated_tree.heading("rank", text="#")
        self.generated_tree.heading("score", text="Objective")
        self.generated_tree.heading("summary", text="Ingredients")
        self.generated_tree.column("rank", width=50, anchor=tk.CENTER)
        self.generated_tree.column("score", width=120, anchor=tk.E)
        self.generated_tree.column("summary", width=620, anchor=tk.W)
        self.generated_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        self.generated_tree.bind("<<TreeviewSelect>>", self._update_generated_details, add="+")
        self.generated_tree.bind("<Double-1>", lambda _event: self.apply_selected_generated_option(), add="+")

        self.generated_details = ScrolledText(generator_tab, wrap="word", height=14)
        self.generated_details.grid(row=2, column=0, sticky="nsew")
        self.generated_details.configure(state="disabled")

    def add_objective_row(self, metric_label: str = "", weight_value: str = "1") -> None:
        row_index = len(self.objective_rows)
        frame = ttk.Frame(self.objectives_container)
        frame.grid(row=row_index, column=0, sticky="ew", pady=2)
        frame.columnconfigure(0, weight=1)

        metric_var = tk.StringVar(value=metric_label)
        weight_var = tk.StringVar(value=weight_value)
        metric_box = SearchableCombobox(
            frame,
            textvariable=metric_var,
            values=METRIC_DISPLAY_OPTIONS,
            width=26,
        )
        metric_box.grid(row=0, column=0, sticky="ew")
        ttk.Entry(frame, textvariable=weight_var, width=8).grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Button(frame, text="Remove", command=lambda: self.remove_objective_row(frame)).grid(
            row=0,
            column=2,
            padx=(6, 0),
        )
        self.objective_rows.append(
            {
                "frame": frame,
                "metric_var": metric_var,
                "weight_var": weight_var,
            }
        )

    def remove_objective_row(self, frame: ttk.Frame) -> None:
        self.objective_rows = [row for row in self.objective_rows if row["frame"] is not frame]
        frame.destroy()
        if not self.objective_rows:
            self.add_objective_row("Health", "1")
            return
        for index, row in enumerate(self.objective_rows):
            row["frame"].grid_configure(row=index)

    def add_constraint_row(
        self,
        metric_label: str = "",
        operator: str = ">=",
        target_value: str = "",
    ) -> None:
        row_index = len(self.constraint_rows)
        frame = ttk.Frame(self.constraints_container)
        frame.grid(row=row_index, column=0, sticky="ew", pady=2)
        frame.columnconfigure(0, weight=1)

        metric_var = tk.StringVar(value=metric_label)
        operator_var = tk.StringVar(value=operator if operator in CONSTRAINT_OPERATORS else ">=")
        target_var = tk.StringVar(value=target_value)

        metric_box = SearchableCombobox(
            frame,
            textvariable=metric_var,
            values=METRIC_DISPLAY_OPTIONS,
            width=28,
        )
        metric_box.grid(row=0, column=0, sticky="ew")
        ttk.Combobox(
            frame,
            textvariable=operator_var,
            values=CONSTRAINT_OPERATORS,
            state="readonly",
            width=4,
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Entry(frame, textvariable=target_var, width=10).grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Button(frame, text="Remove", command=lambda: self.remove_constraint_row(frame)).grid(
            row=0,
            column=3,
            padx=(6, 0),
        )
        self.constraint_rows.append(
            {
                "frame": frame,
                "metric_var": metric_var,
                "operator_var": operator_var,
                "target_var": target_var,
            }
        )

    def remove_constraint_row(self, frame: ttk.Frame) -> None:
        self.constraint_rows = [row for row in self.constraint_rows if row["frame"] is not frame]
        frame.destroy()
        for index, row in enumerate(self.constraint_rows):
            row["frame"].grid_configure(row=index)

    def _collect_objective(self) -> OptimizationObjective | None:
        entries: list[tuple[str, float]] = []
        for row in self.objective_rows:
            metric_text = row["metric_var"].get().strip()
            weight_text = row["weight_var"].get().strip()
            if not metric_text and not weight_text:
                continue
            metric_key = resolve_metric_key(metric_text)
            if metric_key is None:
                self.generator_status_var.set(f"Unknown objective metric: {metric_text}")
                return None
            try:
                weight_value = float(weight_text or "1")
            except ValueError:
                self.generator_status_var.set(f"Invalid objective weight: {weight_text}")
                return None
            if weight_value <= 0.0:
                self.generator_status_var.set("Objective weights must be greater than 0.")
                return None
            entries.append((metric_key, weight_value))

        if not entries:
            return make_optimization_objective((("hp", 1.0),))
        return make_optimization_objective(entries)

    def _collect_generator_inputs(
        self,
    ) -> tuple[OptimizationObjective, list[OptimizationConstraint], str, str, int] | None:
        objective = self._collect_objective()
        if objective is None:
            return None

        constraints: list[OptimizationConstraint] = []
        for row in self.constraint_rows:
            metric_text = row["metric_var"].get().strip()
            operator_text = row["operator_var"].get().strip() or ">="
            target_text = row["target_var"].get().strip()
            if not metric_text and not target_text:
                continue
            metric_key = resolve_metric_key(metric_text)
            if metric_key is None:
                self.generator_status_var.set(f"Unknown constraint metric: {metric_text}")
                return None
            if operator_text not in CONSTRAINT_OPERATORS:
                self.generator_status_var.set(f"Unknown constraint operator: {operator_text}")
                return None
            try:
                target_value = float(target_text or "0")
            except ValueError:
                self.generator_status_var.set(f"Invalid constraint value: {target_text}")
                return None
            constraints.append(OptimizationConstraint(metric_key, operator_text, target_value))

        search_mode = SEARCH_MODE_OPTIONS.get(self.search_mode_var.get())
        if search_mode is None:
            self.generator_status_var.set("Choose a valid search mode.")
            return None

        try:
            top_n = max(1, min(20, int(self.top_n_var.get().strip() or "5")))
        except ValueError:
            self.generator_status_var.set("Top results must be a whole number.")
            return None

        roll_mode = ROLL_MODE_OPTIONS.get(self.roll_mode_var.get(), "average")
        return objective, constraints, roll_mode, search_mode, top_n

    def start_generation(self) -> None:
        if self.optimizer_thread and self.optimizer_thread.is_alive():
            return

        generator_inputs = self._collect_generator_inputs()
        if generator_inputs is None:
            return
        objective, constraints, roll_mode, search_mode, top_n = generator_inputs

        while True:
            try:
                self.optimizer_queue.get_nowait()
            except queue.Empty:
                break

        self.search_stop_event.clear()
        self.generate_button.configure(state=tk.DISABLED)
        self.stop_generation_button.configure(state=tk.NORMAL)
        self.generator_status_var.set(
            f"Running {search_mode.upper()} search for {objective.short_description()}..."
        )

        selection = self._selection_from_controls()

        def progress_callback(options, explored, total_states, elapsed, detail) -> None:
            self.optimizer_queue.put(
                (
                    "progress",
                    options,
                    explored,
                    total_states,
                    elapsed,
                    detail,
                    objective,
                    search_mode,
                )
            )

        def worker() -> None:
            try:
                options = self.optimizer.generate(
                    selection,
                    objective,
                    constraints,
                    roll_mode,
                    search_mode,
                    top_n,
                    stop_event=self.search_stop_event,
                    progress_callback=progress_callback,
                )
            except Exception as exc:
                self.optimizer_queue.put(("error", str(exc)))
                return
            final_status = "stopped" if self.search_stop_event.is_set() else "done"
            self.optimizer_queue.put((final_status, options, objective, search_mode))

        self.optimizer_thread = threading.Thread(target=worker, daemon=True)
        self.optimizer_thread.start()

    def stop_generation(self) -> None:
        self.search_stop_event.set()
        self.stop_generation_button.configure(state=tk.DISABLED)

    def _poll_optimizer_queue(self) -> None:
        while True:
            try:
                message = self.optimizer_queue.get_nowait()
            except queue.Empty:
                break

            status = message[0]
            if status == "progress":
                _status, options, explored, total_states, elapsed, detail, objective, search_mode = message
                self.generated_options = list(options)
                self._update_generated_tree(self.generated_options)
                self.generator_status_var.set(
                    f"{search_mode.upper()} search running: {detail} Current top {len(options)} "
                    f"for {objective.short_description()} after {elapsed:.2f}s."
                )
            elif status == "done":
                _status, options, objective, search_mode = message
                self.generated_options = list(options)
                self._update_generated_tree(self.generated_options)
                self.generate_button.configure(state=tk.NORMAL)
                self.stop_generation_button.configure(state=tk.DISABLED)
                self.generator_status_var.set(
                    f"Found {len(options)} result(s) for {objective.short_description()} with {search_mode.upper()}."
                )
            elif status == "stopped":
                _status, options, objective, search_mode = message
                self.generated_options = list(options)
                self._update_generated_tree(self.generated_options)
                self.generate_button.configure(state=tk.NORMAL)
                self.stop_generation_button.configure(state=tk.DISABLED)
                self.generator_status_var.set(
                    f"Stopped {search_mode.upper()} search with {len(options)} saved result(s)."
                )
            elif status == "error":
                _status, error_text = message
                self.generate_button.configure(state=tk.NORMAL)
                self.stop_generation_button.configure(state=tk.DISABLED)
                self.generator_status_var.set(str(error_text))

        self.after(150, self._poll_optimizer_queue)

    def _update_generated_tree(self, options) -> None:
        previous_selection = self.generated_tree.selection()
        self.generated_tree.delete(*self.generated_tree.get_children())

        for index, option in enumerate(options, start=1):
            ingredients = " | ".join(option.result.selection.ingredient_names)
            self.generated_tree.insert(
                "",
                tk.END,
                iid=str(index - 1),
                values=(index, format_number(option.objective_value), ingredients),
            )

        if previous_selection and previous_selection[0] in self.generated_tree.get_children():
            self.generated_tree.selection_set(previous_selection[0])
            self._update_generated_details()
        else:
            self._set_generated_details("Select a generated craft to inspect it." if options else "No generated crafts yet.")

    def _selected_generated_option(self):
        selection = self.generated_tree.selection()
        if not selection:
            return None
        try:
            index = int(selection[0])
        except ValueError:
            return None
        if 0 <= index < len(self.generated_options):
            return self.generated_options[index]
        return None

    def _update_generated_details(self, _event=None) -> None:
        option = self._selected_generated_option()
        if option is None:
            self._set_generated_details("Select a generated craft to inspect it.")
            return

        result = option.result
        lines = [
            f"{option.objective_label}: {format_number(option.objective_value)}",
            f"Roll Mode: {option.roll_mode.title()}",
            f"Hash: {result.prefixed_hash}",
            "",
            f"Health: {format_number(self.optimizer.metric_value_from_result(result, 'hp', option.roll_mode))}",
            f"Durability: {format_number(self.optimizer.metric_value_from_result(result, 'durability', option.roll_mode))}",
            f"Duration: {format_number(self.optimizer.metric_value_from_result(result, 'duration', option.roll_mode))}",
            f"Charges: {format_number(self.optimizer.metric_value_from_result(result, 'charges', option.roll_mode))}",
            f"Weapon Damage Avg: {format_number(self.optimizer.metric_value_from_result(result, 'weapon_damage_avg', option.roll_mode))}",
            "",
            "Ingredients",
        ]
        for index, ingredient_name in enumerate(result.selection.ingredient_names, start=1):
            lines.append(f"  Slot {index}: {ingredient_name}")

        if not option.objective.is_single_metric():
            lines.extend(["", "Objective Breakdown"])
            for label, weight, raw_value, contribution in self.optimizer.objective_breakdown_from_result(
                result,
                option.objective,
                option.roll_mode,
            ):
                lines.append(
                    f"  {label} x{format_number(weight)}: {format_number(raw_value)} "
                    f"(score {format_number(contribution)})"
                )

        if option.constraint_values:
            lines.extend(["", "Constraints"])
            for label, value in option.constraint_values.items():
                lines.append(f"  {label}: {format_number(value)}")

        self._set_generated_details("\n".join(lines))

    def _set_generated_details(self, text: str) -> None:
        self._set_text(self.generated_details, text)

    def apply_selected_generated_option(self) -> None:
        option = self._selected_generated_option()
        if option is None:
            return
        self._apply_selection(option.result.selection, recalculate=True)
        self.status_var.set("Generated craft applied.")

    def _bind_recipe_widget(self, widget: tk.Misc) -> None:
        if isinstance(widget, SearchableCombobox):
            widget.bind("<<SearchableComboboxSelected>>", self._on_recipe_changed)
            widget.entry.bind("<FocusOut>", self._on_recipe_changed, add="+")
            widget.entry.bind("<KeyRelease>", self._on_recipe_changed, add="+")
            return
        widget.bind("<<ComboboxSelected>>", self._on_recipe_changed)
        widget.bind("<FocusOut>", self._on_recipe_changed)
        widget.bind("<KeyRelease>", self._on_recipe_changed)

    def _on_recipe_changed(self, _event=None) -> None:
        if self._suspend_updates:
            return
        self._update_material_labels()
        self._update_attack_speed_state()
        self._schedule_recalculate()

    def _selection_from_controls(self) -> CraftSelection:
        default = self.data.default_selection()
        recipe_name = self.recipe_var.get().strip() or default.recipe_name
        level_range = self.level_var.get().strip() or default.level_range
        ingredient_names = tuple((var.get().strip() or "No Ingredient") for var in self.ingredient_vars)
        return CraftSelection(
            recipe_name=recipe_name,
            level_range=level_range,
            mat_tiers=(self.mat_vars[0].get() or 3, self.mat_vars[1].get() or 3),
            ingredient_names=ingredient_names,
            attack_speed=self.attack_speed_var.get().strip() or default.attack_speed,
        )

    def _apply_selection(self, selection: CraftSelection, recalculate: bool = True) -> None:
        self._suspend_updates = True
        try:
            self.recipe_var.set(selection.recipe_name)
            self.level_var.set(selection.level_range)
            self.attack_speed_var.set(selection.attack_speed)
            self.mat_vars[0].set(selection.mat_tiers[0])
            self.mat_vars[1].set(selection.mat_tiers[1])
            for idx, ingredient_name in enumerate(selection.ingredient_names):
                self.ingredient_vars[idx].set(ingredient_name)
            self._update_material_labels()
            self._update_attack_speed_state()
        finally:
            self._suspend_updates = False
        if recalculate:
            self._recalculate()

    def _update_material_labels(self) -> None:
        try:
            recipe = self.data.get_recipe(
                self.recipe_var.get().strip() or self.data.default_selection().recipe_name,
                self.level_var.get().strip() or self.data.default_selection().level_range,
            )
        except ValueError:
            self.material_label_vars[0].set("Material 1 Tier")
            self.material_label_vars[1].set("Material 2 Tier")
            return

        self.material_label_vars[0].set(f"{recipe.materials[0].item} Tier")
        self.material_label_vars[1].set(f"{recipe.materials[1].item} Tier")

    def _update_attack_speed_state(self) -> None:
        try:
            recipe = self.data.get_recipe(
                self.recipe_var.get().strip() or self.data.default_selection().recipe_name,
                self.level_var.get().strip() or self.data.default_selection().level_range,
            )
        except ValueError:
            state = "normal"
        else:
            state = "normal" if recipe.type_key in WEAPON_TYPES else "disabled"
        for button in self.attack_speed_buttons:
            button.configure(state=state)

    def _schedule_recalculate(self, _event=None) -> None:
        if self._suspend_updates:
            return
        if self.pending_recalc is not None:
            self.after_cancel(self.pending_recalc)
        self.pending_recalc = self.after(150, self._recalculate)

    def _recalculate(self) -> None:
        self.pending_recalc = None
        try:
            result = self.data.craft(self._selection_from_controls())
        except Exception as exc:
            self.status_var.set(str(exc))
            return

        self.current_result = result
        self._set_text(self.warning_text, format_warnings(result))
        summary = f"{format_recipe_summary(result)}\n\n{format_craft_summary(result)}"
        self._set_text(self.summary_text, summary)
        self._set_text(self.ingredient_text, format_ingredient_summary(result))

        self._suspend_updates = True
        try:
            self.hash_var.set(result.prefixed_hash)
        finally:
            self._suspend_updates = False
        self.status_var.set("Craft updated.")

    def _set_text(self, widget: ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _load_hash(self, _event=None):
        try:
            selection = self.data.decode_hash_to_selection(self.hash_var.get())
        except Exception as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("Invalid hash", str(exc), parent=self)
            return "break"
        self._apply_selection(selection, recalculate=True)
        self.status_var.set("Hash loaded.")
        return "break"

    def _reset(self) -> None:
        self.hash_var.set("")
        self._apply_selection(self.data.default_selection(), recalculate=True)
        self.status_var.set("Reset to defaults.")

    def _copy_text(self, text: str, message: str) -> None:
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_var.set(message)

    def _copy_hash(self) -> None:
        if self.current_result is None:
            return
        self._copy_text(self.current_result.prefixed_hash, "Hash copied.")

    def _copy_short(self) -> None:
        if self.current_result is None:
            return
        self._copy_text(build_copy_short(self.current_result), "Short share text copied.")

    def _copy_long(self) -> None:
        if self.current_result is None:
            return
        self._copy_text(build_copy_long(self.current_result), "Long share text copied.")


def run_self_test() -> None:
    data = CrafterData.load()
    optimizer = CrafterOptimizer(data)

    default_result = data.craft(data.default_selection())
    decoded_default = data.decode_hash_to_selection(default_result.prefixed_hash)
    assert decoded_default.recipe_name == default_result.selection.recipe_name
    assert decoded_default.level_range == default_result.selection.level_range
    assert decoded_default.mat_tiers == default_result.selection.mat_tiers
    assert decoded_default.ingredient_names == default_result.selection.ingredient_names

    weapon_selection = CraftSelection(
        recipe_name="Bow",
        level_range="103-105",
        mat_tiers=(3, 3),
        ingredient_names=(
            "Earth Powder VI",
            "No Ingredient",
            "No Ingredient",
            "No Ingredient",
            "No Ingredient",
            "No Ingredient",
        ),
        attack_speed="FAST",
    )
    weapon_result = data.craft(weapon_selection)
    decoded_weapon = data.decode_hash_to_selection(weapon_result.prefixed_hash)
    assert decoded_weapon == weapon_result.selection

    search_selection = CraftSelection(
        recipe_name="Bow",
        level_range="103-105",
        mat_tiers=(3, 3),
        ingredient_names=(
            "Earth Powder VI",
            "Thunder Powder VI",
            "Thunder Powder VI",
            "Thunder Powder VI",
            "No Ingredient",
            "No Ingredient",
        ),
        attack_speed="FAST",
    )
    objective = make_optimization_objective((("weapon_damage_avg", 1.0),))
    exact_options = optimizer.generate(search_selection, objective, [], "average", "exact", 2)
    mcts_options = optimizer.generate(search_selection, objective, [], "average", "mcts", 2)
    assert exact_options
    assert mcts_options
    assert all(not option.result.warnings for option in exact_options)
    assert all(not option.result.warnings for option in mcts_options)

    armor_selection = CraftSelection(
        recipe_name="Chestplate",
        level_range="103-105",
        mat_tiers=(3, 3),
        ingredient_names=("No Ingredient",) * 6,
        attack_speed="NORMAL",
    )
    armor_objective = make_optimization_objective((("gXp", 1.0),))
    armor_constraints = [OptimizationConstraint("durability", ">", 100.0)]
    armor_exact_options = optimizer.generate(
        armor_selection,
        armor_objective,
        armor_constraints,
        "best",
        "exact",
        3,
    )
    assert armor_exact_options
    assert armor_exact_options[0].objective_value >= 28.0
    assert optimizer.metric_value_from_result(armor_exact_options[0].result, "durability", "best") > 100.0
    assert all(not option.result.warnings for option in armor_exact_options)

    print("Loaded recipes:", len(data.recipes))
    print("Loaded ingredients:", len(data.ingredients))
    print("Default hash:", default_result.prefixed_hash)
    print("Weapon hash:", weapon_result.prefixed_hash)
    print("Exact best:", exact_options[0].result.prefixed_hash)
    print("MCTS best:", mcts_options[0].result.prefixed_hash)
    print("Armor exact best:", armor_exact_options[0].result.prefixed_hash)
    print("Self-test passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Python reimplementation of WynnCrafter.")
    parser.add_argument("--self-test", action="store_true", help="Run a headless smoke test and exit.")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    data = CrafterData.load()
    app = WynnCrafterApp(data)
    app.mainloop()


if __name__ == "__main__":
    main()
