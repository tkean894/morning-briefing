import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { fetchInterests, fetchMe } from "@/lib/api";
import { PreferencesForm } from "@/components/PreferencesForm";

export default async function PreferencesSettingsPage() {
  const { getToken } = await auth();
  const token = await getToken();
  if (!token) redirect("/sign-in");

  const [interests, me] = await Promise.all([
    fetchInterests(),
    fetchMe(token),
  ]);

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-16">
      <div className="mb-10 space-y-2">
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
        redirectTo="/settings/preferences"
      />
    </div>
  );
}
