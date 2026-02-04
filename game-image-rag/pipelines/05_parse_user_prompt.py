import json
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

OUTPUT_DIR = Path("data/user_queries")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ===============================
# Env & Client
# ===============================
load_dotenv()
client = OpenAI()

MODEL_NAME = "gpt-4.1-mini"

# ===============================
# Prompts
# ===============================
SYSTEM_PROMPT = """
You are an assistant that translates a user's character preference
into VISUALLY OBSERVABLE CHARACTER TRAITS ONLY.

- Convert abstract or emotional expressions into commonly associated visual cues
- Store ONLY visually observable traits
- Do NOT store abstract traits (e.g. heroic, motherly, sly)
- If no reasonable visual mapping exists, leave the field empty
"""

USER_PROMPT_TEMPLATE = """
User request:
"{user_input}"

Interpret the request and output ONLY visually observable traits
as JSON with these keys:

- species_traits
- face_features
- facial_expression
- body_traits
- hair_traits
- clothing_style
- visual_color
- props_or_accessories

Output JSON only.
"""

def extract_json_block(text: str) -> str:
    """
    Extract the first valid JSON object from a text string.
    Handles cases where extra text appears before or after JSON.
    """
    if not text:
        raise ValueError("Empty text")

    t = text.strip()

    # 코드블록 ```json ... ``` 제거
    if t.startswith("```"):
        t = t.strip("`").strip()
        if t.lower().startswith("json"):
            t = t[4:].strip()

    start = t.find("{")
    end = t.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in text")

    return t[start:end + 1]

# ===============================
# Core Function
# ===============================
def parse_user_prompt(user_input: str) -> dict:
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(user_input=user_input)
            }
        ]
    )

    # 1️⃣ output_json 우선 시도
    for item in response.output:
        for block in item.content:
            if block.type == "output_json":
                return block.json

    # 2️⃣ fallback: output_text에서 JSON 추출
    texts = []
    for item in response.output:
        for block in item.content:
            if block.type == "output_text":
                texts.append(block.text)

    raw_text = "\n".join(texts).strip()
    if not raw_text:
        raise ValueError("No text output found")

    json_text = extract_json_block(raw_text)
    return json.loads(json_text)



# ===============================
# Local Test
# ===============================
if __name__ == "__main__":
    text = "우는 게 예쁠 것 같은 어두운 분위기의 여성 캐릭터 추천해줘"

    print("[USER INPUT]")
    print(text)

    parsed = parse_user_prompt(text)

    print("\n[PARSED VISUAL CUES]")
    print(json.dumps(parsed, ensure_ascii=False, indent=2))

    # ✅ 여기서 저장
    output_path = OUTPUT_DIR / "latest_user_query.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "user_input": text,
                "visual_cues": parsed
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\n[SAVED] {output_path}")
