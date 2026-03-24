"""
results_panel.py
----------------
Displays per-color percentage results. Updated for granular land cover classes.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Optional, Callable

from src.core.analyzer import AnalysisResult

# Color → hex badge colour mapping for granular labels
COLOR_BADGES: dict[str, str] = {
    "Vegetación Densa":           "#1b4332", # Dark Green
    "Vegetación Media":           "#2d6a4f", # Green
    "Vegetación Escasa / Seca":   "#95d5b2", # Light Green
    "Suelo Árido / Arena":        "#f4a261", # Orange/Sandy
    "Agua / Azul":                 "#0077b6", # Blue
    "Nubes / Nieve":              "#ffffff", # White
}


class ResultsPanel(tk.Frame):
    """Bottom panel showing analysis results with coloured badges."""

    def __init__(self, parent: tk.Widget, on_class_click: Optional[Callable[[str], None]] = None, **kwargs) -> None:
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self._result: Optional[AnalysisResult] = None
        self._on_class_click = on_class_click
        self._build_layout()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_result(self, result: AnalysisResult) -> None:
        """Render *result* into the panel."""
        self._result = result
        self._clear_rows()
        roi_txt = f" ROI: {result.roi}" if result.roi else " (Imagen Completa)"
        self._image_label.config(
            text=f"📄 {result.image_name or 'Sin nombre'}{roi_txt} — "
                 f"{result.non_black_pixels:,} px analizados"
        )
        # Sort by percentage descending
        sorted_pct = sorted(result.percentages.items(), key=lambda x: x[1], reverse=True)
        for label, pct in sorted_pct:
            if pct > 0: # Only show classes that are present
                self._add_row(label, pct)

    def clear(self) -> None:
        self._clear_rows()
        self._image_label.config(text="Sin resultados. Cargá una imagen y calculá.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        bold = tkfont.Font(family="Helvetica", size=10, weight="bold")

        header = tk.Frame(self, bg="#1e1e2e", pady=4)
        header.pack(fill=tk.X, padx=10)

        tk.Label(
            header, text="📊 Análisis de Cobertura", fg="#cdd6f4",
            bg="#1e1e2e", font=bold
        ).pack(side=tk.LEFT)

        self._image_label = tk.Label(
            header, text="Sin resultados. Cargá una imagen y calculá.",
            fg="#6c7086", bg="#1e1e2e", font=tkfont.Font(family="Helvetica", size=9),
        )
        self._image_label.pack(side=tk.LEFT, padx=16)

        # Container for the rows (using a child frame to handle overflow if many classes)
        self._rows_frame = tk.Frame(self, bg="#1e1e2e")
        self._rows_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

    def _clear_rows(self) -> None:
        for widget in self._rows_frame.winfo_children():
            widget.destroy()

    def _add_row(self, label: str, percentage: float) -> None:
        badge_color = COLOR_BADGES.get(label, "#89b4fa")
        
        row = tk.Frame(self._rows_frame, bg="#1e1e2e", cursor="hand2")
        row.pack(side=tk.LEFT, padx=10)

        def on_click(_e):
            if self._on_class_click:
                self._on_class_click(label)

        dot = tk.Label(row, text="●", fg=badge_color, bg="#1e1e2e",
                       font=tkfont.Font(size=12), cursor="hand2")
        dot.pack(side=tk.LEFT)

        info_fr = tk.Frame(row, bg="#1e1e2e", cursor="hand2")
        info_fr.pack(side=tk.LEFT, padx=(2, 4))

        l1 = tk.Label(info_fr, text=label, fg="#cdd6f4", bg="#1e1e2e", 
                      font=tkfont.Font(size=8), cursor="hand2")
        l1.pack(anchor="w")
        l2 = tk.Label(info_fr, text=f"{percentage:.2f}%", fg=badge_color,
                      bg="#1e1e2e", font=tkfont.Font(family="Helvetica", size=10, weight="bold"), cursor="hand2")
        l2.pack(anchor="w")

        # Binding click events to everything in the row
        for w in [row, dot, info_fr, l1, l2]:
            w.bind("<Button-1>", on_click)
