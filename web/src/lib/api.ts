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

export type StorySource = { name: string; url: string };

export type BriefingStory = {
  id: number;
  category: string;
  headline: string;
  summary: string;
  why_it_matters: string;
  what_to_watch: string;
  key_facts: string[];
  is_sensitive: boolean;
  perspectives: string[];
  sources: StorySource[];
  inclusion_reason: "must_include" | "personalized";
};

export type Digest = { bullets: string[] };

export type Briefing = {
  date: string;
  briefing_length_minutes: BriefingLength;
  story_count: number;
  estimated_read_minutes: number;
  digest: Digest | null;
  stories: BriefingStory[];
  audio_url: string | null;
  audio_duration_seconds: number | null;
};

export type RelatedStory = { id: number; headline: string; category: string };

export type StoryDetail = {
  id: number;
  category: string;
  headline: string;
  summary: string;
  why_it_matters: string;
  what_to_watch: string;
  key_facts: string[];
  is_sensitive: boolean;
  perspectives: string[];
  sources: StorySource[];
  related: RelatedStory[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Render's free tier can cold-start after inactivity; give it real time to
// wake up rather than hanging until the platform's own request timeout.
const API_TIMEOUT_MS = 25_000;

export async function fetchInterests(): Promise<Interest[]> {
  const res = await fetch(`${API_URL}/interests`, {
    cache: "no-store",
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error("Failed to load interests");
  return res.json();
}

export async function fetchMe(token: string): Promise<Me> {
  const res = await fetch(`${API_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error("Failed to load profile");
  return res.json();
}

export async function fetchBriefing(token: string): Promise<Briefing> {
  const res = await fetch(`${API_URL}/briefings/today`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error("Failed to load briefing");
  return res.json();
}

export class StoryNotFoundError extends Error {}

export async function fetchStory(
  token: string,
  id: number | string
): Promise<StoryDetail> {
  const res = await fetch(`${API_URL}/stories/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
  if (res.status === 404) throw new StoryNotFoundError();
  if (!res.ok) throw new Error("Failed to load story");
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
