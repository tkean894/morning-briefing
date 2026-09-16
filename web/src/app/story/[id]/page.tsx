import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { fetchStory, StoryNotFoundError } from "@/lib/api";
import { ApiUnavailable } from "@/components/ApiUnavailable";
import { categoryAccent, categoryName } from "@/lib/categories";

export const maxDuration = 30;

export default async function StoryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { getToken } = await auth();
  const token = await getToken();
  if (!token) redirect("/sign-in");

  let story;
  try {
    story = await fetchStory(token, id);
  } catch (err) {
    if (err instanceof StoryNotFoundError) {
      notFound();
    }
    return <ApiUnavailable />;
  }

  const accent = categoryAccent(story.category);

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-6 py-12">
      <Link
        href="/"
        className="text-sm font-medium text-ink/50 hover:text-ink"
      >
        &larr; Back to your brief
      </Link>

      <p className="mt-6 text-sm font-medium" style={{ color: accent }}>
        {categoryName(story.category)}
      </p>

      <h1 className="mt-2 font-serif text-2xl font-medium text-ink">
        {story.headline}
      </h1>
      <p className="mt-4 text-[15px] leading-relaxed text-ink/70">
        {story.summary}
      </p>

      <div
        className="mt-8 rounded-lg border border-ink/10 p-6"
        style={{ borderLeft: `3px solid ${accent}` }}
      >
        <h2 className="font-serif text-lg font-medium text-ink">
          Key facts
        </h2>
        <ul className="mt-3 space-y-2 text-sm text-ink/70">
          {story.key_facts.map((fact, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-ink/30">&mdash;</span>
              <span>{fact}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-8 space-y-6">
        <div>
          <h2 className="font-serif text-lg font-medium text-ink">
            Why it matters
          </h2>
          <p className="mt-2 text-[15px] text-ink/70">
            {story.why_it_matters}
          </p>
        </div>
        <div>
          <h2 className="font-serif text-lg font-medium text-ink">
            What to watch
          </h2>
          <p className="mt-2 text-[15px] text-ink/70">
            {story.what_to_watch}
          </p>
        </div>
      </div>

      {story.is_sensitive && story.perspectives.length > 0 && (
        <div className="mt-8 rounded-lg border border-ink/10 bg-paper p-5">
          <h2 className="font-serif text-lg font-medium text-ink">
            Different perspectives
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-ink/70">
            {story.perspectives.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8">
        <h2 className="font-serif text-lg font-medium text-ink">Sources</h2>
        <ul className="mt-3 space-y-2">
          {story.sources.map((source) => (
            <li key={source.url}>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-ink underline underline-offset-4 hover:text-ink/70"
              >
                {source.name}
              </a>
            </li>
          ))}
        </ul>
      </div>

      {story.related.length > 0 && (
        <div className="mt-10 border-t border-ink/10 pt-8">
          <h2 className="font-serif text-lg font-medium text-ink">
            Related coverage
          </h2>
          <ul className="mt-3 space-y-2">
            {story.related.map((r) => (
              <li key={r.id}>
                <Link
                  href={`/story/${r.id}`}
                  className="text-sm font-medium text-ink/70 hover:text-ink"
                >
                  {r.headline}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
