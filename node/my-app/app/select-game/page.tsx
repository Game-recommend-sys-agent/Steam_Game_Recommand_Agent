"use client";

import { useState } from "react";
import GameCard from "./GameCard";

type Game = {
  id: number;
  name: string;
  image: string;
  genres: string[];
  price: number;
};

const ITEMS_PER_PAGE = 5;

/* 🔥 30개 더미 데이터 */
const mockGames: Game[] = Array.from({ length: 30 }, (_, i) => ({
  id: i + 1,
  name: `추천 게임 ${i + 1}`,
  image: `/images/sample${(i % 5) + 1}.jpg`,
  genres:
    i % 3 === 0
      ? ["RPG", "스토리"]
      : i % 3 === 1
      ? ["액션", "어드벤처"]
      : ["시뮬레이션", "캐주얼"],
  price:
    i % 4 === 0
      ? 0
      : 5900 + (i % 5) * 5000,
}));

export default function SelectGamePage() {
  const [page, setPage] = useState(0);

  const totalPages = Math.ceil(mockGames.length / ITEMS_PER_PAGE);

  const startIndex = page * ITEMS_PER_PAGE;
  const currentGames = mockGames.slice(
    startIndex,
    startIndex + ITEMS_PER_PAGE
  );

  const goPrev = () => {
    if (page > 0) setPage((prev) => prev - 1);
  };

  const goNext = () => {
    if (page < totalPages - 1) setPage((prev) => prev + 1);
  };

  return (
    <div className="page">
      {/* 🔥 여기 클래스 변경 */}
      <div className="select-container">
        <h1 className="title">
          우리 중 <span className="title-accent">누구</span>랑 놀래?
        </h1>

        {/* 🔥 grid 래퍼 추가 (가로 폭 제어용) */}
        <div className="game-grid-wrapper">
          <div className="game-grid">
            {currentGames.map((game) => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        </div>

        <div className="pagination">
          {page > 0 ? (
            <div
              className="triangle-btn triangle-left"
              onClick={goPrev}
            />
          ) : (
            <div style={{ width: 60 }} />
          )}

          <div className="page-indicator">
            {page + 1} / {totalPages}
          </div>

          {page < totalPages - 1 ? (
            <div
              className="triangle-btn triangle-right"
              onClick={goNext}
            />
          ) : (
            <div style={{ width: 60 }} />
          )}
        </div>
      </div>
    </div>
  );
}