from typing import Any

from pydantic import BaseModel


class OcrHealthResponse(BaseModel):
    status: str
    engine: str
    model: str
    device: str
    model_loaded: bool
    version: str


class OcrLocationResponse(BaseModel):
    left: int
    top: int
    width: int
    height: int


class OcrWordResponse(BaseModel):
    words: str
    location: OcrLocationResponse
    score: float | None = None

    @classmethod
    def from_ocr_word(cls, word: Any) -> "OcrWordResponse":
        return cls(
            words=word.words,
            location=OcrLocationResponse(
                left=word.left,
                top=word.top,
                width=word.width,
                height=word.height,
            ),
            score=word.score,
        )


class OcrRecognizeResponse(BaseModel):
    success: bool = True
    engine: str
    model: str
    device: str
    duration_ms: int
    words_result: list[OcrWordResponse]


class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: str
