import { act, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import useResource from "./useResource";
import { api } from "./api";
vi.mock("./api", () => ({ api: { get: vi.fn() }, message: (e) => e.message }));
function Probe({ url }) {
  const r = useResource(url);
  return <div>{r.loading ? "Loading" : r.error || r.data}</div>;
}
it("cancels obsolete requests when switching screens", async () => {
  let resolveOld;
  api.get.mockImplementation((url) =>
    url === "/old"
      ? new Promise((r) => (resolveOld = r))
      : Promise.resolve({ data: "New" }),
  );
  const view = render(<Probe url="/old" />);
  const oldSignal = api.get.mock.calls[0][1].signal;
  view.rerender(<Probe url="/new" />);
  expect(oldSignal.aborted).toBe(true);
  await screen.findByText("New");
  await act(async () => resolveOld({ data: "Old" }));
  expect(screen.getByText("New")).toBeInTheDocument();
});
