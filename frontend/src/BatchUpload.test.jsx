import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import BatchUpload from "./BatchUpload";
import { write } from "./api";

vi.mock("./api", () => ({
  write: vi.fn(),
  message: (error) => error.response?.data?.message || error.message,
}));
vi.mock("./batchFiles", async () => {
  const actual = await vi.importActual("./batchFiles");
  return { ...actual, readDuration: vi.fn().mockResolvedValue("3") };
});

beforeEach(() => vi.clearAllMocks());

async function selectTracks(names = ["First_track.wav", "Second_track.wav"]) {
  const files = names.map(
    (name) => new File(["RIFF fixture WAVE"], name, { type: "audio/wav" }),
  );
  fireEvent.change(screen.getByLabelText(/Select audio files/), {
    target: { files },
  });
  await waitFor(() =>
    expect(screen.getAllByLabelText("Duration (seconds)")[0]).toHaveValue(3),
  );
  fireEvent.change(screen.getByLabelText("Artist for batch"), {
    target: { value: "Batch Artist" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Apply shared details" }));
  return files;
}

it("prefills filename titles/durations and only enables uploads with required metadata", async () => {
  render(<BatchUpload onClose={vi.fn()} onChanged={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Select audio files/), {
    target: { files: [new File(["RIFF"], "First_track.wav")] },
  });
  await waitFor(() =>
    expect(screen.getByLabelText("Duration (seconds)")).toHaveValue(3),
  );
  expect(screen.getByLabelText("Title")).toHaveValue("First track");
  expect(
    screen.getByRole("button", { name: "Upload ready tracks (0)" }),
  ).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Artist"), {
    target: { value: "Asha" },
  });
  expect(
    screen.getByRole("button", { name: "Upload ready tracks (1)" }),
  ).toBeEnabled();
});

it("keeps successes and retries only a server-rejected track", async () => {
  const changed = vi.fn();
  write
    .mockResolvedValueOnce({
      data: { id: 1, featureStatus: "READY", genreSource: "PLACEHOLDER" },
    })
    .mockRejectedValueOnce({
      response: { status: 400, data: { message: "Invalid cover" } },
    })
    .mockResolvedValueOnce({ data: { id: 2, featureStatus: "PENDING" } });
  render(<BatchUpload onClose={vi.fn()} onChanged={changed} />);
  await selectTracks();
  fireEvent.click(
    screen.getByRole("button", { name: "Upload ready tracks (2)" }),
  );
  await screen.findByText("Invalid cover");
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Upload remaining (1)" }),
    ).toBeEnabled(),
  );
  const first = screen.getByRole("region", {
    name: "Track 1: First_track.wav",
  });
  expect(
    within(first).getByText("Uploaded", { exact: true }),
  ).toBeInTheDocument();
  expect(within(first).getByLabelText("Title")).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Upload remaining (1)" }));
  await waitFor(() =>
    expect(screen.getAllByText("Uploaded", { exact: true })).toHaveLength(2),
  );
  expect(write).toHaveBeenCalledTimes(3);
  expect(write.mock.calls.map(([config]) => config.data.get("title"))).toEqual([
    "First track",
    "Second track",
    "Second track",
  ]);
  expect(write.mock.calls[0][0].url).toBe("/admin/songs");
  expect(changed).toHaveBeenCalledTimes(2);
});

it("does not retry a network failure whose server outcome is unknown", async () => {
  write.mockRejectedValue(new Error("Network unavailable"));
  render(<BatchUpload onClose={vi.fn()} onChanged={vi.fn()} />);
  await selectTracks(["Unknown.wav"]);
  fireEvent.click(
    screen.getByRole("button", { name: "Upload ready tracks (1)" }),
  );
  expect(
    await screen.findByText(/Upload could not be confirmed/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Upload remaining (0)" }),
  ).toBeDisabled();
  expect(write).toHaveBeenCalledTimes(1);
});

it("stops a batch after permission denial and blocks closing during an upload", async () => {
  let finish;
  write.mockReturnValue(
    new Promise((resolve, reject) => {
      finish = reject;
    }),
  );
  const close = vi.fn();
  render(<BatchUpload onClose={close} onChanged={vi.fn()} />);
  await selectTracks();
  fireEvent.click(
    screen.getByRole("button", { name: "Upload ready tracks (2)" }),
  );
  expect(screen.getByRole("button", { name: "Close dialog" })).toBeDisabled();
  fireEvent.click(screen.getByRole("dialog").parentElement);
  expect(close).not.toHaveBeenCalled();
  finish({ response: { status: 403, data: { message: "Access denied" } } });
  await screen.findByText(/administrator session is unavailable/);
  expect(write).toHaveBeenCalledTimes(1);
});

it("rejects unsupported file types and skips files already selected", async () => {
  render(<BatchUpload onClose={vi.fn()} onChanged={vi.fn()} />);
  const file = new File(["text"], "notes.txt", { lastModified: 1 });
  const picker = screen.getByLabelText(/Select audio files/);
  fireEvent.change(picker, { target: { files: [file] } });
  expect(
    screen.getByText("Choose WAV, MP3, or OGG audio."),
  ).toBeInTheDocument();
  fireEvent.change(picker, { target: { files: [file] } });
  expect(screen.getAllByRole("region", { name: /Track \d/ })).toHaveLength(1);
  expect(screen.getByText(/already-selected file/)).toBeInTheDocument();
  fireEvent.change(picker, {
    target: { files: Array.from({ length: 26 }, (_, index) => new File(["RIFF"], `track-${index}.wav`)) },
  });
  expect(screen.getByText("Choose at most 25 files per batch.")).toBeInTheDocument();
  expect(screen.getAllByRole("region", { name: /Track \d/ })).toHaveLength(1);
});
