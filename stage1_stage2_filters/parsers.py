# filters/parsers.py
import re
from typing import Dict, Any, Optional, List, Set


# ===============================
# Supported Languages
# ===============================
def parse_supported_languages(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw or not isinstance(raw, str):
        return None

    clean = re.sub(r"<[^>]+>", "", raw)

    all_languages: List[str] = []
    audio_languages: List[str] = []
    subtitle_languages: List[str] = []

    for token in clean.split(","):
        token = token.strip()
        if not token:
            continue

        if "*" in token:
            lang = token.replace("*", "").strip()
            audio_languages.append(lang)
        else:
            lang = token
            subtitle_languages.append(lang)

        all_languages.append(lang)

    return {
        "all_languages": all_languages,
        "audio_languages": audio_languages,
        "subtitle_languages": subtitle_languages,
        "lang_count": len(all_languages),
        "has_korean": "Korean" in all_languages,
        "has_korean_audio": "Korean" in audio_languages,
    }


# ===============================
# Genres
# ===============================
GENRE_GROUP_MAP = {
    "Action": "action",
    "Adventure": "action",
    "Action RPG": "action",
    "Shooter": "action",

    "RPG": "rpg",
    "JRPG": "rpg",
    "CRPG": "rpg",

    "Strategy": "strategy",
    "RTS": "strategy",
    "Turn-Based Strategy": "strategy",

    "Simulation": "simulation",
    "Sandbox": "simulation",

    "Casual": "casual",
    "Puzzle": "casual",
    "Indie": "casual",

    "Visual Novel": "story",
}


def parse_genres(genres: Optional[List[Dict[str, str]]]) -> Optional[Dict[str, Any]]:
    if not genres or not isinstance(genres, list):
        return None

    all_genres = [
        g["description"]
        for g in genres
        if isinstance(g, dict) and "description" in g
    ]

    if not all_genres:
        return None

    genre_groups: Set[str] = {
        GENRE_GROUP_MAP.get(g, "other") for g in all_genres
    }

    return {
        "all_genres": all_genres,
        "genre_groups": list(genre_groups),
        "genre_count": len(all_genres),
    }


# ===============================
# PC Spec (RAM only)
# ===============================
def parse_min_ram(req_html: Optional[str]) -> Dict[str, Any]:
    if not req_html or not isinstance(req_html, str):
        return {"min_ram_gb": None, "parse_success": False}

    text = re.sub(r"<[^>]+>", "", req_html)

    match = re.search(
        r"Memory:\s*([\d.]+)\s*(GB|MB)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return {"min_ram_gb": None, "parse_success": False}

    value = float(match.group(1))
    unit = match.group(2).upper()
    ram_gb = value if unit == "GB" else value / 1024

    return {
        "min_ram_gb": round(ram_gb, 2),
        "parse_success": True,
    }


# ===============================
# Steam App 통합 (🔥 핵심 수정)
# ===============================
def parse_steam_app(app_details: Dict[str, Any]) -> Dict[str, Any]:
    # -------------------------------
    # PC Requirements 방어 처리
    # -------------------------------
    pc_req = app_details.get("pc_requirements")

    minimum_req = None

    if isinstance(pc_req, dict):
        # 일반 케이스
        minimum_req = pc_req.get("minimum")

        # windows / mac / linux 하위 구조 케이스
        if not minimum_req:
            for os_key in ("windows", "mac", "linux"):
                os_req = pc_req.get(os_key)
                if isinstance(os_req, dict) and os_req.get("minimum"):
                    minimum_req = os_req.get("minimum")
                    break

    elif isinstance(pc_req, list) and pc_req:
        # 리스트 안에 dict가 있는 케이스
        first = pc_req[0]
        if isinstance(first, dict):
            minimum_req = first.get("minimum")

    # else: None 유지

    return {
        "languages": parse_supported_languages(
            app_details.get("supported_languages")
        ),
        "genres": parse_genres(
            app_details.get("genres")
        ),
        "pc_spec": parse_min_ram(minimum_req),
    }