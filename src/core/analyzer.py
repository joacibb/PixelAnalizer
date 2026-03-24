"""
analyzer.py
-----------
Core image analysis engine. Computes per-color pixel percentage distribution
using HSV color space. Completely decoupled from any GUI framework.

Now supports ROI (Region of Interest) analysis and pixel inspection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np
from PIL import Image

from src.core.color_ranges import ColorRange, load_color_ranges

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default config path relative to project root
_DEFAULT_CONFIG = Path(__file__).parents[2] / "config" / "color_ranges.yaml"


class AnalysisResult:
    """Holds the percentage distribution of colors in an analyzed image or ROI.

    Attributes
    ----------
    percentages:
        Mapping of color display_name → percentage of non-black area (0–100).
    total_pixels:
        Total number of pixels in the image or ROI.
    non_black_pixels:
        Number of pixels considered for analysis (black excluded).
    image_name:
        Source image filename, if available.
    roi:
        Optional tuple (left, top, right, bottom) of the analyzed region.
    """

    def __init__(
        self,
        percentages: dict[str, float],
        total_pixels: int,
        non_black_pixels: int,
        image_name: str = "",
        roi: Optional[tuple[int, int, int, int]] = None,
    ) -> None:
        self.percentages = percentages
        self.total_pixels = total_pixels
        self.non_black_pixels = non_black_pixels
        self.image_name = image_name
        self.roi = roi

    def __repr__(self) -> str:  # pragma: no cover
        pct = ", ".join(f"{k}={v:.2f}%" for k, v in self.percentages.items())
        r_str = f" [ROI={self.roi}]" if self.roi else ""
        return f"AnalysisResult({pct}){r_str}"


class ImageAnalyzer:
    """Performs HSV-based color analysis on PIL Images.

    Parameters
    ----------
    config_path:
        Path to the YAML color range configuration file.
    """

    def __init__(self, config_path: str | Path = _DEFAULT_CONFIG) -> None:
        self._color_ranges: list[ColorRange] = load_color_ranges(config_path)
        logger.info(
            "ImageAnalyzer initialized with %d color ranges.", len(self._color_ranges)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self, 
        image: Image.Image, 
        image_name: str = "",
        roi: Optional[tuple[int, int, int, int]] = None
    ) -> AnalysisResult:
        """Compute the percentage of each configured color class in *image*.

        Parameters
        ----------
        image:
            A PIL Image in RGB mode.
        image_name:
            Optional label for the source image.
        roi:
            Optional (left, top, right, bottom) coordinates to analyze a portion.

        Returns
        -------
        AnalysisResult
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Crop if ROI exists
        if roi:
            left, top, right, bottom = roi
            # Clamp to image bounds
            left = max(0, min(left, image.width - 1))
            top = max(0, min(top, image.height - 1))
            right = max(left + 1, min(right, image.width))
            bottom = max(top + 1, min(bottom, image.height))
            image = image.crop((left, top, right, bottom))
            logger.info("Analyzing ROI: (%d, %d, %d, %d)", left, top, right, bottom)

        image_np = np.array(image, dtype=np.uint8)
        hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

        # Non-black mask: exclude pixels where all RGB channels are 0
        non_black_mask = np.any(image_np != 0, axis=-1)
        non_black_count = int(np.sum(non_black_mask))
        total_pixels = image_np.shape[0] * image_np.shape[1]

        if non_black_count == 0:
            percentages = {cr.display_name: 0.0 for cr in self._color_ranges}
            return AnalysisResult(percentages, total_pixels, 0, image_name, roi)

        percentages: dict[str, float] = {}
        for color_range in self._color_ranges:
            color_mask = self._build_color_mask(hsv, color_range)
            combined = color_mask & non_black_mask
            pct = float(np.sum(combined)) / non_black_count * 100.0
            # We use display_name for the UI/results
            percentages[color_range.display_name] = round(pct, 4)

        return AnalysisResult(percentages, total_pixels, non_black_count, image_name, roi)

    def inspect_pixel(self, image: Image.Image, x: int, y: int) -> dict:
        """Get information about a specific pixel.

        Returns
        -------
        dict with keys: 'rgb', 'hsv', 'class_name', 'display_name'
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Clamp coordinates
        x = max(0, min(x, image.width - 1))
        y = max(0, min(y, image.height - 1))

        rgb = image.getpixel((x, y))
        
        # Convert to HSV via single-pixel array
        pixel_np = np.array([[rgb]], dtype=np.uint8)
        hsv_arr = cv2.cvtColor(pixel_np, cv2.COLOR_RGB2HSV)
        hsv = tuple(hsv_arr[0, 0].tolist())

        # Determine class
        found_class = "Undefined / Background"
        found_display = "Indefinido"

        # Check classes in order (first match wins)
        for cr in self._color_ranges:
            if self._pixel_matches(hsv, cr):
                found_class = cr.name
                found_display = cr.display_name
                break

        return {
            "coords": (x, y),
            "rgb": rgb,
            "hsv": hsv,
            "class_name": found_class,
            "display_name": found_display
        }

    def get_color_mask(
        self, image: Image.Image, display_name: str | list[str]
    ) -> np.ndarray:
        """Return a binary mask for the given color display name(s).
        
        If a list is provided, returns the union (OR) of all masks.
        """
        if isinstance(display_name, str):
            display_names = [display_name]
        else:
            display_names = display_name

        if image.mode != "RGB":
            image = image.convert("RGB")

        image_np = np.array(image, dtype=np.uint8)
        hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
        
        full_mask = np.zeros(hsv.shape[:2], dtype=bool)

        for name in display_names:
            # Check both display name and internal name
            target = next(
                (cr for cr in self._color_ranges if cr.display_name == name), None
            )
            if target is None:
                target = next((cr for cr in self._color_ranges if cr.name == name), None)
                
            if target is None:
                logger.warning("Class or ID '%s' not found during mask merge.", name)
                continue

            bool_mask = self._build_color_mask(hsv, target)
            full_mask |= bool_mask

        return (full_mask.astype(np.uint8)) * 255

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_color_mask(
        hsv: np.ndarray, color_range: ColorRange
    ) -> np.ndarray:
        """Build a boolean mask for *color_range* from *hsv* image array.

        Now handles sat_max and val_max.
        """
        lower1 = np.array(
            [color_range.hue_lower1, color_range.sat_min, color_range.val_min],
            dtype=np.uint8,
        )
        upper1 = np.array(
            [color_range.hue_upper1, color_range.sat_max, color_range.val_max], 
            dtype=np.uint8
        )
        mask = cv2.inRange(hsv, lower1, upper1).astype(bool)

        if color_range.dual_range:
            lower2 = np.array(
                [color_range.hue_lower2, color_range.sat_min, color_range.val_min],
                dtype=np.uint8,
            )
            upper2 = np.array(
                [color_range.hue_upper2, color_range.sat_max, color_range.val_max], 
                dtype=np.uint8
            )
            mask2 = cv2.inRange(hsv, lower2, upper2).astype(bool)
            mask = mask | mask2

        return mask

    @staticmethod
    def _pixel_matches(hsv: tuple[int, int, int], cr: ColorRange) -> bool:
        """Quick check if a single HSV tuple matches a ColorRange."""
        h, s, v = hsv
        
        # Check Sat/Val limits
        if not (cr.sat_min <= s <= cr.sat_max and cr.val_min <= v <= cr.val_max):
            return False
            
        # Check Hue range 1
        matches = cr.hue_lower1 <= h <= cr.hue_upper1
        
        # Check Hue range 2 if dual
        if not matches and cr.dual_range:
            matches = cr.hue_lower2 <= h <= cr.hue_upper2
            
        return matches
