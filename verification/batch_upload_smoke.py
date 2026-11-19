"""Real browser batch review/upload/retry against Spring, MySQL and Python."""

import json
import uuid
import httpx
from playwright.sync_api import sync_playwright, expect
from runtime import ROOT, RUNTIME, credentials

results = []


def checked(name, details=""):
    results.append(
        {
            "classification": "Observed",
            "check": name,
            "passed": True,
            "details": details,
        }
    )
    print(f"Observed: PASS {name} {details}", flush=True)


def main():
    tag = uuid.uuid4().hex[:8]
    fixture = (RUNTIME / "browser-fixture.wav").read_bytes()
    cover = (RUNTIME / "browser-cover.png").read_bytes()
    private = credentials()
    names = [
        f"Batch {tag} one.wav",
        f"Batch {tag} broken.wav",
        f"Batch {tag} three.wav",
    ]
    saved_ids = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()
        errors = []
        responses = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "response",
            lambda response: (
                responses.append(response.status)
                if response.request.method == "POST"
                and response.url.endswith("/api/admin/songs")
                else None
            ),
        )
        page.goto("http://127.0.0.1:15173/")
        page.get_by_label("Email address").fill("private-admin@raagify.test")
        page.get_by_label("Password", exact=True).fill(private["adminPassword"])
        page.get_by_role("button", name="Sign in →", exact=True).click()
        page.get_by_role("link", name="Manage music").click()
        page.get_by_role("button", name="Batch upload", exact=True).click()
        dialog = page.get_by_role("dialog", name="Batch upload songs")
        expect(dialog.get_by_text("Select your first batch")).to_be_visible()
        checked("batch empty state")
        picker = dialog.get_by_label("Select audio files", exact=False)
        picker.set_input_files(
            [
                {
                    "name": name,
                    "mimeType": "audio/wav",
                    "buffer": fixture if index != 1 else b"this is not a WAV",
                }
                for index, name in enumerate(names)
            ]
        )
        first = dialog.get_by_role("region", name=f"Track 1: {names[0]}")
        broken = dialog.get_by_role("region", name=f"Track 2: {names[1]}")
        third = dialog.get_by_role("region", name=f"Track 3: {names[2]}")
        expect(first.get_by_label("Title", exact=True)).to_have_value(names[0][:-4])
        expect(first.get_by_label("Duration (seconds)")).to_have_value(
            "15", timeout=15000
        )
        expect(third.get_by_label("Duration (seconds)")).to_have_value(
            "15", timeout=15000
        )
        expect(
            dialog.get_by_role("button", name="Upload ready tracks (0)")
        ).to_be_disabled()
        expect(
            broken.get_by_text("Duration could not be read. Enter it manually.")
        ).to_be_visible(timeout=15000)
        checked(
            "filename titles, real native audio duration detection and missing-details guidance"
        )
        dialog.get_by_label("Artist for batch").fill(f"Batch Artist {tag}")
        dialog.get_by_label("Album for batch").fill(f"Batch Album {tag}")
        dialog.get_by_label("Genre for batch").fill("Jazz")
        dialog.get_by_role("button", name="Apply shared details").click()
        expect(first.get_by_label("Artist", exact=True)).to_have_value(
            f"Batch Artist {tag}"
        )
        expect(third.get_by_label("Album", exact=True)).to_have_value(
            f"Batch Album {tag}"
        )
        first.get_by_label("Artist", exact=True).fill(f"Solo Artist {tag}")
        first.get_by_label("Cover (optional)").set_input_files(
            {"name": "cover.png", "mimeType": "image/png", "buffer": cover}
        )
        broken.get_by_label("Duration (seconds)").fill("15")
        checked("shared metadata, per-track edits and optional cover")
        dialog.get_by_role("button", name="Upload ready tracks (3)").click()
        expect(dialog.get_by_role("button", name="Close dialog")).to_be_disabled()
        expect(dialog.get_by_text("Uploaded", exact=True)).to_have_count(
            2, timeout=30000
        )
        expect(
            broken.get_by_text("Content does not match the claimed file type")
        ).to_be_visible()
        expect(
            dialog.get_by_role("button", name="Upload remaining (1)")
        ).to_be_enabled()
        assert responses == [201, 400, 201], responses
        checked("partial batch success with real invalid-signature 400", str(responses))
        broken.get_by_label("Replace audio").set_input_files(
            {
                "name": f"Batch {tag} repaired.wav",
                "mimeType": "audio/wav",
                "buffer": fixture,
            }
        )
        repaired = dialog.get_by_role(
            "region", name=f"Track 2: Batch {tag} repaired.wav"
        )
        expect(repaired.get_by_label("Duration (seconds)")).to_have_value(
            "15", timeout=15000
        )
        repaired.get_by_label("Title", exact=True).fill(f"Batch {tag} repaired")
        dialog.get_by_role("button", name="Upload ready tracks (1)").click()
        expect(dialog.get_by_text("Uploaded", exact=True)).to_have_count(
            3, timeout=30000
        )
        assert responses == [201, 400, 201, 201], responses
        checked(
            "replacement audio and retry do not resubmit successful tracks",
            str(responses),
        )
        response = page.request.get(f"http://127.0.0.1:15173/api/songs?q={tag}&size=50")
        catalog = response.json()["content"]
        saved_ids.extend(song["id"] for song in catalog)
        assert len(catalog) == 3
        titles = {song["title"]: song for song in catalog}
        song = titles[names[0][:-4]]
        assert (
            song["artist"] == f"Solo Artist {tag}"
            and song["album"] == f"Batch Album {tag}"
            and song["durationSeconds"] == 15
        )
        assert song["coverUrl"] and all(
            song["featureStatus"] == "READY" for song in catalog
        )
        checked(
            "three persisted DTOs with edited metadata, cover and actual ML features"
        )
        stream = page.request.get(
            f"http://127.0.0.1:15173/api/songs/{song['id']}/stream",
            headers={"Range": "bytes=0-31"},
        )
        assert stream.status == 206 and stream.body() == fixture[:32]
        checked("batch-uploaded audio authenticated Range bytes")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert dialog.bounding_box()["width"] <= 390
        page.screenshot(path=str(RUNTIME / "batch-mobile.png"))
        checked("batch dialog fits mobile viewport")
        dialog.get_by_role("button", name="Done", exact=True).click()
        page.set_viewport_size({"width": 1440, "height": 960})
        row = page.locator(".admin-row").filter(has_text=names[0][:-4])
        expect(row).to_be_visible()
        row.get_by_role("button", name="Edit", exact=True).click()
        edit = page.get_by_role("dialog", name="Edit song")
        edit.get_by_label("Album", exact=True).fill(f"Edited after batch {tag}")
        edit.get_by_role("button", name="Save changes", exact=True).click()
        expect(edit).to_have_count(0)
        stored = page.request.get(
            f"http://127.0.0.1:15173/api/songs/{song['id']}"
        ).json()
        assert stored["album"] == f"Edited after batch {tag}"
        checked("saved batch tracks remain editable through Manage music")
        assert not errors, errors
        checked("no browser page errors")
        # Delete only the test rows whose IDs were returned for this unique tag.
        token = page.request.get("http://127.0.0.1:15173/api/auth/csrf").json()["token"]
        for song_id in saved_ids:
            assert (
                page.request.delete(
                    f"http://127.0.0.1:15173/api/admin/songs/{song_id}",
                    headers={"X-XSRF-TOKEN": token},
                ).status
                == 204
            )
        browser.close()
    with httpx.Client(base_url="http://127.0.0.1:18080/api", timeout=10) as client:

        def csrf():
            return {"X-XSRF-TOKEN": client.get("/auth/csrf").json()["token"]}

        email = f"batch-listener-{tag}@raagify.test"
        assert (
            client.post(
                "/auth/register",
                headers=csrf(),
                json={
                    "displayName": "Batch security test",
                    "email": email,
                    "password": private["listenerPassword"],
                },
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/auth/login",
                headers=csrf(),
                data={"email": email, "password": private["listenerPassword"]},
            ).status_code
            == 200
        )
        denied = client.post(
            "/admin/songs",
            headers=csrf(),
            data={
                "title": "Denied batch test",
                "artist": "Listener",
                "durationSeconds": "15",
            },
            files={"audio": ("denied.wav", fixture, "audio/wav")},
        )
        assert denied.status_code == 403
        checked(
            "batch transport retains backend ADMIN enforcement", "listener POST -> 403"
        )


if __name__ == "__main__":
    try:
        main()
    finally:
        (ROOT / "verification" / "batch-results.json").write_text(
            json.dumps(results, indent=2)
        )
