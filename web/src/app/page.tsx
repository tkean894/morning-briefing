import { auth } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchMe } from "@/lib/api";
import { ApiUnavailable } from "@/components/ApiUnavailable";

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
  let me;
  try {
    me = token ? await fetchMe(token) : null;
  } catch {
    return <ApiUnavailable />;
  }

  if (!me?.onboarding_completed) {
    redirect("/onboarding");
  }

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-6 py-16">
      <div className="mb-10 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-neutral-900">
          Good morning
        </h1>
        <UserButton />
      </div>
      <div className="rounded-3xl border border-neutral-200 bg-white p-8 shadow-sm">
        <p className="text-neutral-500">
          Your daily briefing pipeline isn&apos;t built yet &mdash; that&apos;s
          the next phase. For now, here&apos;s what&apos;s saved:
        </p>
        <dl className="mt-6 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-neutral-500">Briefing length</dt>
            <dd className="font-medium text-neutral-900">
              {me.briefing_length_minutes} minutes
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-neutral-500">Audio briefing</dt>
            <dd className="font-medium text-neutral-900">
              {me.audio_enabled ? "Enabled" : "Disabled"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-neutral-500">Interests selected</dt>
            <dd className="font-medium text-neutral-900">
              {me.interest_ids.length}
            </dd>
          </div>
        </dl>
        <Link
          href="/settings/preferences"
          className="mt-8 inline-block text-sm font-medium text-neutral-900 underline underline-offset-4"
        >
          Edit preferences
        </Link>
      </div>
    </div>
  );
}
