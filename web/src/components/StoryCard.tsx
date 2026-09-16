import Link from "next/link";
import type { BriefingStory } from "@/lib/api";
import { categoryColor, categoryName } from "@/lib/categories";

export function StoryCard({ story }: { story: BriefingStory }) {
  return (
    <article className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm shadow-neutral-200/50">
      <span
        className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${categoryColor(
          story.category
        )}`}
      >
        {categoryName(story.category)}
      </span>

      <h3 className="mt-3 text-lg font-semibold text-neutral-900">
        {story.headline}
      </h3>
      <p className="mt-2 text-[15px] leading-relaxed text-neutral-600">
        {story.summary}
      </p>

      <dl className="mt-4 space-y-2 text-sm">
        <div>
          <dt className="inline font-medium text-neutral-800">
            Why it matters:{" "}
          </dt>
          <dd className="inline text-neutral-600">{story.why_it_matters}</dd>
        </div>
        <div>
          <dt className="inline font-medium text-neutral-800">
            What to watch:{" "}
          </dt>
          <dd className="inline text-neutral-600">{story.what_to_watch}</dd>
        </div>
      </dl>

      {story.is_sensitive && story.perspectives.length > 0 && (
        <div className="mt-4 rounded-2xl bg-neutral-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
            Different perspectives
          </p>
          <ul className="mt-2 space-y-1 text-sm text-neutral-600">
            {story.perspectives.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between gap-3">
        <p className="truncate text-xs text-neutral-400">
          {story.sources.map((s) => s.name).join(" · ")}
        </p>
        <Link
          href={`/story/${story.id}`}
          className="shrink-0 text-sm font-medium text-neutral-900 underline underline-offset-4"
        >
          Dive Deeper
        </Link>
      </div>
    </article>
  );
}
