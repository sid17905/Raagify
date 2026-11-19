import { describe, expect, it } from "vitest";
import { formatTime } from "./PlayerContext";
describe("formatTime", () => {
  it("formats player time", () => {
    expect(formatTime(125)).toBe("2:05");
    expect(formatTime(NaN)).toBe("0:00");
  });
});
