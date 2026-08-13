import { api } from "./client";
import type { Course, CourseCreatePayload } from "./types";

export const coursesApi = {
  list: () => api.get<Course[]>("/courses"),
  create: (payload: CourseCreatePayload) => api.post<Course>("/courses", payload),
};
