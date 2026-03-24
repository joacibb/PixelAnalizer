"""
test_analyzer.py
----------------
Unit tests for the ImageAnalyzer core class.
No GUI dependencies — all tests run in headless mode.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Ensure the project root is on sys.path when run with pytest from the root.
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.core.analyzer import ImageAnalyzer, AnalysisResult

_CONFIG = Path(__file__).parents[1] / "config" / "color_ranges.yaml"


@pytest.fixture(scope="module")
def analyzer() -> ImageAnalyzer:
    return ImageAnalyzer(config_path=_CONFIG)


# -----------------------------------------------------------------------
# Helper factories
# -----------------------------------------------------------------------

def solid_rgb_image(r: int, g: int, b: int, size: int = 50) -> Image.Image:
    """Return a solid-colour PIL RGB image of *size* × *size* pixels."""
    arr = np.full((size, size, 3), [r, g, b], dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def black_image(size: int = 50) -> Image.Image:
    return solid_rgb_image(0, 0, 0, size)


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

class TestBlackImage:
    def test_all_percentages_zero(self, analyzer: ImageAnalyzer) -> None:
        result = analyzer.analyze(black_image(), image_name="black_test")
        assert isinstance(result, AnalysisResult)
        for color, pct in result.percentages.items():
            assert pct == 0.0, f"Expected 0% for '{color}', got {pct}"

    def test_non_black_pixels_zero(self, analyzer: ImageAnalyzer) -> None:
        result = analyzer.analyze(black_image())
        assert result.non_black_pixels == 0


class TestRedDetection:
    def test_pure_red_dominates(self, analyzer: ImageAnalyzer) -> None:
        """A strongly red image (HSV ≈ 0°, high S and V) should give high red %."""
        # RGB (220, 30, 30) → HSV ≈ (0°, 86%, 86%) — solidly red
        img = solid_rgb_image(220, 30, 30)
        result = analyzer.analyze(img, image_name="red_test")
        assert result.percentages["red"] >= 90.0, (
            f"Expected ≥90% red, got {result.percentages['red']:.2f}%"
        )

    def test_red_percentage_not_tautological(self, analyzer: ImageAnalyzer) -> None:
        """Bug fix verification: purely green image must NOT report ~100% red."""
        img = solid_rgb_image(30, 200, 30)
        result = analyzer.analyze(img)
        assert result.percentages["red"] < 10.0, (
            f"Red detection is tautological — got {result.percentages['red']:.2f}% on green image"
        )


class TestGreenDetection:
    def test_pure_green_dominates(self, analyzer: ImageAnalyzer) -> None:
        # RGB (30, 200, 30) → HSV ≈ (120°, 85%, 78%) — solidly green
        img = solid_rgb_image(30, 200, 30)
        result = analyzer.analyze(img, image_name="green_test")
        assert result.percentages["green"] >= 85.0, (
            f"Expected ≥85% green, got {result.percentages['green']:.2f}%"
        )


class TestBlueDetection:
    def test_pure_blue_dominates(self, analyzer: ImageAnalyzer) -> None:
        # RGB (30, 60, 220) → HSV ≈ (228°→mapped to 114°, high S, V)
        img = solid_rgb_image(30, 60, 220)
        result = analyzer.analyze(img, image_name="blue_test")
        assert result.percentages["blue"] >= 80.0, (
            f"Expected ≥80% blue, got {result.percentages['blue']:.2f}%"
        )


class TestColorMask:
    def test_mask_shape(self, analyzer: ImageAnalyzer) -> None:
        img = solid_rgb_image(220, 30, 30, size=40)
        mask = analyzer.get_color_mask(img, "red")
        assert mask.shape == (40, 40)

    def test_mask_values(self, analyzer: ImageAnalyzer) -> None:
        """Mask for a solid-red image must be all 255 (within detected pixels)."""
        img = solid_rgb_image(220, 30, 30, size=20)
        mask = analyzer.get_color_mask(img, "red")
        unique = set(np.unique(mask))
        assert unique <= {0, 255}, f"Unexpected mask values: {unique}"
        # At least 80% of pixels should be detected as red
        assert np.sum(mask == 255) / mask.size >= 0.8

    def test_invalid_color_raises(self, analyzer: ImageAnalyzer) -> None:
        img = solid_rgb_image(100, 100, 100)
        with pytest.raises(ValueError, match="not found"):
            analyzer.get_color_mask(img, "purple")
