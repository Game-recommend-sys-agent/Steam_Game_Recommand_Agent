import base64
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ===============================
# Env & Client
# ===============================
load_dotenv()  # 🔥 필수
client = OpenAI()

# ===============================
# Config
# ===============================
IMAGE_DIR = Path("data/images")
OUTPUT_DIR = Path("data/captions")
MODEL_NAME = "gpt-4.1-mini"  # vision 지원

# ===============================
# Utils
# ===============================
def encode_image_to_data_url(image_path: Path) -> str:
    """
    Encode image as data URL for OpenAI Vision input
    """
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def build_prompt():
    return (
        "You are an assistant analyzing video game poster images.\n\n"
        "Your goal is to extract visually observable character traits that can later "
        "support image-based character preference matching.\n\n"
        "Steps:\n"
        "1. Write ONE neutral image caption describing only what is visible.\n"
        "2. Extract 4–15 visual keywords based on appearance.\n"
        "3. Identify characters in the poster and extract visual cues.\n\n"
        "Character handling rules:\n"
        "- Identify ONE primary character (most visually emphasized overall).\n"
        "- Additionally, identify up to TWO salient characters who are visually distinctive\n"
        "  due to color, hairstyle, species traits, or accessories, even if they are not central.\n"
        "- Do NOT extract more than 3 characters in total.\n\n"
        "Character visual cue categories:\n"
        "- species_traits (e.g. human, elf ears, animal-like features, android parts)\n"
        "- face_features (e.g. sharp eyes, round eyes, scars, facial markings)\n"
        "- facial_expression (e.g. smiling, neutral, serious, angry)\n"
        "- body_traits (e.g. slim build, muscular, dynamic pose)\n"
        "- hair_traits (e.g. hair color, hairstyle)\n"
        "- clothing_style (e.g. uniform, armor, gothic dress)\n"
        "- visual_color (e.g. pink, black, silver)\n"
        "- props_or_accessories (e.g. glasses, weapons, books)\n\n"
        "Rules:\n"
        "- Do NOT infer personality traits (heroic, cool, kind, evil).\n"
        "- Do NOT infer story roles or morality.\n"
        "- Use only visually observable attributes.\n"
        "- If uncertain, choose the most neutral option.\n\n"
        "Output format (JSON only):\n"
        "{\n"
        '  "image_caption": "...",\n'
        '  "visual_keywords": ["...", "..."],\n'
        '  "primary_character": {\n'
        '    "character_id": "char_1",\n'
        '    "salience_reason": "",\n'
        '    "visual_cues": {\n'
        '      "species_traits": [],\n'
        '      "face_features": [],\n'
        '      "facial_expression": [],\n'
        '      "body_traits": [],\n'
        '      "hair_traits": [],\n'
        '      "clothing_style": [],\n'
        '      "visual_color": [],\n'
        '      "props_or_accessories": []\n'
        "    }\n"
        "  },\n"
        '  "salient_characters": [\n'
        "    {\n"
        '      "character_id": "char_2",\n'
        '      "salience_reason": "",\n'
        '      "visual_cues": {\n'
        '        "species_traits": [],\n'
        '        "face_features": [],\n'
        '        "facial_expression": [],\n'
        '        "body_traits": [],\n'
        '        "hair_traits": [],\n'
        '        "clothing_style": [],\n'
        '        "visual_color": [],\n'
        '        "props_or_accessories": []\n'
        "      }\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
def repair_to_json(raw_text: str) -> dict:
    repair_prompt = (
        "Convert the following content into valid JSON.\n"
        "Return JSON only. Do not add explanations.\n\n"
        f"{raw_text}"
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=repair_prompt
    )

    repaired_text = (response.output_text or "").strip()
    return json.loads(repaired_text)

# ===============================
# Main
# ===============================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_files = list(IMAGE_DIR.glob("*.jpg"))
    print(f"[INFO] Found {len(image_files)} images")

    for image_path in image_files:
        appid = int(image_path.stem)
        output_path = OUTPUT_DIR / f"{appid}.json"
        debug_path = OUTPUT_DIR / f"{appid}_raw.txt"

        if output_path.exists():
            print(f"[SKIP] Caption already exists for appid={appid}")
            continue

        response = None  # raw 응답 백업용

        try:
            print(f"[PROCESS] Generating caption for appid={appid}")

            image_data_url = encode_image_to_data_url(image_path)

            # ---------- 1️⃣ Vision + 1차 JSON 시도 ----------
            response = client.responses.create(
                model=MODEL_NAME,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": build_prompt()},
                            {"type": "input_image", "image_url": image_data_url},
                        ],
                    }
                ],
            )

            raw_text = (response.output_text or "").strip()
            if not raw_text:
                raise ValueError("Empty response from model")

            caption_data = json.loads(raw_text)

        except Exception:
            # ---------- 2️⃣ JSON 파싱 실패 → repair ----------
            print(f"[WARN] JSON parse failed for appid={appid}, attempting repair...")

            try:
                raw_text = (response.output_text or "").strip()
                caption_data = repair_to_json(raw_text)
                print(f"[RECOVERED] appid={appid} repaired successfully")

            except Exception as repair_e:
                # ---------- 3️⃣ 최종 실패 ----------
                print(f"[ERROR] Final failure for appid={appid}: {repair_e}")

                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(response.output_text or "")

                continue  # 다음 이미지로

        # ---------- 4️⃣ 성공 케이스 저장 ----------
        caption_data["appid"] = appid
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)

    print("[DONE] Caption generation completed")


if __name__ == "__main__":
    main()
