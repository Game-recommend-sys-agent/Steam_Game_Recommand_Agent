"""
Context-aware 공용 스키마(placeholder).

추후:
- pydantic 모델로 고정 스키마(JSON) 강제
- 또는 TypedDict/dataclass로 타입 힌트 제공

참고: `docs/context_aware.md`, `docs/context_aware_5to8.md`
"""

from __future__ import annotations

from typing import Any


BehaviorContext = dict[str, Any]
QualityTrustContext = dict[str, Any]
LiveContext = dict[str, Any]
DiscountContext = dict[str, Any]

