import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ListeningChart } from "./AnalyticsDashboard";
import { cleanMusicText, titleFromFilename } from "./batchFiles";

it("shows exact dates/counts when focusing a listening-chart point", () => {
  render(
    <ListeningChart
      points={[
        { date: "2026-11-18", plays: 3 },
        { date: "2026-11-19", plays: 8 },
      ]}
    />,
  );
  fireEvent.focus(screen.getByRole("button", { name: "2026-11-18: 3 plays" }));
  expect(screen.getByText("3 plays", { exact: true })).toBeInTheDocument();
  fireEvent.click(screen.getByText("View daily counts"));
  expect(screen.getByRole("cell", { name: "2026-11-18" })).toBeInTheDocument();
});
it("shows a real empty state instead of fabricated listening points", () => {
  render(<ListeningChart points={[{ date: "2026-11-19", plays: 0 }]} />);
  expect(screen.getByText(/No listening activity/)).toBeInTheDocument();
});
it("cleans download labels and counters while preserving numeric song titles", () => {
  expect(titleFromFilename("53_505_SpotiDost.mp3")).toBe("505");
  expect(cleanMusicText("505", true)).toBe("505");
  expect(titleFromFilename("1979.mp3")).toBe("1979");
  expect(cleanMusicText("Yeh Fitoor Mera (SpotiDost.com)", true)).toBe(
    "Yeh Fitoor Mera",
  );
});
