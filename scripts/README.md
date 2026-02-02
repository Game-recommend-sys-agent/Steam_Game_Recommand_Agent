# scripts/ — Phase 1 수집·전처리 스크립트

1차 스크래핑·API 호출 스크립트는 **여기(`scripts/`)** 에 두고, 아래 **파일명**을 쓰면 됩니다.

## 1차 스크래핑 스크립트 (파일 위치·이름)

| 파일명 | 역할 | 출력 (예시) |
|--------|------|--------------|
| `scrape_steam_store.py` | Steam **스토어** 검색 목록 스크래핑 (게임 목록, 출시일, 가격 등) | `data/raw/steam_store_games.json` (또는 팀 합의 경로) |
| `scrape_steam_full_sample.py` | 한 게임 **전체 샘플** (상세 페이지 + 리뷰 JSON) — 수집 가능 필드 확인용 | `data/raw/full_sample_{appid}.json` |
| `scrape_steam_api.py` | Steam **공식 API** 호출 (GetAppList, GetNewsForApp, GetOwnedGames 등) | `data/raw/steam_api_sample.json` |

- **위치:** 위 파일들은 모두 **`scripts/`** 디렉터리에 생성.
- **실행:** 프로젝트 루트에서 `python scripts/scrape_steam_store.py --pages 2` 처럼 실행.

## 전처리 스크립트 (나중 단계)

- raw → processed 변환, 스키마 통일 등은 팀 합의 후 `scripts/preprocess_*.py` 등으로 추가하면 됩니다.
