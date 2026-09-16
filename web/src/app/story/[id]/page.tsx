import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { fetchStory, StoryNotFoundError } from "@/lib/api";
import { ApiUnavailable } from "@/components/ApiUnavailable";
import { categoryColor, categoryName } from "@/lib/categories";

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

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-6 py-12">
      <Link
        href="/"
        className="text-sm font-medium text-neutral-500 hover:text-neutral-900"
      >
        &larr; Back to your brief
      </Link>

      <span
        className={`mt-6 inline-block rounded-full px-3 py-1 text-xs font-medium ${categoryColor(
          story.category
        )}`}
      >
        {categoryName(story.category)}
      </span>

      <h1 className="mt-3 text-2xl font-semibold text-neutral-900">
        {story.headline}
      </h1>
      <p className="mt-4 text-[15px] leading-relaxed text-neutral-600">
        {story.summary}
      </p>

      <div className="mt-8 rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm shadow-neutral-200/50">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Key Facts
        </h2>
        <ul className="mt-3 space-y-2 text-sm text-neutral-700">
          {story.key_facts.map((fact, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-neutral-300">&bull;</span>
              <span>{fact}</span>
            </li>
          ))}
        </ul>
      </div>

      <dl className="mt-8 space-y-6">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Why It Matters
          </dt>
          <dd className="mt-2 text-[15px] text-neutral-700">
            {story.why_it_matters}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            What to Watch
          </dt>
          <dd className="mt-2 text-[15px] text-neutral-700">
            {story.what_to_watch}
          </dd>
        </div>
      </dl>

      {story.is_sensitive && story.perspectives.length > 0 && (
        <div className="mt-8 rounded-2xl bg-neutral-50 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
            Different Perspectives
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-neutral-700">
            {story.perspectives.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Sources
        </h2>
        <ul className="mt-3 space-y-2">
          {story.sources.map((source) => (
            <li key={source.url}>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-neutral-900 underline underline-offset-4"
              >
                {source.name}
              </a>
            </li>
          ))}
        </ul>
      </div>

      {story.related.length > 0 && (
        <div className="mt-10 border-t border-neutral-200 pt-8">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Related Coverage
          </h2>
          <ul className="mt-3 space-y-2">
            {story.related.map((r) => (
              <li key={r.id}>
                <Link
                  href={`/story/${r.id}`}
                  className="text-sm font-medium text-neutral-700 hover:text-neutral-900"
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
