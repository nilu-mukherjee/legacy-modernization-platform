"use client";

import { useEffect, useState } from "react";

const CARDS = [
  { label: "Code Health",         score: 72, color: "#22c55e", delay: 500 },
  { label: "Modernization Score", score: 45, color: "#f97316", delay: 700 },
  { label: "Dependency Risk",     score: 28, color: "#ef4444", delay: 900 },
];

function AnimatedNumber({ target, color, active }: { target: number; color: string; active: boolean }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!active) return;
    let frame: number;
    let start: number | null = null;
    const duration = 2800;

    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      setCount(Math.round(eased * target));
      if (progress < 1) frame = requestAnimationFrame(step);
    };

    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [active, target]);

  return <span style={{ color }}>{count}</span>;
}

export function ScoreCards() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 300);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="grid grid-cols-3 gap-3">
      {CARDS.map((card) => (
        <div
          key={card.label}
          className="glass rounded-xl p-3 text-center"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(10px)",
            transition: `opacity 0.9s ease ${card.delay}ms, transform 0.9s ease ${card.delay}ms`,
          }}
        >
          <div className="text-2xl font-extrabold">
            <AnimatedNumber target={card.score} color={card.color} active={visible} />
          </div>
          <div className="mt-1 text-[10px] leading-tight text-muted-foreground">
            {card.label}
          </div>
        </div>
      ))}
    </div>
  );
}
