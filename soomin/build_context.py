# build_context.py
from contexts import situational, sentiment, content_tone, play_style


def build(selected_contexts, raw_inputs):
    """
    selected_contexts: list[str]
      e.g. ["situational", "sentiment", "content_tone", "play_style"]

    raw_inputs:
      {
        "situational": {
            "user": {...},
            "time": {...}          # optional
        },
        "sentiment": {
            "review_analysis": {...},
            "user_input": {...}
        },
        "content_tone": {
            "narrative_result": {...},   # 3.1 LLM output (required)
            "meta_input": {...}           # optional (IGDB/RAWG 자리)
        },
        "play_style": {
            "play_log": [...]
        }
      }
    """

    context = {}

    # 1️⃣ Situational Context
    if "situational" in selected_contexts:
        context["situational"] = situational.build(
            raw_inputs["situational"]["user"],
            raw_inputs["situational"].get("time")
        )

    # 2️⃣ Sentiment / Persona Context
    if "sentiment" in selected_contexts:
        context["sentiment"] = sentiment.build(
            raw_inputs["sentiment"]["review_analysis"],
            raw_inputs["sentiment"]["user_input"]
        )

    # 3️⃣ Content / Character Tone Context
    # - narrative_result: LLM 기반 (필수)
    # - meta_input: DB 기반 (optional, PoC에서는 비워도 됨)
    if "content_tone" in selected_contexts:
        context["content_tone"] = content_tone.build(
            narrative_result=raw_inputs["content_tone"]["narrative_result"],
            meta_input=raw_inputs["content_tone"].get("meta_input")
        )

    # 4️⃣ Play Style Context
    if "play_style" in selected_contexts:
        context["play_style"] = play_style.build(
            raw_inputs["play_style"]["play_log"]
        )

    return context


if __name__ == "__main__":
    from pprint import pprint
    import json

    with open("samples/situational.json") as f:
        situational_sample = json.load(f)

    with open("samples/sentiment.json") as f:
        sentiment_sample = json.load(f)

    with open("samples/content_tone.json") as f:
        content_tone_sample = json.load(f)

    with open("samples/play_style.json") as f:
        play_style_sample = json.load(f)

    result = build(
        selected_contexts=[
            "situational",
            "sentiment",
            "content_tone",
            "play_style"
        ],
        raw_inputs={
            "situational": situational_sample,
            "sentiment": sentiment_sample,
            "content_tone": content_tone_sample,
            "play_style": play_style_sample
        }
    )

    pprint(result)