"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoadingPage() {
  const router = useRouter();

  const steps = [
    { icon: "👀", text: "어디서 놀 수 있는지 먼저 살펴보는 중…" },
    { icon: "💻", text: "무리 없이 즐길 수 있는지 살짝 체크 중이야" },
    { icon: "✨", text: "분위기랑 장르가 잘 맞는지 비교하고 있어" },
    { icon: "🔍", text: "느낌이 비슷한 캐릭터를 발견했어!" },
  ];

  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
      }, 900);

      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  return (
    <main className="loading-page">
      <div className="loading-card">
        <h1 className="title">
          <span className="title-accent">추천을 만들고 있어!</span>
        </h1>

        <ul className="loading-list">
          {steps.map((step, index) => (
            <li
              key={index}
              className={`loading-item ${
                index === currentStep ? "active" : ""
              } ${index < currentStep ? "done" : ""}`}
            >
              <span className="loading-dot" />
              <span>{step.icon}</span>
              <span>{step.text}</span>
            </li>
          ))}
        </ul>

        {currentStep >= steps.length && (
          <button
            className="loading-final-btn"
            onClick={() => router.push("/select-game")}
          >
            이제 보여줄게!
          </button>
        )}
      </div>

      <button
        className="restart-btn"
        onClick={() => router.push("/")}
      >
        처음부터 다시하기
      </button>
    </main>
  );
}