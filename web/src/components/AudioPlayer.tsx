"use client";

import { useState } from "react";

export function AudioPlayer({ audioUrl }: { audioUrl: string }) {
  const [expanded, setExpanded] = useState(false);

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="rounded-md border border-ink/15 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/40"
      >
        Listen to brief
      </button>
    );
  }

  return (
    <audio controls autoPlay src={audioUrl} className="h-11 w-full max-w-xs">
      Your browser does not support the audio element.
    </audio>
  );
}
