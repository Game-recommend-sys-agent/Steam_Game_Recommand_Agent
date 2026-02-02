# 프로젝트 디렉터리 구조

`docs/workflow.md` Phase 0~6에 맞춘 디렉터리 역할 정리입니다.

## 추천 아키텍처: Retrieval-first (Top-K), LLM은 후보 내에서만

유저 컨텍스트를 **LLM에 바로 넣지 않고**, ML 시스템·RAG 시스템처럼 **후보 검색(Retrieval) → Top-K 선택** 구조를 사용합니다.

- **후보 풀·Top-K Retrieval:** 컨텍스트·메타데이터·임베딩 등으로 후보 게임 풀을 만들고, 그 중 상위 K개를 선택. (비교 가능한 구조로 모델·파라미터 실험 가능.)
- **LLM 사용 시:** 전체 컨텍스트가 아니라 **Top-K로 줄인 후보**에 대해서만 비교·재랭킹·설명에 사용.

이에 맞춰 `context_aware/` 는 “후보 풀 생성 + Top-K”까지 담당하고, (선택) Top-K 내 LLM/재랭킹은 `context_aware/` 또는 별도 `rerank/` 모듈에서 처리할 수 있습니다.

**포트폴리오용:** ML·LLM·툴 사용 위치는 [workflow.md §2.1](workflow.md) 표에 정리되어 있습니다. (후보 풀·Top-K = ML/임베딩/FAISS 등, 재랭킹·설명 = LLM API.)

## 루트

| 항목 | 설명 |
|------|------|
| `README.md` | 프로젝트 소개, 디렉터리 요약, 시작하기 |
| `requirements.txt` | Python 의존성 |
| `baseline.py` | 베이스라인·실험용 스크립트 |
| `전략.pdf` | 차별화 전략 참고 문서 |
| `.gitignore` | 커밋 제외 대상 (가상환경, 데이터 파일, 시크릿 등) |

## config/

- 설정 파일, 스키마 예시.
- Phase 0에서 저장 형식·스키마 합의 후 예시를 두면 됨 (예: `schema.example.json`).

## data/

| 디렉터리 | 용도 |
|----------|------|
| `data/raw/` | Phase 1 — 스토어 스크래핑·API 응답 등 **원본** 저장. (대용량이면 .gitignore로 제외) |
| `data/processed/` | 전처리·병합된 **정제 데이터**. 추천 모듈 입력용. |
| `data/interim/` | 중간 산출물 (선택). |

## docs/

- `workflow.md` — **전체 워크플로우·Phase별 상세 계획·Mermaid**
- `DIRECTORY.md` — 이 문서 (디렉터리 역할)
- (선택) `scrapable-fields/`, `steam-data-sources.md` — 수집 가능 컬럼·데이터 소스 정리

## scripts/

- Phase 1용 **일회성·배치 스크립트**: 스토어 스크래핑, 공식 API 호출, 전처리 등.
- 예: `scrape_steam_store.py`, `scrape_steam_api.py`, `scrape_steam_full_sample.py`, 전처리 스크립트.
- 실행은 보통 프로젝트 루트에서 `python scripts/...` 또는 `python -m scripts....` 형태로.

## src/game_recommendation/

추천 로직 **패키지**. Phase 2~6에 대응하는 하위 패키지.

| 패키지 | Phase | 역할 |
|--------|-------|------|
| `context_aware/` | 2 | Context-aware: “지금 어떤 게임을 하고 싶은가” 입력·**후보 풀 생성·Top-K Retrieval**. (선택) Top-K 내 LLM/재랭킹. |
| `personalization/` | 3 | Age(출시 시기)·Popularity(인기도) 슬라이더 필터·정렬 |
| `spec_aware/` | 4 | 사양 비교, 성능 여유도·안정성 보정, FinalScore 반영 |
| `price_aware/` | 5 | 할인·가성비·구매 타이밍 보조 |
| `api/` | 6 | 통합 추천 API (Retrieval → Top-K → (선택) 재랭킹 → 응답) |

- 각 하위 패키지는 `__init__.py` 로 모듈 노출.
- 상위에서 `from game_recommendation.context_aware import ...` 형태로 import.

## tests/

- 단위·통합 테스트.
- `tests/test_*.py` 또는 `tests/context_aware/`, `tests/api/` 등 Phase별로 구분해도 됨.

---

## 워크플로우와의 대응

```
Phase 0 → config/, docs/, requirements.txt
Phase 1 → scripts/, data/raw/, data/processed/
Phase 2 → src/game_recommendation/context_aware/  (후보 풀·Top-K Retrieval, 선택 시 Top-K 내 LLM)
Phase 3 → src/game_recommendation/personalization/
Phase 4 → src/game_recommendation/spec_aware/
Phase 5 → src/game_recommendation/price_aware/
Phase 6 → src/game_recommendation/api/, 통합
```

- **Retrieval-first:** 컨텍스트 → 후보 풀 → Top-K → (선택) Top-K 내 비교/LLM → 최종 추천. LLM은 “컨텍스트 직접 입력”이 아닌 “Top-K 후보에 대한 비교·재랭킹”에만 사용.

테스트는 각 Phase별 코드에 맞춰 `tests/` 에 추가하면 됩니다.
