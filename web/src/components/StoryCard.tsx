import Link from "next/link";
import type { BriefingStory } from "@/lib/api";
import { categoryAccent, categoryName } from "@/lib/categories";

export function StoryCard({ story }: { story: BriefingStory }) {
  const accent = categoryAccent(story.category);

  return (
    <article
      data-story-id={story.id}
      className="rounded-lg border border-ink/10 bg-white p-6"
      style={{ borderLeft: `3px solid ${accent}` }}
    >
      <p className="text-xs font-medium" style={{ color: accent }}>
        {categoryName(story.category)}
      </p>

      <h3 className="mt-2 font-serif text-xl font-medium text-ink">
        {story.headline}
      </h3>
      <p className="mt-2 text-[15px] leading-relaxed text-ink/70">
        {story.summary}
      </p>

      <div className="mt-4 space-y-2 text-sm text-ink/70">
        <p>
          <span className="font-medium text-ink">Why it matters. </span>
          {story.why_it_matters}
        </p>
        <p>
          <span className="font-medium text-ink">What to watch. </span>
          {story.what_to_watch}
        </p>
      </div>

      {story.is_sensitive && story.perspectives.length > 0 && (
        <div className="mt-4 rounded-md bg-paper p-4">
          <p className="text-sm font-medium text-ink">Different perspectives</p>
          <ul className="mt-2 space-y-1 text-sm text-ink/70">
            {story.perspectives.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-ink/10 pt-4">
        <p className="truncate text-xs text-ink/50">
          {story.sources.map((s) => s.name).join(", ")}
        </p>
        <Link
          href={`/story/${story.id}`}
          className="shrink-0 text-sm font-medium text-ink underline underline-offset-4 hover:text-ink/70"
        >
          Dive deeper
        </Link>
      </div>
    </article>
  );
}
