import { auth, currentUser } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchBriefing, fetchMe } from "@/lib/api";
import { ApiUnavailable } from "@/components/ApiUnavailable";
import { StoryCard } from "@/components/StoryCard";
import { ReadProgress } from "@/components/ReadProgress";
import { categoryAccent, categoryName } from "@/lib/categories";
import { formatBriefingDate } from "@/lib/format";

export const maxDuration = 30;

export default async function Home() {
  const { userId, getToken } = await auth();

  if (!userId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <p className="font-serif text-lg text-ink/60">Morning Briefs</p>
        <h1 className="mt-4 max-w-xl font-serif text-4xl font-medium text-ink">
          Know what matters today, in ten minutes.
        </h1>
        <p className="mt-4 max-w-md text-ink/60">
          One finite, personalized briefing every morning &mdash; markets,
          tech, and the news you actually need. No feed, no clutter.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/sign-up"
            className="rounded-md bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:bg-ink/85"
          >
            Get started
          </Link>
          <Link
            href="/sign-in"
            className="rounded-md border border-ink/15 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/40"
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
      <ReadProgress total={briefing.story_count} />

      <div className="mb-10 flex items-start justify-between">
        <div>
          <p className="text-sm text-ink/50">
            {formatBriefingDate(briefing.date)}
          </p>
          <h1 className="mt-1 font-serif text-3xl font-medium text-ink">
            Good morning, {firstName}
          </h1>
          {briefing.story_count > 0 ? (
            <p className="mt-3 text-ink/60">
              {briefing.story_count} stories today, about{" "}
              {Math.max(1, Math.round(briefing.estimated_read_minutes))}{" "}
              minutes to read.
            </p>
          ) : (
            <p className="mt-3 text-ink/60">
              Today&apos;s briefing isn&apos;t ready yet &mdash; check back
              shortly.
            </p>
          )}
        </div>
        <UserButton />
      </div>

      {briefing.story_count > 0 && (
        <div className="mb-10 flex flex-wrap gap-3">
          <a
            href="#briefing"
            className="rounded-md bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:bg-ink/85"
          >
            Start reading
          </a>
          <Link
            href="/settings/preferences"
            className="rounded-md border border-ink/15 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/40"
          >
            Edit preferences
          </Link>
        </div>
      )}

      {briefing.digest && briefing.digest.bullets.length > 0 && (
        <section className="mb-10 border-t border-ink/10 pt-6">
          <h2 className="font-serif text-lg font-medium text-ink">
            Today in 30 seconds
          </h2>
          <ul className="mt-3 space-y-2">
            {briefing.digest.bullets.map((bullet, i) => (
              <li key={i} className="flex gap-2 text-[15px] text-ink/70">
                <span className="text-ink/30">&mdash;</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {categories.length > 0 && (
        <section id="briefing" className="space-y-10 scroll-mt-6">
          {categories.map(({ slug, stories }) => {
            const accent = categoryAccent(slug);
            return (
              <div key={slug}>
                <h2
                  className="border-t pt-3 text-sm font-semibold"
                  style={{ borderColor: accent, color: accent }}
                >
                  {categoryName(slug)}
                </h2>
                <div className="mt-4 space-y-4">
                  {stories.map((story) => (
                    <StoryCard key={story.id} story={story} />
                  ))}
                </div>
              </div>
            );
          })}
        </section>
      )}

      {briefing.story_count > 0 && (
        <p className="mt-16 text-center font-serif text-lg text-ink/40">
          You&apos;re caught up.
        </p>
      )}
    </div>
  );
}
