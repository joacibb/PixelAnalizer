"""
toolbar.py
----------
Toolbar widget with all action buttons.
Now includes ROI selection and Inspection tools.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable


class Toolbar(tk.Frame):
    """Top button bar for PixelAnalizer.

    Parameters
    ----------
    parent:
        Parent Tkinter widget.
    on_load:
        Callback for "Cargar Imagen".
    on_calculate:
        Callback for "Calcular Porcentajes".
    on_show_color:
        Callback for "Mostrar Rojos".
    on_reset:
        Callback for "Restablecer".
    on_export_csv:
        Callback for "Exportar CSV".
    on_export_json:
        Callback for "Exportar JSON".
    on_set_mode:
        Callback for switching interaction mode (ROI, Inspect, etc).
    """

    _BTN_STYLE = {
        "relief": tk.FLAT,
        "padx": 10,
        "pady": 6,
        "cursor": "hand2",
        "bd": 0,
        "activeforeground": "#ffffff",
    }

    def __init__(
        self,
        parent: tk.Widget,
        on_load: Callable,
        on_calculate: Callable,
        on_show_color: Callable,
        on_reset: Callable,
        on_export_csv: Callable,
        on_export_json: Callable,
        on_set_mode: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, bg="#181825", pady=4, **kwargs)

        label_font = tkfont.Font(family="Helvetica", size=9, weight="bold")
        self._on_set_mode = on_set_mode

        # --- Primary Actions ---
        primary_fr = tk.Frame(self, bg="#181825")
        primary_fr.pack(side=tk.LEFT, padx=5)

        self.load_btn = self._make_btn(primary_fr, "📂  Cargar", "#313244", "#45475a", on_load, label_font)
        self.calc_btn = self._make_btn(primary_fr, "📊  Calcular", "#1e66f5", "#1558d6", on_calculate, label_font)

        # --- Tools (Toggle-like behavior) ---
        tools_fr = tk.Frame(self, bg="#181825")
        tools_fr.pack(side=tk.LEFT, padx=15)

        self.roi_btn = self._make_btn(tools_fr, "📐  Área (ROI)", "#45475a", "#585b70", 
                                      lambda: self._toggle_mode("ROI"), label_font)
        self.inspect_btn = self._make_btn(tools_fr, "🔍  Inspeccionar", "#45475a", "#585b70", 
                                         lambda: self._toggle_mode("INSPECT"), label_font)
        
        # --- Visualization ---
        viz_fr = tk.Frame(self, bg="#181825")
        viz_fr.pack(side=tk.LEFT, padx=5)
        
        self.veg_btn = self._make_btn(viz_fr, "🌿  Ver Vegetación", "#40a02b", "#369023", on_show_color, label_font)
        self.reset_btn = self._make_btn(viz_fr, "🔄  Restablecer", "#40a02b", "#369023", on_reset, label_font)

        # --- Export ---
        export_fr = tk.Frame(self, bg="#181825")
        export_fr.pack(side=tk.LEFT, padx=15)
        
        self.csv_btn = self._make_btn(export_fr, "💾  CSV", "#8839ef", "#7527d8", on_export_csv, label_font)
        self.json_btn = self._make_btn(export_fr, "📄  JSON", "#df8e1d", "#c47a0f", on_export_json, label_font)

        self._action_buttons = [
            self.calc_btn, self.roi_btn, self.inspect_btn, 
            self.veg_btn, self.reset_btn, self.csv_btn, self.json_btn
        ]

        # Status label
        self._status_label = tk.Label(
            self, text="", fg="#6c7086", bg="#181825",
            font=tkfont.Font(family="Helvetica", size=9)
        )
        self._status_label.pack(side=tk.RIGHT, padx=12)

        self._active_mode = "PAN"
        self.set_image_loaded(False)

    def _make_btn(self, parent, text, bg, abg, cmd, font):
        btn = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#cdd6f4",
                        activebackground=abg, font=font, **self._BTN_STYLE)
        btn.pack(side=tk.LEFT, padx=2)
        return btn

    def _toggle_mode(self, mode: str):
        if self._active_mode == mode:
            self._active_mode = "PAN"
        else:
            self._active_mode = mode
            
        # Update colors to show which one is active
        self.roi_btn.config(bg="#1e66f5" if self._active_mode == "ROI" else "#45475a")
        self.inspect_btn.config(bg="#1e66f5" if self._active_mode == "INSPECT" else "#45475a")
        
        self._on_set_mode(self._active_mode)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_image_loaded(self, loaded: bool) -> None:
        state = tk.NORMAL if loaded else tk.DISABLED
        for btn in self._action_buttons:
            btn.config(state=state)
        if not loaded:
            self._active_mode = "PAN"
            self.roi_btn.config(bg="#45475a")
            self.inspect_btn.config(bg="#45475a")

    def set_status(self, message: str, color: str = "#6c7086") -> None:
        self._status_label.config(text=message, fg=color)
        self.update_idletasks()
