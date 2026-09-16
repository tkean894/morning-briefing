"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { BriefingLength, Interest, Me } from "@/lib/api";
import { putPreferences } from "@/lib/api";

const LENGTH_OPTIONS: BriefingLength[] = [5, 10, 15, 20];

export function PreferencesForm({
  interests,
  initial,
  submitLabel,
  redirectTo,
}: {
  interests: Interest[];
  initial?: Me;
  submitLabel: string;
  redirectTo: string;
}) {
  const { getToken } = useAuth();
  const router = useRouter();
  const [selected, setSelected] = useState<Set<number>>(
    new Set(initial?.interest_ids ?? [])
  );
  const [length, setLength] = useState<BriefingLength>(
    initial?.briefing_length_minutes ?? 10
  );
  const [audioEnabled, setAudioEnabled] = useState(
    initial?.audio_enabled ?? true
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      await putPreferences(token, {
        interest_ids: Array.from(selected),
        briefing_length_minutes: length,
        audio_enabled: audioEnabled,
      });
      router.push(redirectTo);
      router.refresh();
    } catch {
      setError("Something went wrong saving your preferences. Try again.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-2xl space-y-10">
      <section className="space-y-4">
        <h2 className="font-serif text-lg font-medium text-ink">
          What do you want to follow?
        </h2>
        <p className="text-sm text-ink/60">
          Pick as many broad topics as you like. We&apos;ll still surface
          major stories outside these when they really matter.
        </p>
        <div className="space-y-5">
          {interests.map((broad) => (
            <div key={broad.id} className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-ink/80">
                <input
                  type="checkbox"
                  checked={selected.has(broad.id)}
                  onChange={() => toggle(broad.id)}
                  className="h-4 w-4 rounded border-ink/25"
                />
                {broad.name}
              </label>
              {broad.children.length > 0 && selected.has(broad.id) && (
                <div className="ml-6 flex flex-wrap gap-2">
                  {broad.children.map((child) => (
                    <label
                      key={child.id}
                      className={`cursor-pointer rounded-full border px-3 py-1 text-xs transition ${
                        selected.has(child.id)
                          ? "border-ink bg-ink text-paper"
                          : "border-ink/15 text-ink/60 hover:border-ink/40"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selected.has(child.id)}
                        onChange={() => toggle(child.id)}
                        className="hidden"
                      />
                      {child.name}
                    </label>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-serif text-lg font-medium text-ink">
          How long should your briefing be?
        </h2>
        <div className="flex gap-3">
          {LENGTH_OPTIONS.map((option) => (
            <button
              type="button"
              key={option}
              onClick={() => setLength(option)}
              className={`rounded-md border px-4 py-3 text-sm font-medium transition ${
                length === option
                  ? "border-ink bg-ink text-paper"
                  : "border-ink/15 text-ink/60 hover:border-ink/40"
              }`}
            >
              {option} min
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-medium text-ink/80">
          <input
            type="checkbox"
            checked={audioEnabled}
            onChange={(e) => setAudioEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-ink/25"
          />
          Include an audio version of my briefing
        </label>
      </section>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-ink px-4 py-3 text-sm font-medium text-paper transition hover:bg-ink/85 disabled:opacity-50"
      >
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
