from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, List, Sequence

import cv2
import numpy as np
from PIL import Image

from .exceptions import TechnicalRejectError


@dataclass
class QualityReport:
    score: float
    threshold: float


class ImageProcessor:
    def __init__(self, quality_threshold: float = 80.0, max_side: int = 1024) -> None:
        self.quality_threshold = quality_threshold
        self.max_side = max_side

    def calculate_phash(self, image_bytes: bytes) -> str:
        """Generate a perceptual hash for deduplication."""
        with Image.open(BytesIO(image_bytes)) as img:
            gray = img.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        pixels = np.asarray(gray, dtype=np.float32)
        dct = cv2.dct(pixels)
        low_freq = dct[:8, :8]
        median = float(np.median(low_freq))
        bits = ["1" if v > median else "0" for v in low_freq.flatten()]
        as_int = int("".join(bits), 2)
        return f"{as_int:016x}"

    def quality_check(self, image_bytes: bytes) -> QualityReport:
        """Raise early if image fails basic focus/clarity requirements."""
        np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
        if frame is None:
            raise TechnicalRejectError("Invalid image input; cannot decode.")

        variance = float(cv2.Laplacian(frame, cv2.CV_64F).var())
        if variance < self.quality_threshold:
            raise TechnicalRejectError(
                f"Image too blurry (score {variance:.2f} < {self.quality_threshold})."
            )
        return QualityReport(score=variance, threshold=self.quality_threshold)

    def smart_resize(self, image_bytes: bytes) -> bytes:
        """Resize while keeping aspect ratio; cap the longest side."""
        with Image.open(BytesIO(image_bytes)) as img:
            width, height = img.size
            longest = max(width, height)
            if longest <= self.max_side:
                return image_bytes

            scale = self.max_side / float(longest)
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            output = BytesIO()
            format_hint = img.format or "JPEG"
            resized.save(output, format=format_hint, quality=90)
            return output.getvalue()

    def redact_image(self, image_bytes: bytes, boxes: Iterable[Sequence[float]]) -> bytes:
        """
        Black out sensitive regions for audit compliance.

        Boxes are expected as absolute pixel coords [x1, y1, x2, y2].
        """
        np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
        if frame is None:
            return image_bytes

        height, width = frame.shape[:2]
        for box in boxes:
            if len(box) != 4:
                continue
            x1, y1, x2, y2 = [int(b) for b in box]
            x_start = max(x1, 0)
            y_start = max(y1, 0)
            x_end = min(x2, width)
            y_end = min(y2, height)
            cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (0, 0, 0), -1)

        _, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return bytes(encoded)

