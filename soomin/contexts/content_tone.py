# contexts/content_tone.py
from typing import Dict, List, Optional


def build(
    narrative_result: Dict,
    meta_input: Optional[Dict] = None
) -> Dict:
    """
    Build content & character tone context (3.2 + 3.1 결과 병합).

    narrative_result (LLM-based, required):
      - emotional_tone: List[str]
      - narrative_focus: str
      - char_personality_tags: List[str]
      - avoidance_flags: List[str]

    meta_input (DB-based, optional / PoC에서는 비워도 됨):
      - world_setting_tags: List[str]
      - char_species: List[str]
      - char_visual_style: List[str]
    """

    if not narrative_result:
        return {}

    meta_input = meta_input or {}

    # LLM 추론 기반 태그
    emotional_tone = narrative_result.get("emotional_tone", [])
    personality_tags = narrative_result.get("char_personality_tags", [])

    # DB / 메타 기반 태그 (PoC에서는 optional)
    world_setting_tags = meta_input.get("world_setting_tags", [])

    # 추천용 통합 태그 (LLM + Meta)
    content_tags = list(set(
        emotional_tone +
        personality_tags +
        world_setting_tags
    ))

    return {
        # 3.1 (LLM 기반)
        "emotional_tone": emotional_tone,
        "narrative_focus": narrative_result.get("narrative_focus", ""),
        "char_personality_tags": personality_tags,
        "avoidance_flags": narrative_result.get("avoidance_flags", []),

        # 3.A (팩트 기반, optional)
        "char_species": meta_input.get("char_species", []),
        "char_visual_style": meta_input.get("char_visual_style", []),
        "world_setting_tags": world_setting_tags,

        # 추천 엔진용 통합 태그
        "content_tags": content_tags
    }