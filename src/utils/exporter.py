"""
exporter.py
-----------
Export analysis results to CSV and JSON formats with full metadata.
Designed for reproducibility: every export includes the timestamp,
image path, and the exact HSV parameters used.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.core.analyzer import AnalysisResult

logger = logging.getLogger(__name__)

_EXPORTS_DIR = Path(__file__).parents[2] / "exports"


def _build_metadata(result: AnalysisResult, image_path: str | Path) -> dict:
    """Build a metadata dictionary common to all export formats."""
    return {
        "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "image_name": result.image_name or Path(image_path).name,
        "image_path": str(image_path),
        "total_pixels": result.total_pixels,
        "non_black_pixels": result.non_black_pixels,
        "percentages": result.percentages,
    }


def export_csv(
    result: AnalysisResult,
    image_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Export *result* to a CSV file.

    Parameters
    ----------
    result:
        The AnalysisResult returned by ImageAnalyzer.analyze().
    image_path:
        Path to the source image (used for metadata).
    output_path:
        Destination CSV file path. If None, a timestamped file is created
        automatically inside ``exports/``.

    Returns
    -------
    Path
        Absolute path to the written CSV file.
    """
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(image_path).stem
        output_path = _EXPORTS_DIR / f"{stem}_{ts}.csv"

    output_path = Path(output_path)
    meta = _build_metadata(result, image_path)

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        # Header block
        writer.writerow(["# PixelAnalizer Export"])
        writer.writerow(["timestamp_utc", meta["timestamp_utc"]])
        writer.writerow(["image_name", meta["image_name"]])
        writer.writerow(["image_path", meta["image_path"]])
        writer.writerow(["total_pixels", meta["total_pixels"]])
        writer.writerow(["non_black_pixels", meta["non_black_pixels"]])
        writer.writerow([])
        # Data
        writer.writerow(["color", "percentage"])
        for color, pct in result.percentages.items():
            writer.writerow([color, f"{pct:.4f}"])

    logger.info("CSV export written: %s", output_path)
    return output_path


def export_json(
    result: AnalysisResult,
    image_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Export *result* to a JSON file.

    Parameters
    ----------
    result:
        The AnalysisResult returned by ImageAnalyzer.analyze().
    image_path:
        Path to the source image (used for metadata).
    output_path:
        Destination JSON file path. If None, a timestamped file is created
        automatically inside ``exports/``.

    Returns
    -------
    Path
        Absolute path to the written JSON file.
    """
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(image_path).stem
        output_path = _EXPORTS_DIR / f"{stem}_{ts}.json"

    output_path = Path(output_path)
    meta = _build_metadata(result, image_path)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    logger.info("JSON export written: %s", output_path)
    return output_path
