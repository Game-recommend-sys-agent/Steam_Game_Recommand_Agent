"use client";

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import GameCard, { Game } from "../../select-game/GameCard";

/* 임시 mock */
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
  price: i % 4 === 0 ? 0 : 9900 + (i % 5) * 5000,
  os: "Windows",
  steamUrl: "https://store.steampowered.com/",
}));

function formatPrice(price: number) {
  return price === 0 ? "무료" : `₩ ${price.toLocaleString()}`;
}

export default function ResultDetailPage() {
  const router = useRouter(); // ✅ 여기로 이동
  const params = useParams();
  const routeId = Number(params?.id ?? 1);

  const initialGame =
    mockGames.find((g) => g.id === routeId) ?? mockGames[0];

  const [activeId] = useState<number>(initialGame.id);

  const activeGame = useMemo(() => {
    return mockGames.find((g) => g.id === activeId) ?? mockGames[0];
  }, [activeId]);

  const extraGames = useMemo(() => {
    return mockGames
      .filter((g) => g.id !== activeGame.id)
      .slice(0, 2);
  }, [activeGame.id]);

  const handleGoSteam = () => {
    const url =
      activeGame.steamUrl ?? "https://store.steampowered.com/";
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="page">
      <div className="select-container">

        {/* 🔁 Restart Bubble */}
        <button
          className="restart-bubble"
          onClick={() => router.push("/")}
        >
          처음부터 다시 해 볼래?
        </button>

        <div className="result-layout">

          {/* ================= LEFT ================= */}
          <section className="result-left">

            <div className="main-title-box">
              부담없이 가볍게 같이 놀기 좋은 친구야
            </div>

            <div
              className="main-frame clickable"
              onClick={handleGoSteam}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ")
                  handleGoSteam();
              }}
            >
              <div className="main-poster">
                <img
                  src={activeGame.image}
                  alt={activeGame.name}
                  draggable={false}
                />
              </div>
            </div>

            <div className="main-meta-box">
              <div className="main-meta-row">
                <div className="meta-pill">
                  {activeGame.genres.slice(0, 2).join(" · ")}
                </div>
                <div className="meta-pill">
                  {formatPrice(activeGame.price)}
                </div>
                <div className="meta-pill">
                  {activeGame.os}
                </div>
              </div>
            </div>

            <button
              className="main-play-btn"
              onClick={handleGoSteam}
            >
              이 친구랑 놀기 →
            </button>

          </section>

          {/* ================= RIGHT ================= */}
          <aside className="result-right">

            <div className="side-header-box">
              이 친구는 어때?
            </div>

            <div className="game-grid">
              {extraGames.map((g) => (
                <GameCard key={g.id} game={g} />
              ))}
            </div>

          </aside>

        </div>
      </div>
    </div>
  );
}