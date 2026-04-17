import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from repository_sqlserver import RepositorySqlServer
from service_dimensionnement import ServiceDimensionnement


class ApplicationTk(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Panneau Solaire Pro")
        self.geometry("1280x820")
        self.minsize(1180, 760)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.configure(fg_color="#F0F2F5")
        self._configure_ttk_styles()

        self.repository = RepositorySqlServer()
        self.service = ServiceDimensionnement()

        self.simulation_active_id: int | None = None
        self.map_simulations: dict[str, int] = {}
        self.map_tranches: dict[str, int] = {}
        self.tranches_disponibles: list[str] = ["MATIN", "SOIR", "NUIT"]

        self.entree_en_edition_id: int | None = None
        self.result_labels: dict[str, ctk.CTkLabel] = {}

        self._build_ui()
        self._connect_db()

    def _configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dashboard.Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#1F2937",
            borderwidth=0,
            rowheight=38,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            background="#E5EAF2",
            foreground="#1F2937",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=(8, 10),
        )
        style.map(
            "Dashboard.Treeview",
            background=[("selected", "#D1FAE5")],
            foreground=[("selected", "#065F46")],
        )

        style.configure(
            "Sidebar.TCombobox",
            fieldbackground="#111827",
            background="#111827",
            foreground="#E5E7EB",
            arrowcolor="#10B981",
            bordercolor="#374151",
            lightcolor="#374151",
            darkcolor="#374151",
            borderwidth=1,
            padding=6,
            font=("Segoe UI", 10),
        )
        style.map(
            "Sidebar.TCombobox",
            fieldbackground=[("readonly", "#111827")],
            foreground=[("readonly", "#E5E7EB")],
        )

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color="#111827")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="#F0F2F5")
        self.main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self._build_sidebar()
        self._build_main_content()

    def _build_sidebar(self):
        ctk.CTkLabel(
            self.sidebar,
            text="Panneau Solaire",
            font=("Segoe UI Semibold", 30),
            text_color="#F9FAFB",
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            self.sidebar,
            text="Energy sizing workspace",
            font=("Segoe UI", 12),
            text_color="#9CA3AF",
        ).pack(anchor="w", padx=24, pady=(0, 20))

        sim_card = ctk.CTkFrame(self.sidebar, fg_color="#1F2937", corner_radius=16)
        sim_card.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(sim_card, text="Simulation active", text_color="#D1D5DB", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=14, pady=(14, 6)
        )

        self.cmb_simulations = ttk.Combobox(sim_card, width=29, state="readonly", style="Sidebar.TCombobox")
        self.cmb_simulations.pack(fill="x", padx=14, pady=(0, 12))
        self.cmb_simulations.bind("<<ComboboxSelected>>", self.selectionner_simulation)

        ctk.CTkButton(
            sim_card,
            text="Supprimer simulation",
            command=self.supprimer_simulation,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F3F4F6",
            corner_radius=12,
            height=36,
        ).pack(fill="x", padx=14, pady=(0, 14))

        new_card = ctk.CTkFrame(self.sidebar, fg_color="#1F2937", corner_radius=16)
        new_card.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(new_card, text="Nouvelle simulation", text_color="#D1D5DB", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=14, pady=(14, 6)
        )

        self.var_titre_simulation = tk.StringVar()
        self.var_notes_simulation = tk.StringVar()

        self.ent_titre_simulation = ctk.CTkEntry(
            new_card,
            textvariable=self.var_titre_simulation,
            placeholder_text="Ex: Maison familiale",
            fg_color="#111827",
            border_color="#374151",
            text_color="#F9FAFB",
            corner_radius=10,
            height=36,
        )
        self.ent_titre_simulation.pack(fill="x", padx=14, pady=(0, 10))

        self.ent_notes_simulation = ctk.CTkEntry(
            new_card,
            textvariable=self.var_notes_simulation,
            placeholder_text="Notes (optionnel)",
            fg_color="#111827",
            border_color="#374151",
            text_color="#F9FAFB",
            corner_radius=10,
            height=36,
        )
        self.ent_notes_simulation.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkButton(
            new_card,
            text="+ Creer",
            command=self.creer_simulation,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#F9FAFB",
            corner_radius=12,
            height=38,
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x", padx=14, pady=(0, 14))

    def _build_main_content(self):
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Tableau de bord",
            font=("Segoe UI Semibold", 28),
            text_color="#1F2937",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=datetime.now().strftime("%d/%m/%Y"),
            font=("Segoe UI", 12),
            text_color="#6B7280",
        ).grid(row=0, column=1, sticky="e")

        self.kpi_row = ctk.CTkFrame(self.main, fg_color="transparent")
        self.kpi_row.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        for i in range(4):
            self.kpi_row.grid_columnconfigure(i, weight=1)

        self.kpi_labels: dict[str, ctk.CTkLabel] = {}
        self._create_kpi_card(0, "Puissance totale", "kpi_puissance_totale", "0.00 W")
        self._create_kpi_card(1, "Appareils", "kpi_nb_appareils", "0")
        self._create_kpi_card(2, "Energie totale", "kpi_energie_totale", "0.00 Wh")
        self._create_kpi_card(3, "Autonomie estimee", "kpi_autonomie", "0.00 h")

        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._build_form_card(content)
        self._build_table_card(content)
        self._build_results_panel(content)

    def _create_kpi_card(self, column: int, title: str, key: str, default_value: str):
        card = ctk.CTkFrame(self.kpi_row, fg_color="#FFFFFF", corner_radius=16)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 8 if column < 3 else 0), pady=0)

        ctk.CTkLabel(card, text=title, text_color="#6B7280", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=14, pady=(10, 4)
        )
        value = ctk.CTkLabel(card, text=default_value, text_color="#1F2937", font=("Segoe UI Semibold", 22))
        value.pack(anchor="w", padx=14, pady=(0, 12))
        self.kpi_labels[key] = value

    def _build_form_card(self, parent: ctk.CTkFrame):
        form_card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        form_card.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        for i in range(5):
            form_card.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(
            form_card,
            text="Ajouter une charge",
            font=("Segoe UI", 18, "bold"),
            text_color="#1F2937",
        ).grid(row=0, column=0, columnspan=5, sticky="w", padx=16, pady=(14, 10))

        self.var_materiel = tk.StringVar()
        self.var_puissance = tk.StringVar()
        self.var_tranche = tk.StringVar(value="MATIN")
        self.var_duree = tk.StringVar()

        self.ent_materiel = self._labeled_entry(
            form_card,
            "Materiel",
            self.var_materiel,
            "Ex: Refrigerateur",
            row=1,
            col=0,
        )
        self.ent_puissance = self._labeled_entry(
            form_card,
            "Puissance (W)",
            self.var_puissance,
            "Ex: 120",
            row=1,
            col=1,
        )
        self.cmb_tranches = self._labeled_option_menu(
            form_card,
            "Tranche",
            self.var_tranche,
            self.tranches_disponibles,
            row=1,
            col=2,
        )
        self.ent_duree = self._labeled_entry(
            form_card,
            "Duree (h)",
            self.var_duree,
            "Ex: 8",
            row=1,
            col=3,
        )

        self.btn_ajouter = ctk.CTkButton(
            form_card,
            text="+ Ajouter",
            command=self.ajouter_entree,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            corner_radius=12,
            height=38,
            font=("Segoe UI", 11, "bold"),
        )
        self.btn_ajouter.grid(row=2, column=0, padx=16, pady=(8, 14), sticky="w")

        ctk.CTkButton(
            form_card,
            text="Modifier",
            command=self.modifier_entree,
            fg_color="#E5E7EB",
            hover_color="#D1D5DB",
            text_color="#1F2937",
            corner_radius=12,
            height=38,
        ).grid(row=2, column=1, padx=8, pady=(8, 14), sticky="ew")

        ctk.CTkButton(
            form_card,
            text="Annuler",
            command=self.annuler_edition,
            fg_color="#F3F4F6",
            hover_color="#E5E7EB",
            text_color="#374151",
            corner_radius=12,
            height=38,
        ).grid(row=2, column=2, padx=8, pady=(8, 14), sticky="ew")

    def _labeled_entry(self, parent, label, variable, placeholder, row, col):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, padx=8, pady=(0, 8), sticky="ew")
        wrap.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrap, text=label, text_color="#4B5563", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        entry = ctk.CTkEntry(
            wrap,
            textvariable=variable,
            placeholder_text=placeholder,
            fg_color="#F9FAFB",
            border_color="#D1D5DB",
            text_color="#1F2937",
            corner_radius=10,
            height=36,
        )
        entry.grid(row=1, column=0, sticky="ew")
        return entry

    def _labeled_option_menu(self, parent, label, variable, values, row, col):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, padx=8, pady=(0, 8), sticky="ew")
        wrap.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrap, text=label, text_color="#4B5563", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        option = ctk.CTkOptionMenu(
            wrap,
            variable=variable,
            values=values,
            fg_color="#F9FAFB",
            button_color="#10B981",
            button_hover_color="#059669",
            text_color="#1F2937",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#1F2937",
            dropdown_hover_color="#E5E7EB",
            corner_radius=10,
            height=36,
        )
        option.grid(row=1, column=0, sticky="ew")
        return option

    def _build_table_card(self, parent: ctk.CTkFrame):
        table_card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        table_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 0))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            table_card,
            text="Entrees de consommation",
            font=("Segoe UI", 18, "bold"),
            text_color="#1F2937",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        table_holder = tk.Frame(table_card, bg="#FFFFFF")
        table_holder.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.tree_entrees = ttk.Treeview(
            table_holder,
            columns=("id", "materiel", "puissance_w", "tranche", "duree_h", "action"),
            show="headings",
            style="Dashboard.Treeview",
            height=14,
        )

        columns = [
            ("id", "ID", 70),
            ("materiel", "Materiel", 260),
            ("puissance_w", "Puissance (W)", 130),
            ("tranche", "Tranche", 110),
            ("duree_h", "Duree (h)", 110),
            ("action", "Action", 90),
        ]
        for col, title, width in columns:
            self.tree_entrees.heading(col, text=title)
            self.tree_entrees.column(col, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(table_holder, orient="vertical", command=self.tree_entrees.yview)
        self.tree_entrees.configure(yscrollcommand=scrollbar.set)

        self.tree_entrees.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree_entrees.bind("<Double-1>", self.charger_pour_edition)
        self.tree_entrees.bind("<Button-1>", self._on_tree_click)

    def _build_results_panel(self, parent: ctk.CTkFrame):
        right = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="Resultats",
            font=("Segoe UI", 18, "bold"),
            text_color="#1F2937",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        ctk.CTkButton(
            right,
            text="Calculer",
            command=self.calculer,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            corner_radius=12,
            height=38,
            font=("Segoe UI", 11, "bold"),
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        metrics = ctk.CTkFrame(right, fg_color="#F9FAFB", corner_radius=12)
        metrics.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        metrics.grid_columnconfigure(0, weight=1)
        metrics.grid_columnconfigure(1, weight=1)

        self._result_line(metrics, "Energie MATIN", "energie_matin_wh", "Wh", 0, 0)
        self._result_line(metrics, "Energie SOIR", "energie_soir_wh", "Wh", 1, 0)
        self._result_line(metrics, "Energie NUIT", "energie_nuit_wh", "Wh", 2, 0)
        self._result_line(metrics, "Puissance MATIN", "puissance_matin_w", "W", 0, 1)
        self._result_line(metrics, "Puissance SOIR", "puissance_soir_w", "W", 1, 1)
        self._result_line(metrics, "Puissance NUIT", "puissance_nuit_w", "W", 2, 1)
        self._result_line(metrics, "Batterie theorique", "batterie_theorique_wh", "Wh", 3, 0)
        self._result_line(metrics, "Charge batterie", "puissance_charge_batterie_w", "W", 4, 0)
        self._result_line(metrics, "Panneau theorique", "panneau_theorique_w", "W", 3, 1)

        sizing = ctk.CTkFrame(right, fg_color="#ECFDF5", corner_radius=12)
        sizing.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
        sizing.grid_columnconfigure(0, weight=1)

        self._result_block(sizing, "Panneau a acheter", "panneau_pratique_kw", "kW", 0)
        self._result_block(sizing, "Batterie a acheter", "batterie_pratique_kwh", "kWh", 1)

        chart_card = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=12)
        chart_card.grid(row=4, column=0, sticky="nsew", padx=14, pady=(0, 14))
        chart_card.grid_columnconfigure(0, weight=1)
        chart_card.grid_rowconfigure(1, weight=1)
        right.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(chart_card, text="Consommation par tranche", text_color="#1F2937", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 0)
        )

        self.figure = Figure(figsize=(4.2, 2.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_card)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._update_chart(0.0, 0.0, 0.0)

    def _result_line(self, parent, label, key, unit, row, col):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=8)
        wrap.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrap, text=label, text_color="#6B7280", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        value = ctk.CTkLabel(wrap, text="0.00", text_color="#1F2937", font=("Segoe UI Semibold", 16))
        value.grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(wrap, text=unit, text_color="#9CA3AF", font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=(6, 0))
        self.result_labels[key] = value

    def _result_block(self, parent, title, key, unit, row):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        wrap.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrap, text=title, text_color="#047857", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        value = ctk.CTkLabel(wrap, text="0.000", text_color="#065F46", font=("Segoe UI Semibold", 24))
        value.grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(wrap, text=unit, text_color="#047857", font=("Segoe UI", 12)).grid(row=1, column=1, sticky="w", padx=(6, 0))
        self.result_labels[key] = value

    def _connect_db(self):
        try:
            self.repository.connecter()
            self._charger_tranches()
            self.rafraichir_simulations()
        except Exception as exc:
            messagebox.showerror(
                "Base de donnees",
                "Connexion impossible. Cree manuellement la base et les tables puis relance l'application.\n\n"
                f"Detail: {exc}",
            )

    def _charger_tranches(self):
        tranches = self.repository.lister_tranches()
        if tranches:
            self.map_tranches = {libelle: tranche_id for tranche_id, libelle in tranches}
            self.tranches_disponibles = [libelle for _id, libelle in tranches]
            self.cmb_tranches.configure(values=self.tranches_disponibles)
            self.var_tranche.set(self.tranches_disponibles[0])

    def rafraichir_simulations(self):
        self.map_simulations.clear()
        rows = self.repository.lister_simulations()

        labels = []
        for sim in rows:
            label = f"{sim.id} - {sim.titre}"
            labels.append(label)
            self.map_simulations[label] = sim.id

        self.cmb_simulations["values"] = labels
        if labels:
            self.cmb_simulations.current(0)
            self.selectionner_simulation()
        else:
            self.simulation_active_id = None
            self.tree_entrees.delete(*self.tree_entrees.get_children())
            self._reset_result_values()
            self._update_kpis()

    def creer_simulation(self):
        try:
            titre = self.var_titre_simulation.get().strip()
            notes = self.var_notes_simulation.get().strip() or None
            if not titre:
                self.ent_titre_simulation.configure(border_color="#EF4444")
                return

            self.ent_titre_simulation.configure(border_color="#374151")
            self.repository.creer_simulation(titre, notes)
            self.var_titre_simulation.set("")
            self.var_notes_simulation.set("")
            self.rafraichir_simulations()
        except Exception as exc:
            messagebox.showerror("Simulation", str(exc))

    def supprimer_simulation(self):
        try:
            if self.simulation_active_id is None:
                return
            self.repository.supprimer_simulation(self.simulation_active_id)
            self.simulation_active_id = None
            self.tree_entrees.delete(*self.tree_entrees.get_children())
            self.rafraichir_simulations()
            self._reset_result_values()
            self._update_kpis()
        except Exception as exc:
            messagebox.showerror("Simulation", str(exc))

    def selectionner_simulation(self, _event=None):
        label = self.cmb_simulations.get().strip()
        self.simulation_active_id = self.map_simulations.get(label)
        self.rafraichir_entrees()

    def rafraichir_entrees(self):
        self.tree_entrees.delete(*self.tree_entrees.get_children())
        if self.simulation_active_id is None:
            self._update_kpis()
            return

        for entree in self.repository.lister_entrees(self.simulation_active_id):
            self.tree_entrees.insert(
                "",
                "end",
                values=(
                    entree.id,
                    entree.materiel,
                    f"{entree.puissance_w:.2f}",
                    entree.tranche,
                    f"{entree.duree_h:.2f}",
                    "Suppr",
                ),
            )
        self._update_kpis()

    def _on_tree_click(self, event):
        region = self.tree_entrees.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree_entrees.identify_column(event.x)
        if column != "#6":
            return

        item = self.tree_entrees.identify_row(event.y)
        if not item:
            return

        self.tree_entrees.selection_set(item)
        self.supprimer_entree()

    def charger_pour_edition(self, _event):
        selection = self.tree_entrees.selection()
        if not selection:
            return
        values = self.tree_entrees.item(selection[0])["values"]
        self.entree_en_edition_id = int(values[0])
        self.var_materiel.set(values[1])
        self.var_puissance.set(values[2])
        self.var_tranche.set(values[3])
        self.var_duree.set(values[4])
        self.btn_ajouter.configure(text="Mettre a jour")

    def annuler_edition(self):
        self.entree_en_edition_id = None
        self.var_materiel.set("")
        self.var_puissance.set("")
        self.var_tranche.set(self.tranches_disponibles[0] if self.tranches_disponibles else "MATIN")
        self.var_duree.set("")
        self.btn_ajouter.configure(text="+ Ajouter")
        self._clear_field_highlights()
        selection = self.tree_entrees.selection()
        if selection:
            self.tree_entrees.selection_remove(selection)

    def _clear_field_highlights(self):
        self.ent_materiel.configure(border_color="#D1D5DB")
        self.ent_puissance.configure(border_color="#D1D5DB")
        self.ent_duree.configure(border_color="#D1D5DB")

    def _validate_input_fields(self) -> bool:
        self._clear_field_highlights()
        ok = True

        if not self.var_materiel.get().strip():
            self.ent_materiel.configure(border_color="#EF4444")
            ok = False

        try:
            if float(self.var_puissance.get()) <= 0:
                raise ValueError
        except Exception:
            self.ent_puissance.configure(border_color="#EF4444")
            ok = False

        try:
            if float(self.var_duree.get()) <= 0:
                raise ValueError
        except Exception:
            self.ent_duree.configure(border_color="#EF4444")
            ok = False

        return ok

    def ajouter_entree(self):
        try:
            if self.simulation_active_id is None:
                raise ValueError("Selectionnez d'abord une simulation")

            if not self._validate_input_fields():
                return

            materiel = self.var_materiel.get().strip()
            puissance_w = float(self.var_puissance.get())
            tranche = self.var_tranche.get().strip().upper()
            duree_h = float(self.var_duree.get())

            if tranche not in self.map_tranches:
                raise ValueError("Tranche invalide")

            if self.entree_en_edition_id:
                self.repository.modifier_entree(
                    entree_id=self.entree_en_edition_id,
                    materiel=materiel,
                    puissance_w=puissance_w,
                    id_tranche_heure=self.map_tranches[tranche],
                    duree_h=duree_h,
                )
                self.annuler_edition()
            else:
                self.repository.ajouter_entree(
                    simulation_id=self.simulation_active_id,
                    materiel=materiel,
                    puissance_w=puissance_w,
                    id_tranche_heure=self.map_tranches[tranche],
                    duree_h=duree_h,
                )
                self.var_materiel.set("")
                self.var_puissance.set("")
                self.var_duree.set("")

            self.rafraichir_entrees()
        except ValueError as exc:
            messagebox.showerror("Entree", str(exc))
        except Exception as exc:
            messagebox.showerror("Entree", str(exc))

    def modifier_entree(self):
        if self.entree_en_edition_id:
            self.ajouter_entree()
        else:
            messagebox.showinfo("Modification", "Double-cliquez sur une entree pour l'editer")

    def supprimer_entree(self):
        try:
            selection = self.tree_entrees.selection()
            if not selection:
                return
            entree_id = int(self.tree_entrees.item(selection[0])["values"][0])
            self.repository.supprimer_entree(entree_id)
            self.rafraichir_entrees()
            self.annuler_edition()
        except Exception as exc:
            messagebox.showerror("Entree", str(exc))

    def _set_result_value(self, key: str, value: float, decimals: int = 2):
        if key in self.result_labels:
            self.result_labels[key].configure(text=f"{value:.{decimals}f}")

    def _reset_result_values(self):
        for key, label in self.result_labels.items():
            label.configure(text="0.000" if key.endswith("kw") or key.endswith("kwh") else "0.00")
        self._update_chart(0.0, 0.0, 0.0)

    def _update_kpis(self):
        rows = self.tree_entrees.get_children()
        nb = len(rows)

        total_power = 0.0
        total_energy = 0.0
        for row in rows:
            values = self.tree_entrees.item(row)["values"]
            puissance = float(values[2])
            duree = float(values[4])
            total_power += puissance
            total_energy += puissance * duree

        autonomie = (total_energy / total_power) if total_power > 0 else 0.0

        self.kpi_labels["kpi_puissance_totale"].configure(text=f"{total_power:.2f} W")
        self.kpi_labels["kpi_nb_appareils"].configure(text=f"{nb}")
        self.kpi_labels["kpi_energie_totale"].configure(text=f"{total_energy:.2f} Wh")
        self.kpi_labels["kpi_autonomie"].configure(text=f"{autonomie:.2f} h")

    def _update_chart(self, matin: float, soir: float, nuit: float):
        self.ax.clear()
        labels = ["Matin", "Soir", "Nuit"]
        values = [matin, soir, nuit]
        colors = ["#F59E0B", "#10B981", "#3B82F6"]

        self.ax.bar(labels, values, color=colors, width=0.55)
        self.ax.set_facecolor("#FFFFFF")
        self.figure.patch.set_facecolor("#FFFFFF")
        self.ax.tick_params(axis="x", colors="#374151")
        self.ax.tick_params(axis="y", colors="#6B7280")
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color("#D1D5DB")
        self.ax.spines["bottom"].set_color("#D1D5DB")
        self.ax.set_ylabel("Wh", color="#6B7280")
        self.canvas.draw_idle()

    def calculer(self):
        try:
            if self.simulation_active_id is None:
                raise ValueError("Selectionnez d'abord une simulation")

            entrees = self.repository.lister_entrees(self.simulation_active_id)
            parametres = self.repository.charger_parametres()
            resultat = self.service.calculer(entrees, parametres)

            self._set_result_value("energie_matin_wh", resultat.energie_matin_wh)
            self._set_result_value("energie_soir_wh", resultat.energie_soir_wh)
            self._set_result_value("energie_nuit_wh", resultat.energie_nuit_wh)

            self._set_result_value("puissance_matin_w", resultat.puissance_matin_w)
            self._set_result_value("puissance_soir_w", resultat.puissance_soir_w)
            self._set_result_value("puissance_nuit_w", resultat.puissance_nuit_w)

            self._set_result_value("batterie_theorique_wh", resultat.batterie_theorique_wh)
            self._set_result_value("puissance_charge_batterie_w", resultat.puissance_charge_batterie_w)
            self._set_result_value("panneau_theorique_w", resultat.panneau_theorique_w)

            self._set_result_value("panneau_pratique_kw", resultat.panneau_pratique_achat_w / 1000.0, 3)
            self._set_result_value("batterie_pratique_kwh", resultat.batterie_pratique_achat_wh / 1000.0, 3)

            self._update_chart(
                resultat.energie_matin_wh,
                resultat.energie_soir_wh,
                resultat.energie_nuit_wh,
            )
            self._update_kpis()
        except Exception as exc:
            messagebox.showerror("Calcul", str(exc))
