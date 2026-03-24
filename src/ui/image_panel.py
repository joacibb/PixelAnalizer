"""
image_panel.py
--------------
Tkinter widget responsible for image display, zoom and drag navigation.
Now supports ROI (Region of Interest) selection and Pixel Inspection.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Optional, Callable

import numpy as np
import cv2
from PIL import Image, ImageTk
import tkinter as tk

logger = logging.getLogger(__name__)


class InteractionMode(Enum):
    PAN_ZOOM = auto()
    SELECT_ROI = auto()
    INSPECT = auto()


class ImagePanel(tk.Frame):
    """Canvas-like frame that displays a PIL Image with zoom, drag, ROI and Inspection.

    Parameters
    ----------
    parent:
        Parent Tkinter widget.
    """

    # Zoom limits
    ZOOM_MIN = 0.05
    ZOOM_MAX = 20.0

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, bg="black", **kwargs)

        self._label = tk.Label(self, bg="black")
        self._label.pack(expand=True, fill=tk.BOTH)

        # State
        self._original_image: Optional[Image.Image] = None
        self._current_image: Optional[Image.Image] = None   # may be filtered
        self._image_tk: Optional[ImageTk.PhotoImage] = None

        self._zoom_factor: float = 1.0
        self._pan_x: float = 0.0
        self._pan_y: float = 0.0
        self._drag_start: Optional[tuple[int, int]] = None
        self._show_filtered: bool = False
        
        self._mode = InteractionMode.PAN_ZOOM
        self._roi_start: Optional[tuple[int, int]] = None
        self._roi_rect_id: Optional[int] = None
        self._current_roi: Optional[tuple[int, int, int, int]] = None
        
        self.on_pixel_inspect: Optional[Callable[[int, int], None]] = None

        # Bind events
        self._label.bind("<Button-1>", self._on_click_start)
        self._label.bind("<B1-Motion>", self._on_drag_motion)
        self._label.bind("<ButtonRelease-1>", self._on_click_release)
        self._label.bind("<MouseWheel>", self._on_mouse_wheel)
        self._label.bind("<Button-4>", self._on_scroll_up)
        self._label.bind("<Button-5>", self._on_scroll_down)

        # We need a canvas for drawing the ROI rectangle over the image
        # Wait, using a Label is simpler for images but Canvas is better for drawing.
        # Let's stick with Label for now and use a thin Frame or similar for ROI if needed,
        # OR just refresh the image with the ROI drawn on it (simpler to implement correctly).
        # Actually, let's keep it simple: draw ROI on a temporary copy of the image.

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_image(self, image: Image.Image) -> None:
        """Load a new image and reset view state."""
        self._original_image = image.copy()
        self._current_image = image.copy()
        self._zoom_factor = 1.0
        self._center_image()
        self._refresh()
        self._current_roi = None
        self._show_filtered = False

    def set_mode(self, mode: InteractionMode) -> None:
        self._mode = mode
        logger.debug("ImagePanel mode changed to: %s", mode.name)
        if mode == InteractionMode.PAN_ZOOM:
            self._label.config(cursor="")
        elif mode == InteractionMode.SELECT_ROI:
            self._label.config(cursor="crosshair")
        elif mode == InteractionMode.INSPECT:
            self._label.config(cursor="tcross")

    def show_color_mask(self, mask: np.ndarray) -> None:
        """Display a binary colour mask."""
        if self._original_image is None:
            return
        orig_np = np.array(self._original_image, dtype=np.uint8)
        mask_3ch = np.stack([mask, mask, mask], axis=-1)
        filtered_np = cv2.bitwise_and(orig_np, mask_3ch)
        self._current_image = Image.fromarray(filtered_np)
        self._show_filtered = True
        self._refresh()

    def clear_roi(self) -> None:
        self._current_roi = None
        self._refresh()

    def reset(self) -> None:
        """Restore original image and reset zoom/pan."""
        if self._original_image is None:
            return
        self._current_image = self._original_image.copy()
        self._show_filtered = False
        self._zoom_factor = 1.0
        self._current_roi = None
        self._center_image()
        self._refresh()

    def get_current_roi(self) -> Optional[tuple[int, int, int, int]]:
        return self._current_roi

    def has_image(self) -> bool:
        return self._original_image is not None

    @property
    def original_image(self) -> Optional[Image.Image]:
        return self._original_image

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _center_image(self) -> None:
        self.update_idletasks()
        fw = self.winfo_width() or 1360
        fh = self.winfo_height() or 700
        iw, ih = self._original_image.size
        self._pan_x = (iw - fw) / 2.0
        self._pan_y = (ih - fh) / 2.0

    def _refresh(self, roi_preview: Optional[tuple[int, int, int, int]] = None) -> None:
        if self._original_image is None:
            return

        src = self._current_image if self._show_filtered else self._original_image
        display = self._zoom_crop(src)
        
        # Draw ROI if exists
        if self._current_roi or roi_preview:
            draw_img = display.copy()
            # We need to map original coordinates to current display coordinates
            # This is complex because of zoom/crop. 
            # Simpler: convert to numpy, draw with cv2, convert back.
            arr = np.array(draw_img)
            
            roi_to_draw = roi_preview if roi_preview else self._current_roi
            if roi_to_draw:
                # Map ROI (orig coords) to display coords (0-W, 0-H)
                d_roi = self._map_to_display(roi_to_draw)
                if d_roi:
                    cv2.rectangle(arr, (d_roi[0], d_roi[1]), (d_roi[2], d_roi[3]), (0, 255, 255), 2)
            
            display = Image.fromarray(arr)

        self._image_tk = ImageTk.PhotoImage(display)
        self._label.config(image=self._image_tk)
        self._label.image = self._image_tk

    def _map_to_display(self, orig_roi: tuple[int, int, int, int]) -> Optional[tuple[int, int, int, int]]:
        """Map coordinates from original image to current display label."""
        w, h = self._original_image.size
        zoom = self._zoom_factor
        
        # Visible region in original coords
        half_w = w / (2 * zoom)
        half_h = h / (2 * zoom)
        cx = self._pan_x + w / 2
        cy = self._pan_y + h / 2
        left_orig = cx - half_w
        top_orig = cy - half_h

        # Scaling factor from cropped region to full display size (which is w, h by design of _zoom_crop)
        # _zoom_crop returns an image resized back to (w, h)
        scale_x = w / (2 * half_w) # which is just 'zoom'
        scale_y = h / (2 * half_h)

        x1 = int((orig_roi[0] - left_orig) * scale_x)
        y1 = int((orig_roi[1] - top_orig) * scale_y)
        x2 = int((orig_roi[2] - left_orig) * scale_x)
        y2 = int((orig_roi[3] - top_orig) * scale_y)

        # Clamp to display bounds
        return (max(0, x1), max(0, y1), min(w, x2), min(h, y2))

    def _map_to_original(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Map screen (label) coordinates back to original image coordinates."""
        w, h = self._original_image.size
        zoom = self._zoom_factor
        
        half_w = w / (2 * zoom)
        half_h = h / (2 * zoom)
        cx = self._pan_x + w / 2
        cy = self._pan_y + h / 2
        left_orig = cx - half_w
        top_orig = cy - half_h

        orig_x = left_orig + (screen_x / w) * (2 * half_w)
        orig_y = top_orig + (screen_y / h) * (2 * half_h)
        
        return (int(orig_x), int(orig_y))

    def _zoom_crop(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, self._zoom_factor))
        half_w = w / (2 * zoom)
        half_h = h / (2 * zoom)
        cx = self._pan_x + w / 2
        cy = self._pan_y + h / 2

        left   = max(0.0, cx - half_w)
        top    = max(0.0, cy - half_h)
        right  = min(float(w), cx + half_w)
        bottom = min(float(h), cy + half_h)

        if right - left < 1 or bottom - top < 1:
            return img

        cropped = img.crop((int(left), int(top), int(right), int(bottom)))
        return cropped.resize((w, h), Image.LANCZOS)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_click_start(self, event: tk.Event) -> None:
        if self._original_image is None:
            return
            
        if self._mode == InteractionMode.PAN_ZOOM:
            self._drag_start = (event.x, event.y)
        elif self._mode == InteractionMode.SELECT_ROI:
            self._roi_start = self._map_to_original(event.x, event.y)
        elif self._mode == InteractionMode.INSPECT:
            ox, oy = self._map_to_original(event.x, event.y)
            if self.on_pixel_inspect:
                self.on_pixel_inspect(ox, oy)

    def _on_drag_motion(self, event: tk.Event) -> None:
        if self._original_image is None:
            return
            
        if self._mode == InteractionMode.PAN_ZOOM and self._drag_start:
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            self._pan_x -= dx / self._zoom_factor
            self._pan_y -= dy / self._zoom_factor
            self._drag_start = (event.x, event.y)
            self._refresh()
        elif self._mode == InteractionMode.SELECT_ROI and self._roi_start:
            curr = self._map_to_original(event.x, event.y)
            # Preview ROI
            x1, y1 = min(self._roi_start[0], curr[0]), min(self._roi_start[1], curr[1])
            x2, y2 = max(self._roi_start[0], curr[0]), max(self._roi_start[1], curr[1])
            self._refresh(roi_preview=(x1, y1, x2, y2))

    def _on_click_release(self, event: tk.Event) -> None:
        if self._mode == InteractionMode.SELECT_ROI and self._roi_start:
            curr = self._map_to_original(event.x, event.y)
            x1, y1 = min(self._roi_start[0], curr[0]), min(self._roi_start[1], curr[1])
            x2, y2 = max(self._roi_start[0], curr[0]), max(self._roi_start[1], curr[1])
            
            # Minimum ROI size check (10x10)
            if (x2 - x1) > 5 and (y2 - y1) > 5:
                self._current_roi = (x1, y1, x2, y2)
                logger.info("ROI defined: %s", self._current_roi)
            else:
                self._current_roi = None
            
            self._roi_start = None
            self._refresh()
            
        self._drag_start = None

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        if self._original_image is None:
            return
        factor = 1.1 ** (event.delta / 120.0)
        self._zoom_factor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, self._zoom_factor * factor))
        self._refresh()

    def _on_scroll_up(self, event: tk.Event) -> None:
        if self._original_image is None:
            return
        self._zoom_factor = min(self.ZOOM_MAX, self._zoom_factor * 1.1)
        self._refresh()

    def _on_scroll_down(self, event: tk.Event) -> None:
        if self._original_image is None:
            return
        self._zoom_factor = max(self.ZOOM_MIN, self._zoom_factor / 1.1)
        self._refresh()
