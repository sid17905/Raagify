import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";
import { api, ensureCsrf, write } from "./api";
vi.mock("./api", () => ({
  api: { get: vi.fn() },
  write: vi.fn(),
  ensureCsrf: vi.fn(),
}));
function Probe() {
  const a = useAuth();
  return (
    <>
      <span>{a.loading ? "Restoring" : a.user?.displayName || "Guest"}</span>
      <span>{a.error}</span>
      <button onClick={() => a.login("listener@example.com", "password")}>
        Login
      </button>
      <button onClick={a.logout}>Logout</button>
    </>
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  ensureCsrf.mockResolvedValue("token");
  write.mockResolvedValue({ data: {} });
});
describe("session lifecycle (isolated client tests)", () => {
  it("waits for session restoration before showing identity", async () => {
    let resolve;
    api.get.mockReturnValue(new Promise((r) => (resolve = r)));
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    expect(screen.getByText("Restoring")).toBeInTheDocument();
    await act(async () => resolve({ data: { displayName: "Asha" } }));
    expect(screen.getByText("Asha")).toBeInTheDocument();
  });
  it("shows connection failures distinctly from signed-out state", async () => {
    api.get.mockRejectedValue(new Error("network"));
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    expect(await screen.findByText(/Unable to connect/)).toBeInTheDocument();
  });
  it("refreshes CSRF after form login and clears identity on logout", async () => {
    api.get
      .mockRejectedValueOnce({ response: { status: 401 } })
      .mockResolvedValue({ data: { displayName: "Asha" } });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await screen.findByText("Guest");
    fireEvent.click(screen.getByText("Login"));
    await screen.findByText("Asha");
    expect(write.mock.calls[0][0].data.toString()).toContain(
      "email=listener%40example.com",
    );
    expect(ensureCsrf).toHaveBeenCalledWith(true);
    fireEvent.click(screen.getByText("Logout"));
    await waitFor(() => expect(screen.getByText("Guest")).toBeInTheDocument());
    expect(write).toHaveBeenLastCalledWith({
      method: "post",
      url: "/auth/logout",
    });
  });
});
