import json
from pathlib import Path

CAPTION_DIR = Path("data/captions")

def is_valid_caption_json(data: dict) -> bool:
    try:
        # 1. caption
        if not isinstance(data.get("image_caption"), str):
            return False
        if not data["image_caption"].strip():
            return False

        # 2. keywords
        keywords = data.get("visual_keywords")
        if not isinstance(keywords, list) or len(keywords) < 3:
            return False

        # 3. primary character cues
        primary = data.get("primary_character")
        if not isinstance(primary, dict):
            return False

        cues = primary.get("visual_cues")
        if not isinstance(cues, dict):
            return False

        # 시각 단서가 전부 비어 있으면 무효
        if all(not v for v in cues.values()):
            return False

        # 4. salient characters는 list면 OK
        salient = data.get("salient_characters", [])
        if not isinstance(salient, list):
            return False

        return True

    except Exception:
        return False


def extract_json_block(text: str) -> str | None:
    if not text:
        return None

    t = text.strip()

    # 1) ```json ... ``` 코드블록 제거
    if t.startswith("```"):
        t = t.strip("`").strip()
        if t.lower().startswith("json"):
            t = t[4:].strip()

    # 2) 전체에서 첫 { ~ 마지막 } 범위
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start:end + 1]

    return None


def main():
    raw_files = sorted(CAPTION_DIR.glob("*_raw.txt"))
    print(f"[INFO] Found {len(raw_files)} raw files")

    for raw_path in raw_files:
        appid = raw_path.stem.replace("_raw", "")
        json_path = CAPTION_DIR / f"{appid}.json"
        invalid_path = CAPTION_DIR / f"{appid}_invalid.json"

        if json_path.exists():
            print(f"[SKIP] appid={appid} already converted")
            continue

        text = raw_path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"[WARN] Empty raw file appid={appid}")
            continue

        try:
            json_text = extract_json_block(text)
            if not json_text:
                raise ValueError("No JSON object found")

            data = json.loads(json_text)

            if not is_valid_caption_json(data):
                print(f"[INVALID] appid={appid} failed validation")
                with open(invalid_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                continue

            data["appid"] = int(appid)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[OK] appid={appid} converted")

        except Exception as e:
            print(f"[FAIL] appid={appid}: {e}")

    print("[DONE] Raw repair completed")


if __name__ == "__main__":
    main()

