# filters/pipeline.py
import pandas as pd
import random

from .filters import (
    filter_age,
    filter_genre,
    filter_price,
    # filter_discount,
    filter_spec,
)
from .parsers import parse_steam_app
from .steam_api import fetch_app_details


def run_pipeline(
    games_df,
    user_pref: dict,
    max_results: int = 300,
    max_api_calls: int = 1000,
):
    """
    검증용 파이프라인
    - Stage1: OS 필터만
    - Stage1.5: 랜덤 최대 1000개로 API 요청 제한
    - Stage2: 실 API + 하드 필터
    """

    # ==================================================
    # Stage 1 : OS Filter (CSV 기반)
    # ==================================================
    os_col_map = {
        "windows": "Windows",
        "mac": "Mac",
        "linux": "Linux",
    }

    os_col = os_col_map.get(user_pref["os"])
    if os_col is None or os_col not in games_df.columns:
        stage1_df = games_df
    else:
        stage1_df = games_df[games_df[os_col].astype(bool)]

    # 🔥 핵심 수정: AppID를 반드시 int로 변환
    # ✅ AppID는 index에서 가져온다 (정답)
    stage1_appids = (
    stage1_df.index
    .to_series()
    .pipe(pd.to_numeric, errors="coerce")
    .dropna()
    .astype(int)
    .tolist()
)

    if not stage1_appids:
        return []

    print(f"[Stage1] OS 통과 AppID 수: {len(stage1_appids)}")

    # ==================================================
    # Stage 1.5 : 랜덤 샘플링 (최대 1000개)
    # ==================================================
    if len(stage1_appids) > max_api_calls:
        random.seed(42)
        stage1_appids = random.sample(stage1_appids, max_api_calls)

    print(f"[Stage1.5] API 요청 대상 AppID 수: {len(stage1_appids)}")

    # ==================================================
    # Stage 2 : API + Hard Filtering
    # ==================================================
    results = []

    debug_drop_counts = {
        "age": 0,
        "spec": 0,
        "price": 0,
        # "discount": 0,
        "genre": 0,
        "passed": 0,
        "api_fail": 0,
    }

    for idx, appid in enumerate(stage1_appids, start=1):
        # 🔒 안전장치 (혹시 모를 타입 붕괴 방지)
        if not isinstance(appid, int):
            debug_drop_counts["api_fail"] += 1
            continue

        app_details = fetch_app_details(appid)
        if not app_details:
            debug_drop_counts["api_fail"] += 1
            continue

        # --- 파싱 ---
        parsed = parse_steam_app(app_details)

        # API 필드 병합
        parsed["required_age"] = app_details.get("required_age")

        price_info = app_details.get("price_overview") or {}
        parsed["final_price"] = price_info.get("final")
        parsed["discount_percent"] = price_info.get("discount_percent")

        # ==================================================
        # Stage 2 Hard Filters (탈락 확률 낮은 순)
        # ==================================================

        if not filter_age(parsed, user_pref["age_limit"]):
            debug_drop_counts["age"] += 1
            continue

        if not filter_spec(parsed, user_pref["spec_preset"]):
            debug_drop_counts["spec"] += 1
            continue

        if not filter_price(parsed, user_pref["price_bucket"]):
            debug_drop_counts["price"] += 1
            continue

        # if not filter_discount(parsed, user_pref["discount_buckets"]):
        #     debug_drop_counts["discount"] += 1
        #     continue

        if not filter_genre(parsed, user_pref["genre_groups"]):
            debug_drop_counts["genre"] += 1
            continue

        # --- 통과 ---
        results.append(appid)
        debug_drop_counts["passed"] += 1

        if len(results) >= max_results:
            break

        if idx % 100 == 0:
            print(f"[Stage2] processed {idx} / {len(stage1_appids)}")

    # ==================================================
    # Debug Summary
    # ==================================================
    print("\n[DEBUG] Stage2 탈락 원인 요약")
    for k, v in debug_drop_counts.items():
        print(f"  - {k}: {v}")

    return results