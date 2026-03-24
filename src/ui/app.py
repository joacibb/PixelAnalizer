"""
app.py
------
Main application class. Wires together the UI components and delegates
all image processing to the core modules.

Updated with ROI (Region of Interest) and Pixel Inspection support.
"""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

from src.core.analyzer import ImageAnalyzer
from src.core.image_loader import ImageLoadError, load_image
from src.ui.image_panel import ImagePanel, InteractionMode
from src.ui.results_panel import ResultsPanel
from src.ui.toolbar import Toolbar
from src.utils.exporter import export_csv, export_json

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
_CONFIG_PATH  = _PROJECT_ROOT / "config" / "color_ranges.yaml"

WINDOW_TITLE  = "PixelAnalizer — Análisis Científico de Cobertura Terrestre"
WINDOW_SIZE   = "1360x850"


class PixelAnalizerApp:
    """Top-level application controller."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title(WINDOW_TITLE)
        self._root.geometry(WINDOW_SIZE)
        self._root.configure(bg="#11111b")
        self._root.minsize(1000, 600)

        self._analyzer = ImageAnalyzer(config_path=_CONFIG_PATH)
        self._current_image_path: str | None = None
        self._last_result = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Toolbar
        self._toolbar = Toolbar(
            self._root,
            on_load=self._on_load,
            on_calculate=self._on_calculate,
            on_show_color=self._on_show_veg,
            on_reset=self._on_reset,
            on_export_csv=self._on_export_csv,
            on_export_json=self._on_export_json,
            on_set_mode=self._on_set_mode,
        )
        self._toolbar.pack(side=tk.TOP, fill=tk.X)

        # Image panel
        self._image_panel = ImagePanel(self._root)
        self._image_panel.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._image_panel.on_pixel_inspect = self._on_pixel_inspect

        # Results panel
        self._results_panel = ResultsPanel(self._root, on_class_click=self._on_class_filter)
        self._results_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self._results_panel.config(height=100)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_class_filter(self, label: str | list[str]) -> None:
        """Filter the image to show only the selected class(es)."""
        if not self._image_panel.has_image():
            return
        
        display_label = label if isinstance(label, str) else "Vegetación (Total)"
        self._toolbar.set_status(f"Filtrando: {display_label}...", "#cba6f7")
        try:
            mask = self._analyzer.get_color_mask(self._image_panel.original_image, label)
            self._image_panel.show_color_mask(mask)
            self._toolbar.set_status(f"✓ Mostrando {display_label}", "#a6e3a1")
        except Exception as exc:
            logger.exception("Filter failed")
            messagebox.showerror("Error de Filtro", str(exc))

    def _on_set_mode(self, mode_str: str) -> None:
        if mode_str == "ROI":
            mode = InteractionMode.SELECT_ROI
            self._toolbar.set_status("Herramienta ROI activa: Dibujá un rectángulo para delimitar área.", "#cba6f7")
        elif mode_str == "INSPECT":
            mode = InteractionMode.INSPECT
            self._toolbar.set_status("Inspección activa: Hacé clic sobre la imagen.", "#cba6f7")
        else:
            mode = InteractionMode.PAN_ZOOM
            self._toolbar.set_status("Modo navegación (Pan/Zoom).", "#6c7086")
        
        self._image_panel.set_mode(mode)

    def _on_pixel_inspect(self, x: int, y: int) -> None:
        if not self._image_panel.has_image():
            return
            
        data = self._analyzer.inspect_pixel(self._image_panel.original_image, x, y)
        
        msg = (
            f"📍 Coordenadas: ({x}, {y})\n"
            f"🎨 RGB: {data['rgb']}\n"
            f"🌈 HSV: {data['hsv']}\n"
            f"🏷️ Clasificación: {data['display_name']} ({data['class_name']})"
        )
        self._toolbar.set_status(f"✓ Inspeccionado: {data['display_name']} en ({x},{y})", "#fab387")
        messagebox.showinfo("Inspección de Píxel", msg)

    def _on_load(self) -> None:
        file_path = filedialog.askopenfilename()
        if not file_path: return

        try:
            image = load_image(file_path)
            self._current_image_path = file_path
            self._last_result = None
            self._image_panel.set_image(image)
            self._results_panel.clear()
            self._toolbar.set_image_loaded(True)
            self._toolbar.set_status(f"✓ {Path(file_path).name} cargada", "#a6e3a1")
        except ImageLoadError as exc:
            messagebox.showerror("Error", str(exc))

    def _on_calculate(self) -> None:
        if not self._image_panel.has_image(): return

        roi = self._image_panel.get_current_roi()
        image = self._image_panel.original_image
        image_name = Path(self._current_image_path).name

        try:
            result = self._analyzer.analyze(image, image_name=image_name, roi=roi)
            self._last_result = result
            self._results_panel.display_result(result)
            status = "✓ Análisis de ROI completo" if roi else "✓ Análisis completo (Imagen Total)"
            self._toolbar.set_status(status, "#a6e3a1")
        except Exception as exc:
            logger.exception("Analysis failed")
            messagebox.showerror("Error", str(exc))

    def _on_show_veg(self) -> None:
        """Visualizar máscara de TODAS las vegetaciones (Densa + Media + Escasa)."""
        if not self._image_panel.has_image(): return
        # Usamos las IDs internas para evitar problemas con espacios en los nombres mostrados
        veg_classes = ["high_vegetation", "moderate_vegetation", "sparse_vegetation"]
        self._on_class_filter(veg_classes)
        self._toolbar.set_status("Vista restablecida.", "#6c7086")
        self._on_set_mode("PAN") # Reset to pan mode too

    def _on_reset(self) -> None:
        self._image_panel.reset()
        self._toolbar.set_status("Vista restablecida.", "#6c7086")
        self._on_set_mode("PAN") # Reset to pan mode too

    def _on_export_csv(self) -> None:
        if self._last_result is None: return
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if out_path:
            saved = export_csv(self._last_result, self._current_image_path or "", out_path)
            self._toolbar.set_status(f"✓ Exportado a {saved.name}", "#a6e3a1")

    def _on_export_json(self) -> None:
        if self._last_result is None: return
        out_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if out_path:
            saved = export_json(self._last_result, self._current_image_path or "", out_path)
            self._toolbar.set_status(f"✓ Exportado a {saved.name}", "#a6e3a1")
