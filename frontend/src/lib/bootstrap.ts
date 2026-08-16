// Identity comes from the signed-in session (AuthProvider) as of Phase 8
// slice 4 -- this only ensures the two Language rows and the one Course
// row everything else foreign-keys against exist, creating whichever are
// missing. Runs nested inside AuthProvider, so a real user is always
// signed in by the time this fires.

import { api, ApiError } from "./api/client";
import { coursesApi } from "./api/courses";
import { languagesApi } from "./api/languages";
import { clearBootstrapCache, readBootstrapCache, writeBootstrapCache } from "./storage";

export interface BootstrapResult {
  courseId: string;
  baseLanguageId: string;
  targetLanguageId: string;
}

async function cacheIsStillValid(cached: BootstrapResult): Promise<boolean> {
  try {
    await api.get(`/courses/${cached.courseId}`);
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

  const result: BootstrapResult = {
    courseId: course.id,
    baseLanguageId: english.id,
    targetLanguageId: spanish.id,
  };
  writeBootstrapCache(result);
  return result;
}
