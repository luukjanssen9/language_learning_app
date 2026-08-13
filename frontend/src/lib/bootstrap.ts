// No auth in v1 -- "single-user, assumed" per CLAUDE.md, meaning the person
// should never see a signup/setup screen. This silently ensures the one
// User row, the two Language rows, and the one Course row everything else
// foreign-keys against all exist, creating only whichever are missing.

import { api, ApiError } from "./api/client";
import { coursesApi } from "./api/courses";
import { languagesApi } from "./api/languages";
import { usersApi } from "./api/users";
import { clearBootstrapCache, readBootstrapCache, writeBootstrapCache } from "./storage";

export interface BootstrapResult {
  userId: string;
  courseId: string;
  baseLanguageId: string;
  targetLanguageId: string;
}

// Placeholder, not the developer's real address: nothing in this app's UI
// ever surfaces the email, and this repo is public -- no reason to put a
// real one in source.
const DEFAULT_USER_EMAIL = "you@example.com";
const DEFAULT_USER_DISPLAY_NAME = "Learner";

async function cacheIsStillValid(cached: BootstrapResult): Promise<boolean> {
  try {
    await api.get(`/users/${cached.userId}`);
    return true;
  } catch (err) {
    // Any failure other than a confirmed 404 (network hiccup, backend
    // momentarily down) shouldn't nuke a perfectly good cache -- only a
    // definite "this row is gone" should trigger rediscovery.
    return !(err instanceof ApiError && err.status === 404);
  }
}

export async function ensureBootstrap(): Promise<BootstrapResult> {
  const cached = readBootstrapCache();
  if (cached && (await cacheIsStillValid(cached))) return cached;
  if (cached) clearBootstrapCache(); // stale -- e.g. the dev DB got reset

  const languages = await languagesApi.list();
  const english =
    languages.find((l) => l.code === "en") ??
    (await languagesApi.create({ code: "en", name: "English" }));
  const spanish =
    languages.find((l) => l.code === "es") ??
    (await languagesApi.create({ code: "es", name: "Spanish" }));

  const courses = await coursesApi.list();
  const course =
    courses.find(
      (c) => c.base_language_id === english.id && c.target_language_id === spanish.id,
    ) ??
    (await coursesApi.create({
      base_language_id: english.id,
      target_language_id: spanish.id,
      name: "English to Spanish",
      slug: "en-es",
    }));

  const users = await usersApi.list();
  const user =
    users[0] ??
    (await usersApi.create({
      email: DEFAULT_USER_EMAIL,
      display_name: DEFAULT_USER_DISPLAY_NAME,
    }));

  const result: BootstrapResult = {
    userId: user.id,
    courseId: course.id,
    baseLanguageId: english.id,
    targetLanguageId: spanish.id,
  };
  writeBootstrapCache(result);
  return result;
}
