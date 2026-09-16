import { auth, currentUser } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchBriefing, fetchMe } from "@/lib/api";
import { ApiUnavailable } from "@/components/ApiUnavailable";
import { StoryCard } from "@/components/StoryCard";
import { categoryColor, categoryName } from "@/lib/categories";
import { formatBriefingDate } from "@/lib/format";

export const maxDuration = 30;

export default async function Home() {
  const { userId, getToken } = await auth();

  if (!userId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <p className="mb-3 text-sm font-medium uppercase tracking-wide text-neutral-400">
          Morning Briefs
        </p>
        <h1 className="max-w-xl text-4xl font-semibold text-neutral-900">
          Know what matters today in 10 minutes.
        </h1>
        <p className="mt-4 max-w-md text-neutral-500">
          One finite, personalized briefing every morning &mdash; markets,
          tech, and the news you actually need. No feed, no clutter.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/sign-up"
            className="rounded-2xl bg-neutral-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-neutral-700"
          >
            Get started
          </Link>
          <Link
            href="/sign-in"
            className="rounded-2xl border border-neutral-200 px-5 py-3 text-sm font-medium text-neutral-700 transition hover:border-neutral-400"
          >
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  const token = await getToken();
  if (!token) redirect("/sign-in");

  let me;
  try {
    me = await fetchMe(token);
  } catch {
    return <ApiUnavailable />;
  }
  if (!me.onboarding_completed) redirect("/onboarding");

  let briefing;
  try {
    briefing = await fetchBriefing(token);
  } catch {
    return <ApiUnavailable />;
  }

  const user = await currentUser();
  const firstName = user?.firstName ?? "there";

  const categories: { slug: string; stories: typeof briefing.stories }[] = [];
  for (const story of briefing.stories) {
    const group = categories.find((c) => c.slug === story.category);
    if (group) {
      group.stories.push(story);
    } else {
      categories.push({ slug: story.category, stories: [story] });
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-6 py-12">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <p className="text-sm text-neutral-500">
            {formatBriefingDate(briefing.date)}
          </p>
          <h1 className="mt-1 text-3xl font-semibold text-neutral-900">
            Good morning, {firstName}
          </h1>
        </div>
        <UserButton />
      </div>

      <section className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm shadow-neutral-200/50">
        <p className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Your Morning Brief
        </p>
        {briefing.story_count > 0 ? (
          <>
            <p className="mt-2 text-neutral-600">
              {Math.max(1, Math.round(briefing.estimated_read_minutes))} min
              read &bull; {briefing.story_count} stories
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a
                href="#briefing"
                className="rounded-2xl bg-neutral-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-neutral-700"
              >
                Start Reading
              </a>
              <Link
                href="/settings/preferences"
                className="rounded-2xl border border-neutral-200 px-5 py-3 text-sm font-medium text-neutral-700 transition hover:border-neutral-400"
              >
                Edit preferences
              </Link>
            </div>
          </>
        ) : (
          <p className="mt-2 text-neutral-500">
            Today&apos;s briefing isn&apos;t ready yet &mdash; check back
            shortly.
          </p>
        )}
      </section>

      {briefing.digest && briefing.digest.bullets.length > 0 && (
        <section className="mt-10">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Today in 30 Seconds
          </h2>
          <ul className="mt-3 space-y-2">
            {briefing.digest.bullets.map((bullet, i) => (
              <li key={i} className="flex gap-2 text-[15px] text-neutral-700">
                <span className="text-neutral-300">&bull;</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {categories.length > 0 && (
        <section id="briefing" className="mt-12 space-y-10 scroll-mt-6">
          {categories.map(({ slug, stories }) => (
            <div key={slug}>
              <h2
                className={`inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${categoryColor(
                  slug
                )}`}
              >
                {categoryName(slug)}
              </h2>
              <div className="mt-4 space-y-4">
                {stories.map((story) => (
                  <StoryCard key={story.id} story={story} />
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {briefing.story_count > 0 && (
        <p className="mt-16 text-center text-lg font-medium text-neutral-400">
          You&apos;re caught up.
        </p>
      )}
    </div>
  );
}
