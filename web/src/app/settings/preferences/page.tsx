import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchInterests, fetchMe, type Interest, type Me } from "@/lib/api";
import { PreferencesForm } from "@/components/PreferencesForm";
import { ApiUnavailable } from "@/components/ApiUnavailable";

export const maxDuration = 30;

export default async function PreferencesSettingsPage() {
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

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-16">
      <Link
        href="/"
        className="text-sm font-medium text-neutral-500 hover:text-neutral-900"
      >
        &larr; Back to your brief
      </Link>
      <div className="mt-6 mb-10 space-y-2">
        <h1 className="text-2xl font-semibold text-neutral-900">
          Briefing preferences
        </h1>
        <p className="text-neutral-500">
          Update your interests and briefing length any time.
        </p>
      </div>
      <PreferencesForm
        interests={interests}
        initial={me}
        submitLabel="Save changes"
        redirectTo="/"
      />
    </div>
  );
}
