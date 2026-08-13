import { api } from "./client";
import type { Skill } from "./types";

export const skillsApi = {
  list: (courseId: string) =>
    api.get<Skill[]>(`/skills?${new URLSearchParams({ course_id: courseId })}`),
};
