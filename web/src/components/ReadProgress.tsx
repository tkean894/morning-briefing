"use client";

import { useEffect, useState } from "react";

// A finite briefing, unlike a feed, can be "finished" -- this tracks how much
// of it the reader has scrolled past so that promise is visible, not just copy.
export function ReadProgress({ total }: { total: number }) {
  const [readCount, setReadCount] = useState(0);

  useEffect(() => {
    if (total === 0) return;

    const targets = document.querySelectorAll("[data-story-id]");
    const read = new Set<string>();

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = entry.target.getAttribute("data-story-id");
          if (!id) continue;
          if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
            read.add(id);
          }
        }
        setReadCount(read.size);
      },
      { rootMargin: "0px 0px -75% 0px", threshold: 0 }
    );

    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [total]);

  if (total === 0) return null;

  return (
    <>
      <div className="pointer-events-none fixed inset-x-0 top-0 z-50 h-0.5 bg-ink/5">
        <div
          className="h-full bg-marigold transition-all duration-300"
          style={{ width: `${Math.min(100, (readCount / total) * 100)}%` }}
        />
      </div>
      <div className="fixed bottom-6 right-6 z-50 rounded-full border border-ink/10 bg-white px-3 py-1.5 text-xs font-medium text-ink/70 shadow-sm">
        {readCount} of {total} read
      </div>
    </>
  );
}
