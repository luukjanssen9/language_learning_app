import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Skill, UserProgress } from "@/lib/api/types";
import { SkillNode } from "./SkillNode";

function makeSkill(overrides: Partial<Skill>): Skill {
  return {
    id: "skill-1",
    course_id: "course-1",
    name: "Greetings",
    slug: "greetings",
    order_index: 0,
    prerequisite_skill_id: null,
    specialty_module: null,
    intro_content: null,
    created_at: "2026-08-14T00:00:00Z",
    ...overrides,
  };
}

function makeProgress(overrides: Partial<UserProgress>): UserProgress {
  return {
    id: "progress-1",
    user_id: "user-1",
    skill_id: "skill-1",
    mastery_level: 0.5,
    last_practiced_at: "2026-08-14T00:00:00Z",
    times_correct: 3,
    times_attempted: 6,
    streak_count: 0,
    created_at: "2026-08-14T00:00:00Z",
    ...overrides,
  };
}

describe("SkillNode", () => {
  it("renders the skill name and a practice link into its lesson", () => {
    render(<SkillNode skill={makeSkill({})} progress={undefined} />);

    expect(screen.getByText("Greetings")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Practice" })).toHaveAttribute(
      "href",
      "/skills/skill-1/lesson",
    );
  });

  it("shows \"Not started\" with no progress row", () => {
    render(<SkillNode skill={makeSkill({})} progress={undefined} />);

    expect(screen.getByText("Not started")).toBeInTheDocument();
  });

  it("shows the correct/attempted count once progress exists", () => {
    render(<SkillNode skill={makeSkill({})} progress={makeProgress({})} />);

    expect(screen.getByText("3/6 correct")).toBeInTheDocument();
    expect(screen.queryByText("Not started")).not.toBeInTheDocument();
  });
});
