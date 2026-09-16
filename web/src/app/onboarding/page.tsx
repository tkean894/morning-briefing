import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { fetchInterests, fetchMe, type Interest, type Me } from "@/lib/api";
import { PreferencesForm } from "@/components/PreferencesForm";
import { ApiUnavailable } from "@/components/ApiUnavailable";

export const maxDuration = 30;

export default async function OnboardingPage() {
  const { getToken } = await auth();
  const token = await getToken();
  if (!token) redirect("/sign-in");

  let interests: Interest[];
  let me: Me;
  try {
    [interests, me] = await Promise.all([fetchInterests(), fetchMe(token)]);
  } catch {
    return <ApiUnavailable />;
  }

  if (me.onboarding_completed) redirect("/");

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-16">
      <div className="mb-10 space-y-2">
        <h1 className="font-serif text-2xl font-medium text-ink">
          Let&apos;s set up your briefing
        </h1>
        <p className="text-ink/60">
          Takes about a minute. You can always change this later.
        </p>
      </div>
      <PreferencesForm
        interests={interests}
        initial={me}
        submitLabel="Start my briefing"
        redirectTo="/"
      />
    </div>
  );
}
