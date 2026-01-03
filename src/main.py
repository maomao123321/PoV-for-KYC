from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Set

from pydantic import ValidationError

from .config import Settings
from .exceptions import ModelCallError, SchemaValidationError, TechnicalRejectError
from .extractor import FireworksExtractor
from .processor import ImageProcessor
from .schemas import ExtractionResult
from .validator import DocumentValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    status: str
    score: float
    logic_score: float
    phash: str
    issues: list
    flagged_fields: list
    payload: dict


QUALITY_THRESHOLD = 80.0
MAX_SIDE = 1024
MODEL = "accounts/fireworks/models/qwen2p5-vl-32b-instruct"
FALLBACK_MODEL = "accounts/fireworks/models/qwen2p5-vl-32b-instruct"
TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_BASE = 0.8


class KYCPipeline:
    def __init__(self, api_key: str, seen_hashes: Optional[Set[str]] = None) -> None:
        self.processor = ImageProcessor(quality_threshold=QUALITY_THRESHOLD, max_side=MAX_SIDE)
        self.validator = DocumentValidator()
        self.api_key = api_key
        self.seen_hashes: Set[str] = seen_hashes or set()

    async def run(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> PipelineResult:
        phash = self.processor.calculate_phash(image_bytes)
        if phash in self.seen_hashes:
            raise TechnicalRejectError("Duplicate upload detected.")
        self.seen_hashes.add(phash)

        quality_report = self.processor.quality_check(image_bytes)
        resized = self.processor.smart_resize(image_bytes)

        async with FireworksExtractor(
            api_key=self.api_key,
            model=MODEL,
            fallback_model=FALLBACK_MODEL,
            timeout=TIMEOUT,
            max_retries=MAX_RETRIES,
            backoff_base=BACKOFF_BASE,
        ) as extractor:
            extraction_payload = await extractor.extract(resized, mime_type=mime_type)

        extraction_result = ExtractionResult(
            payload=extraction_payload, image_quality=quality_report.score, phash=phash
        )
        outcome = self.validator.assess(
            extraction=extraction_result.payload, image_quality=quality_report.score
        )

        return PipelineResult(
            status=outcome.status,
            score=outcome.ucs,
            logic_score=outcome.logic_score,
            phash=phash,
            issues=outcome.issues,
            flagged_fields=outcome.flagged_fields,
            payload=extraction_payload.model_dump(),
        )


def load_image_bytes(path: Path, mime_override: Optional[str] = None) -> tuple[bytes, str]:
    data = path.read_bytes()
    mime = mime_override or _guess_mime_from_suffix(path.suffix.lower())
    return data, mime


def _guess_mime_from_suffix(suffix: str) -> str:
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }
    return mapping.get(suffix, "image/jpeg")


async def run_single_file(image_path: Path, mime: Optional[str], api_key: str) -> PipelineResult:
    image_bytes, mime_type = load_image_bytes(image_path, mime_override=mime)
    pipeline = KYCPipeline(api_key=api_key)
    try:
        return await pipeline.run(image_bytes, mime_type=mime_type)
    except TechnicalRejectError as exc:
        return PipelineResult(
            status="RETRY_UPLOAD",
            score=0.0,
            logic_score=0.0,
            phash="",
            issues=[str(exc)],
            flagged_fields=[],
            payload={},
        )
    except (ModelCallError, SchemaValidationError) as exc:
        return PipelineResult(
            status="SYSTEM_ERROR",
            score=0.0,
            logic_score=0.0,
            phash="",
            issues=[f"API/parsing failure: {exc}"],
            flagged_fields=[],
            payload={},
        )


async def run_batch(
    input_dir: Path, output_dir: Path, api_key: str, mime: Optional[str] = None
) -> dict:
    """Process all images in a directory and generate summary."""
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not files:
        logger.warning(f"No image files found in {input_dir}")
        return {"total": 0, "success": 0, "manual_review": 0, "retry": 0, "error": 0, "results": []}
    
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    summary = {"SUCCESS": 0, "MANUAL_REVIEW": 0, "RETRY_UPLOAD": 0, "SYSTEM_ERROR": 0}
    
    for img_file in files:
        logger.info(f"Processing {img_file.name}...")
        result = await run_single_file(img_file, mime, api_key)
        
        summary[result.status] = summary.get(result.status, 0) + 1
        out_file = output_dir / f"{img_file.stem}.json"
        _write_output(out_file, result)
        
        results.append({
            "file": img_file.name,
            "status": result.status,
            "score": result.score,
            "issues": result.issues,
            "output": str(out_file)
        })
    
    summary_report = {
        "total": len(files),
        "success": summary.get("SUCCESS", 0),
        "manual_review": summary.get("MANUAL_REVIEW", 0),
        "retry": summary.get("RETRY_UPLOAD", 0),
        "error": summary.get("SYSTEM_ERROR", 0),
        "results": results
    }
    
    summary_file = output_dir / "summary.json"
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    logger.info(f"Batch summary written to {summary_file}")
    
    return summary_report


async def main(
    image_path: Optional[str] = None,
    batch_dir: Optional[str] = None,
    mime: Optional[str] = None,
    output_path: Optional[str] = None,
) -> None:
    try:
        settings = Settings.from_env()
    except ValidationError as exc:
        logger.error("Configuration invalid: %s", exc)
        return
    
    if batch_dir:
        input_dir = Path(batch_dir)
        output_dir = Path(output_path) if output_path else Path("outputs")
        summary = await run_batch(input_dir, output_dir, settings.fireworks_api_key, mime)
        logger.info(
            f"Batch complete: {summary['success']} success, {summary['manual_review']} manual review, "
            f"{summary['retry']} retry, {summary['error']} error"
        )
        return
    
    target = image_path or os.getenv("KYC_SAMPLE_IMAGE")
    if not target:
        logger.info("Provide --image or --batch to run.")
        return
    
    result = await run_single_file(Path(target), mime, settings.fireworks_api_key)
    logger.info("Pipeline result: %s", asdict(result))
    
    if output_path:
        _write_output(Path(output_path), result)


def _write_output(path: Path, result: PipelineResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    asyncio.run(main())

