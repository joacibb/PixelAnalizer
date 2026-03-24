"""
image_loader.py
---------------
Responsible for loading, validating and converting images from disk.
Decoupled from UI to allow use in batch/headless processing pipelines.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Supported image file extensions
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
)


class ImageLoadError(Exception):
    """Raised when an image cannot be loaded or is invalid."""


def load_image(file_path: str | Path) -> Image.Image:
    """Load an image from *file_path* and return it as a PIL RGB Image.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the image file.

    Returns
    -------
    PIL.Image.Image
        Image in RGB mode.

    Raises
    ------
    ImageLoadError
        If the path does not exist, the extension is unsupported,
        or the file cannot be decoded.
    """
    path = Path(file_path)

    if not path.exists():
        raise ImageLoadError(f"File not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImageLoadError(
            f"Unsupported file type '{path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    logger.info("Loading image: %s", path)

    bgr_image: np.ndarray | None = cv2.imread(str(path))
    if bgr_image is None:
        raise ImageLoadError(
            f"OpenCV could not decode the file: {path}. "
            "The file may be corrupt or in an unsupported format."
        )

    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    logger.info(
        "Image loaded successfully — size: %dx%d px, mode: %s",
        pil_image.width,
        pil_image.height,
        pil_image.mode,
    )
    return pil_image
