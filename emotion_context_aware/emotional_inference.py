import json
from typing import Dict, Any


# ===============================
# LLM Emotional Inference Engine
# ===============================
def LLM_emotional_inference(
    llm_payload: Dict[str, Any],
    client,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2
) -> Dict[str, Any]:
    """
    Infer the emotional and narrative structure of a game
    using a 2-layer emotional representation:
    - dominant label
    - distribution over multiple labels

    Returns a fixed emotional schema.
    """

    # ---------------------------
    # System Prompt
    # ---------------------------
    system_prompt = """
You are an expert in game narrative, emotional design, and interactive experience analysis.

Your task is to infer the emotional and experiential structure of a game
ONLY from the provided data:

- Game genres, tags, and short description
- Soundtrack tracklist (titles, order, duration)

You must NOT rely on prior knowledge of the game.
Do NOT invent story details not supported by the data.

Base your reasoning primarily on the soundtrack.
Game metadata should be used only as supporting signals.

Return ONLY valid JSON that strictly follows the given schema.
"""

    # ---------------------------
    # User Prompt (🔥 2-layer schema)
    # ---------------------------
    user_prompt = f"""
Analyze the following game data and infer its emotional structure.

For each of the following axes:
- affect
- experience_frame
- world_dynamics

1. Select ONE dominant label.
2. Then provide a probability distribution over relevant labels.
3. Probabilities must sum to 1.0.
4. Do NOT include negligible labels.

Return your result strictly in the JSON schema below.

JSON Schema:
{{
  "emotional_persistence": "stable | oscillating | volatile",
  "emotional_rhythm": "slow-wave | pulse | spike-driven",
  "emotional_residue": "resolved | lingering | amplifying | fading",

  "dominant_affect": "hopeful | anxious | aggressive | playful | melancholic | awe | oppressive | neutral",
  "affect_distribution": {{
    "<affect_label>": float
  }},

  "experience_frame_distribution": {{
    "playful | desperate | duty-bound | curious | defiant | altruistic | cynical": float
  }},

  "world_dynamics_distribution": {{
    "event-driven | space-driven | interaction-driven": float
  }},

  "rationale": {{
    "key_track_signals": [],
    "structural_signals": [],
    "notes": ""
  }}
}}

Game Meta:
{json.dumps(llm_payload["game_meta"], ensure_ascii=False, indent=2)}

Soundtrack Tracklist:
{json.dumps(llm_payload["soundtrack"]["tracks"], ensure_ascii=False, indent=2)}
"""

    # ---------------------------
    # LLM Call
    # ---------------------------
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        temperature=temperature
    )

    content = response.choices[0].message.content.strip()

    # ---------------------------
    # Parse JSON
    # ---------------------------
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            "LLM returned invalid JSON.\n\n"
            f"Raw output:\n{content}"
        ) from e

    # ---------------------------
    # Validation (distribution sum)
    # ---------------------------
    def _validate_distribution(dist: Dict[str, float], name: str):
        s = sum(dist.values())
        if not (0.99 <= s <= 1.01):
            raise ValueError(
                f"{name} distribution must sum to 1.0 (got {s})"
            )

    _validate_distribution(result["affect_distribution"], "affect_distribution")
    _validate_distribution(result["experience_frame_distribution"], "experience_frame_distribution")
    _validate_distribution(result["world_dynamics_distribution"], "world_dynamics_distribution")

    return result