"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  /* ======================
     State
  ====================== */
  const [prompt, setPrompt] = useState("");
  const [age, setAge] = useState<number | null>(null);
  const [price, setPrice] = useState<string | null>(null);
  const [os, setOs] = useState<string | null>(null);
  const [spec, setSpec] = useState<string | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [showMore, setShowMore] = useState(false);
  const router = useRouter();

  const toggleGenre = (g: string) => {
    setGenres((prev) =>
      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]
    );
  };

  const isActive = (a: any, b: any) => a === b;

  /* ======================
     UI
  ====================== */
  return (
    <main className="page">
      <section className="container">
        {/* ===== Title ===== */}
        <h1 className="title">
  오늘 같이 놀 <span className="title-accent">캐릭터는?</span>
</h1>

<p className="subtitle">
  ----- 기분, 관계, 분위기로 고르는 게임 -----
</p>

        {/* ===== Prompt ===== */}
        <div className="prompt-box">
          <textarea
            placeholder={`네가 만나고 싶은 친구는 누구야?`}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
          />
        </div>

        {/* ===== Filter Card ===== */}
        <div className="filter-card">
          {/* 장르 */}
          <FilterSection title="🎮 장르">
            {[
              "액션",
              "RPG",
              "전략",
              "시뮬레이션",
              "스토리 중심",
              "퍼즐",
              "온라인",
              "제작",
            ].map((g) => (
              <PillButton
                key={g}
                active={genres.includes(g)}
                onClick={() => toggleGenre(g)}
              >
                {g}
              </PillButton>
            ))}
          </FilterSection>

          {/* 가격 */}
          <FilterSection title="💰 가격">
            {[
              { label: "모든 가격", value: null },
              { label: "1만원 미만", value: "<10000" },
              { label: "1~3만원", value: "10000-30000" },
              { label: "3만원 이상", value: ">=30000" },
            ].map((o) => (
              <PillButton
                key={o.label}
                active={isActive(price, o.value)}
                onClick={() => setPrice(o.value)}
              >
                {o.label}
              </PillButton>
            ))}
          </FilterSection>

          {/* 연령 */}
          <FilterSection title="👶 연령">
            {[
              { label: "전체", value: null },
              { label: "7세 이상", value: 7 },
              { label: "12세 이상", value: 12 },
              { label: "15세 이상", value: 15 },
              { label: "18세 이상", value: 18 },
            ].map((o) => (
              <PillButton
                key={o.label}
                active={isActive(age, o.value)}
                onClick={() => setAge(o.value)}
              >
                {o.label}
              </PillButton>
            ))}
          </FilterSection>

          {/* 추가 조건 */}
          {showMore && (
            <>
              <FilterSection title="💻 OS">
                {["windows", "mac", "linux"].map((v) => (
                  <PillButton
                    key={v}
                    active={isActive(os, v)}
                    onClick={() => setOs(v)}
                  >
                    {v}
                  </PillButton>
                ))}
              </FilterSection>

              <FilterSection title="⚙️ 사양">
                {[
                  { label: "저사양", value: "low" },
                  { label: "중사양", value: "mid" },
                  { label: "고사양", value: "high" },
                ].map((o) => (
                  <PillButton
                    key={o.label}
                    active={isActive(spec, o.value)}
                    onClick={() => setSpec(o.value)}
                  >
                    {o.label}
                  </PillButton>
                ))}
              </FilterSection>
            </>
          )}

          {/* 조건 토글 */}
          <button
            type="button"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              marginTop: "10px",
              color: "#a67c00",
            }}
            onClick={() => setShowMore(!showMore)}
          >
            {showMore ? "조건 접기 ▲" : "조건 더 설정하기 ▼"}
          </button>
        </div>

        {/* ===== CTA ===== */}
        <button
  className="cta"
  onClick={() => router.push("/loading-page")}
>
  여행 떠나기
</button>
      </section>
    </main>
  );
}

/* ======================
   Components
====================== */

function FilterSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="filter-section">
      <div className="filter-title">{title}</div>
      <div className="pill-container">{children}</div>
    </div>
  );
}

function PillButton({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`pill ${active ? "active" : ""}`}
    >
      {children}
    </button>
  );
}