# contexts/sentiment.py
from typing import Dict, List


def normalize_aspect_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
    """
    Ensure aspect weights sum to 1.0
    """
    total = sum(raw_weights.values())
    if total == 0:
        return raw_weights
    return {k: v / total for k, v in raw_weights.items()}


def build(review_analysis: Dict, user_input: Dict) -> Dict:
    """
    Build sentiment / persona context.

    review_analysis (LLM output placeholder):
      - aspect_weights: Dict[str, float]
      - churn_triggers: List[str]

    user_input:
      - current_mood_tag: List[str]
    """

    aspect_weights = normalize_aspect_weights(
        review_analysis.get("aspect_weights", {})
    )

    churn_triggers = review_analysis.get("churn_triggers", [])

    current_mood = user_input.get("current_mood_tag", [])

    sentiment_tags = list(set(
        list(aspect_weights.keys()) +
        churn_triggers +
        current_mood
    ))

    return {
        "weighted_aspect_preference": aspect_weights,
        "churn_triggers": churn_triggers,
        "current_mood_tag": current_mood,
        "sentiment_tags": sentiment_tags
    }