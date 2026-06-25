from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any


class OcrEngineError(RuntimeError):
    """Raised when the OCR engine cannot load or recognize an image."""


@dataclass
class OcrWord:
    words: str
    left: int
    top: int
    width: int
    height: int
    score: float | None = None


@dataclass
class OcrResult:
    words: list[OcrWord]
    duration_ms: int


class RapidOcrEngine:
    """OCR engine backed by RapidOCR with ONNX Runtime.

    Uses PP-OCR model weights and runs inference through ONNX Runtime,
    which is 2–5× faster on CPU and uses less memory than PaddlePaddle.
    """

    def __init__(self) -> None:
        self._model: Any | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        if self._model is not None:
            return

        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]
        except Exception as exc:
            raise OcrEngineError(
                "RapidOCR cannot be imported. "
                "Install it with: pip install rapidocr-onnxruntime"
            ) from exc

        try:
            self._model = RapidOCR()
        except Exception as exc:
            raise OcrEngineError(
                f"RapidOCR cannot be loaded: {exc}"
            ) from exc

    def recognize(self, image_path: Path) -> OcrResult:
        self.load()

        started = perf_counter()
        try:
            raw_result, elapse = self._model(str(image_path))
        except Exception as exc:
            raise OcrEngineError(
                f"RapidOCR recognize failed: {exc}"
            ) from exc

        return OcrResult(
            words=self._parse_result(raw_result),
            duration_ms=self._calc_duration_ms(elapse, started),
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _parse_result(self, raw_result: Any) -> list[OcrWord]:
        """Parse RapidOCR output into OcrWord list.

        ``raw_result`` is ``None`` when no text is detected, otherwise a
        list of ``[box, text, score]`` triples where *box* is four corner
        points ``[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]``.
        """
        if not raw_result:
            return []

        parsed: list[OcrWord] = []
        for item in raw_result:
            box, text, score = item
            bounds = _box_to_bounds(box)
            if bounds is None:
                continue
            parsed.append(
                OcrWord(
                    words=str(text),
                    score=float(score) if score is not None else None,
                    **bounds,
                )
            )
        return parsed

    @staticmethod
    def _calc_duration_ms(elapse: Any, started: float) -> int:
        """Extract duration in milliseconds from RapidOCR elapse value.

        *elapse* is ``[det_time, cls_time, rec_time]`` (seconds) or a
        single float.  Falls back to wall-clock measurement.
        """
        if isinstance(elapse, (list, tuple)):
            return int(sum(float(e) for e in elapse) * 1000)
        if isinstance(elapse, (int, float)):
            return int(float(elapse) * 1000)
        return int((perf_counter() - started) * 1000)


def _box_to_bounds(box: Any) -> dict[str, int] | None:
    """Convert a RapidOCR bounding box to ``{left, top, width, height}``.

    Handles both axis-aligned ``[x1, y1, x2, y2]`` rectangles and
    four-corner polygon ``[[x1,y1], …, [x4,y4]]`` lists.
    """
    if box is None:
        return None

    if hasattr(box, "tolist"):
        box = box.tolist()

    if (
        isinstance(box, (list, tuple))
        and len(box) == 4
        and all(isinstance(value, (int, float)) for value in box)
    ):
        left = int(box[0])
        top = int(box[1])
        width = int(box[2] - box[0])
        height = int(box[3] - box[1])
        return {"left": left, "top": top, "width": width, "height": height}

    if not isinstance(box, (list, tuple)):
        return None

    points = []
    for point in box:
        if hasattr(point, "tolist"):
            point = point.tolist()
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        try:
            points.append((float(point[0]), float(point[1])))
        except (TypeError, ValueError):
            return None

    if not points:
        return None

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    left = int(min(xs))
    top = int(min(ys))
    return {
        "left": left,
        "top": top,
        "width": int(max(xs) - left),
        "height": int(max(ys) - top),
    }


ocr_engine = RapidOcrEngine()
