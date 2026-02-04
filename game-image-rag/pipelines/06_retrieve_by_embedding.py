import json
import math
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ===============================
# Env & Client
# ===============================
load_dotenv()
client = OpenAI()

EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4.1-mini"

# ===============================
# Paths
# ===============================
CAPTION_DIR = Path("data/captions")
IMAGE_DIR = Path("data/images")
USER_QUERY_PATH = Path("data/user_queries/latest_user_query.json")

RESULT_DIR = Path("data/results")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# ===============================
# Weights (face = color > props)
# ===============================
WEIGHTS = {
    "face_features": 2,
    "facial_expression": 2,
    "visual_color": 2,
    "props_or_accessories": 1,
    "hair_traits": 1,
    "clothing_style": 1,
    "body_traits": 1,
    "species_traits": 0.5,
}

# ===============================
# Utils
# ===============================
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b + 1e-8)


def flatten_visual_cues(cues: dict) -> str:
    chunks = []
    for key, weight in WEIGHTS.items():
        values = cues.get(key, [])
        if not values:
            continue
        phrase = ", ".join(values)
        repeated = " ".join([phrase] * int(weight))
        chunks.append(f"{key}: {repeated}")
    return "\n".join(chunks)


def get_embedding(text: str) -> list[float]:
    res = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return res.data[0].embedding


def get_game_cues(game: dict) -> dict | None:
    """
    구조 fallback:
    1) character_visual_cues
    2) primary_character.visual_cues
    """
    if "character_visual_cues" in game:
        return game["character_visual_cues"]

    primary = game.get("primary_character")
    if primary:
        return primary.get("visual_cues")

    return None


# ===============================
# LLM fallback rerank
# ===============================
def llm_fallback_rerank(user_input: str, candidates: list, top_k: int):
    prompt = f"""
User preference:
"{user_input}"

Below are game poster candidates with visual descriptions.
Select the TOP {top_k} games that best match the user's preference.
Even if imperfect, choose the most visually similar ones.

Return JSON only.

Candidates:
{json.dumps(candidates, ensure_ascii=False, indent=2)}
"""

    response = client.responses.create(
        model=LLM_MODEL,
        input=prompt
    )

    raw = (response.output_text or "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start:end + 1])


# ===============================
# Main
# ===============================
def main(top_k: int = 5):
    # 1️⃣ Load user query
    user_data = json.loads(USER_QUERY_PATH.read_text(encoding="utf-8"))
    user_text = flatten_visual_cues(user_data["visual_cues"])
    user_embedding = get_embedding(user_text)

    print("[INFO] User embedding generated")

    scored_games = []

    # 2️⃣ Score games
    for path in CAPTION_DIR.glob("*.json"):
        game = json.loads(path.read_text(encoding="utf-8"))
        appid = game.get("appid")

        if not appid:
            continue

        cues = get_game_cues(game)
        if not cues:
            continue

        image_path = IMAGE_DIR / f"{appid}.jpg"
        if not image_path.exists():
            continue

        game_text = flatten_visual_cues(cues)
        game_embedding = get_embedding(game_text)
        score = cosine_similarity(user_embedding, game_embedding)

        scored_games.append({
            "appid": appid,
            "game_name": game.get("name", f"appid_{appid}"),
            "score": score,
            "image_path": str(image_path),
            "image_caption": game.get("image_caption", ""),
            "visual_summary": game_text
        })

    # 3️⃣ Sort
    scored_games.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_games[:top_k]

    # 4️⃣ Fallback: if empty or too weak
    if not top_results:
        print("[WARN] No strong match found → LLM fallback rerank")

        fallback_pool = scored_games[:10]
        output = llm_fallback_rerank(
            user_input=user_data["user_input"],
            candidates=fallback_pool,
            top_k=top_k
        )
    else:
        output = {
            "user_input": user_data["user_input"],
            "top_k": top_k,
            "results": [
                dict(rank=i + 1, **item)
                for i, item in enumerate(top_results)
            ]
        }

    # 5️⃣ Save
    output_path = RESULT_DIR / "latest_recommendations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] {output_path}\n")

    # 6️⃣ Preview
    for r in output.get("results", []):
        print(
            f"{r.get('rank', '-')}. {r.get('game_name')} "
            f"(appid={r.get('appid')}) | score={r.get('score', 0):.4f}"
        )
        print(f"   image: {r.get('image_path')}\n")


if __name__ == "__main__":
    main(top_k=5)
