# filters/dataset.py
import os
import pandas as pd
from .pipeline import run_pipeline


def main():
    # 1. CSV 로드
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "..", "data", "raw", "games.csv")
    games_df = pd.read_csv(csv_path)

    # 2. 유저 임의 조건 (검증용)
    user_pref = {
        "os": "windows",

        # Stage2 (하드 필터)
        "age_limit": 22,
        "genre_groups": ["story", "rpg"],
        "price_bucket": "10000_30000",
        # "discount_buckets": ["30_50", "50_70"],
        "spec_preset": "mid",
    }

    # 3. 전체 파이프라인 실행 (샘플링 제거 버전)
    final_results = run_pipeline(
        games_df=games_df,
        user_pref=user_pref,
        max_results=300,
    )

    print(f"[Result] 최종 결과 수: {len(final_results)}")
    print(final_results[:10])


if __name__ == "__main__":
    main()