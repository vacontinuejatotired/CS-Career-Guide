"""Application facade and strategy contract for the existing interview behavior."""

from dataclasses import dataclass
from typing import Protocol

RESUME_MODE_AUTO = "auto"
RESUME_MODE_ATTACHED = "attached"
RESUME_MODE_NONE = "none"


@dataclass(frozen=True)
class InterviewPrompt:
    system: str
    user: str


class InterviewImplementation(Protocol):
    def prepare_turn(self, message, history, style, *, review=False, **kwargs) -> InterviewPrompt: ...
    def plan_turn(self, message, history, style, *, review=False, **kwargs): ...
    def parse_review(self, content) -> dict: ...


class InterviewService:
    def __init__(self, implementation):
        self.implementation = implementation

    def plan_turn(self, message, history, style, *,
                  review=False, resume=None, resume_mode=RESUME_MODE_AUTO,
                  summary="", summary_upto=0):
        return self.implementation.plan_turn(
            message, history, style, review=review,
            resume=resume, resume_mode=resume_mode,
            summary=summary, summary_upto=summary_upto,
        )

    def prepare_turn(self, message, history, style, *,
                     review=False, resume=None, resume_mode=RESUME_MODE_AUTO,
                     summary="", summary_upto=0):
        """向后兼容：旧调用方不传新参数仍可运行。"""
        return self.implementation.prepare_turn(
            message, history, style, review=review,
            resume=resume, resume_mode=resume_mode,
            summary=summary, summary_upto=summary_upto,
        )

    def parse_review(self, content):
        return self.implementation.parse_review(content)

