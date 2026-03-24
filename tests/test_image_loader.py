"""
test_image_loader.py
--------------------
Unit tests for the image loading and validation module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.core.image_loader import load_image, ImageLoadError


@pytest.fixture(tmp_path=Path)
def sample_png(tmp_path: Path) -> Path:
    """Create a small valid PNG in a temp directory."""
    img = Image.fromarray(
        np.zeros((10, 10, 3), dtype=np.uint8), mode="RGB"
    )
    path = tmp_path / "sample.png"
    img.save(path)
    return path


class TestLoadImage:
    def test_load_valid_png(self, sample_png: Path) -> None:
        img = load_image(sample_png)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"

    def test_load_returns_correct_size(self, sample_png: Path) -> None:
        img = load_image(sample_png)
        assert img.size == (10, 10)

    def test_load_nonexistent_file_raises(self) -> None:
        with pytest.raises(ImageLoadError, match="not found"):
            load_image("/nonexistent/path/image.png")

    def test_load_unsupported_extension_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "document.pdf"
        bad_file.write_bytes(b"fake pdf content")
        with pytest.raises(ImageLoadError, match="Unsupported file type"):
            load_image(bad_file)

    def test_load_existing_project_image(self) -> None:
        """Integration test using an actual image from the project images/ folder."""
        project_root = Path(__file__).parents[1]
        images_dir = project_root / "images"
        pngs = list(images_dir.glob("*.png"))
        if not pngs:
            pytest.skip("No PNG images found in images/ — skipping integration test")
        img = load_image(pngs[0])
        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
