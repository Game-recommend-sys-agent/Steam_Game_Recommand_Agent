import json
from pathlib import Path

CAPTION_DIR = Path("data/captions")
OUTPUT_PATH = Path("data/embedding_input.jsonl")


def flatten_visual_cues(cues: dict) -> str:
    parts = []
    for key, values in cues.items():
        if not values:
            continue
        joined = ", ".join(values)
        parts.append(f"{key}: {joined}")
    return "; ".join(parts)


def main():
    json_files = sorted(CAPTION_DIR.glob("*.json"))
    print(f"[INFO] Found {len(json_files)} caption json files")

    records = []

    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        appid = data["appid"]

        chunks = []

        # 1️⃣ image caption
        if data.get("image_caption"):
            chunks.append(f"Image description: {data['image_caption']}")

        # 2️⃣ visual keywords
        if data.get("visual_keywords"):
            keywords = ", ".join(data["visual_keywords"])
            chunks.append(f"Visual keywords: {keywords}")

        # 3️⃣ primary character (🔥 가중치 2)
        primary = data.get("primary_character")
        if primary:
            cues = flatten_visual_cues(primary.get("visual_cues", {}))
            if cues:
                chunks.append(f"Primary character traits: {cues}")
                chunks.append(f"Primary character traits: {cues}")  # 가중치

        # 4️⃣ salient characters (가중치 1)
        for sc in data.get("salient_characters", []):
            cues = flatten_visual_cues(sc.get("visual_cues", {}))
            if cues:
                chunks.append(f"Salient character traits: {cues}")

        embedding_text = "\n".join(chunks)

        records.append({
            "appid": appid,
            "embedding_text": embedding_text
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[DONE] Saved embedding input to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
