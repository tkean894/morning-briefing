export type Interest = {
  id: number;
  slug: string;
  name: string;
  children: Interest[];
};

export type BriefingLength = 5 | 10 | 15 | 20;

export type Me = {
  onboarding_completed: boolean;
  briefing_length_minutes: BriefingLength;
  audio_enabled: boolean;
  interest_ids: number[];
};

export type PreferencesInput = {
  interest_ids: number[];
  briefing_length_minutes: BriefingLength;
  audio_enabled: boolean;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchInterests(): Promise<Interest[]> {
  const res = await fetch(`${API_URL}/interests`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load interests");
  return res.json();
}

export async function fetchMe(token: string): Promise<Me> {
  const res = await fetch(`${API_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load profile");
  return res.json();
}

export async function putPreferences(
  token: string,
  body: PreferencesInput
): Promise<Me> {
  const res = await fetch(`${API_URL}/preferences`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to save preferences");
  return res.json();
}
