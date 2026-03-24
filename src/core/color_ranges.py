"""
color_ranges.py
---------------
Dataclass and loader for HSV color range configuration.
Reads from config/color_ranges.yaml so thresholds can be tuned
without modifying source code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ColorRange:
    """Represents an HSV range used to detect a specific color.

    OpenCV HSV convention: H ∈ [0, 179], S ∈ [0, 255], V ∈ [0, 255].

    Attributes
    ----------
    name:
        Human-readable color name (e.g. "red", "green").
    hue_lower1, hue_upper1:
        Primary hue range.
    hue_lower2, hue_upper2:
        Secondary hue range (used for red, which wraps around 0/179).
    sat_min:
        Minimum saturation threshold to exclude grays.
    val_min:
        Minimum value (brightness) threshold to exclude near-blacks.
    dual_range:
        If True, both (lower1, upper1) and (lower2, upper2) are used.
    """

    name: str
    display_name: str
    hue_lower1: int
    hue_upper1: int
    sat_min: int
    val_min: int
    dual_range: bool = False
    hue_lower2: Optional[int] = field(default=None)
    hue_upper2: Optional[int] = field(default=None)
    sat_max: int = 255
    val_max: int = 255

    def __post_init__(self) -> None:
        if self.dual_range and (self.hue_lower2 is None or self.hue_upper2 is None):
            raise ValueError(
                f"ColorRange '{self.name}' has dual_range=True "
                "but hue_lower2/hue_upper2 are not set."
            )


def load_color_ranges(config_path: str | Path) -> list[ColorRange]:
    """Load color ranges from a YAML configuration file.

    Parameters
    ----------
    config_path:
        Path to the YAML file (e.g. ``config/color_ranges.yaml``).

    Returns
    -------
    list[ColorRange]
        List of parsed ColorRange objects, in the order defined in the file.

    Raises
    ------
    FileNotFoundError
        If *config_path* does not exist.
    ValueError
        If the YAML structure is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Color range config not found: {path}")

    logger.info("Loading color ranges from: %s", path)

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "colors" not in data:
        raise ValueError("Invalid config file: missing top-level 'colors' key.")

    ranges: list[ColorRange] = []
    for color_name, props in data["colors"].items():
        try:
            cr = ColorRange(
                name=color_name,
                display_name=props.get("display_name", color_name.capitalize()),
                hue_lower1=int(props["hue_lower1"]),
                hue_upper1=int(props["hue_upper1"]),
                sat_min=int(props["sat_min"]),
                val_min=int(props["val_min"]),
                dual_range=bool(props.get("dual_range", False)),
                hue_lower2=props.get("hue_lower2"),
                hue_upper2=props.get("hue_upper2"),
                sat_max=int(props.get("sat_max", 255)),
                val_max=int(props.get("val_max", 255)),
            )
            ranges.append(cr)
            logger.debug("Loaded range: %s", cr)
        except (KeyError, TypeError) as exc:
            raise ValueError(
                f"Invalid configuration for color '{color_name}': {exc}"
            ) from exc

    logger.info("Loaded %d color range(s): %s", len(ranges), [r.name for r in ranges])
    return ranges
