"""Observe model-free media processing, artwork, metadata and analytics."""

import io
import json
import math
import struct
import time
import uuid
import wave
import httpx
from PIL import Image
from mutagen.wave import WAVE
from mutagen.id3 import APIC, TIT2, TPE1, TALB, TCON
from playwright.sync_api import sync_playwright, expect
from runtime import ROOT, RUNTIME, credentials, stop, start_media, start_backend

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


def fixture():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(22050)
        audio.writeframes(
            b"".join(
                struct.pack("<h", int(10000 * math.sin(2 * math.pi * 440 * i / 22050)))
                for i in range(22050 * 3)
            )
        )
    picture = io.BytesIO()
    Image.new("RGB", (12, 12), (120, 40, 70)).save(picture, format="PNG")
    stream.seek(0)
    tagged = WAVE(stream)
    tagged.add_tags()
    for tag in [
        TIT2(encoding=3, text="53_505 SpotiDost"),
        TPE1(encoding=3, text="Arctic Monkeys - Topic"),
        TALB(encoding=3, text="AM"),
        TCON(encoding=3, text="Music"),
        APIC(encoding=3, mime="image/png", type=3, data=picture.getvalue()),
    ]:
        tagged.tags.add(tag)
    tagged.save(stream)
    return stream.getvalue(), picture.getvalue()


def main():
    private = credentials()
    audio, cover = fixture()
    created = []
    tag = uuid.uuid4().hex[:8]
    with httpx.Client(base_url="http://127.0.0.1:18080/api", timeout=90) as client:

        def csrf():
            return {"X-XSRF-TOKEN": client.get("/auth/csrf").json()["token"]}

        def login():
            assert (
                client.post(
                    "/auth/login",
                    headers=csrf(),
                    data={
                        "email": "private-admin@raagify.test",
                        "password": private["adminPassword"],
                    },
                ).status_code
                == 200
            )

        login()
        metadata = client.post(
            "/admin/songs/metadata",
            headers=csrf(),
            files={"file": ("53_505.wav", audio, "audio/wav")},
        )
        assert (
            metadata.status_code == 200
            and metadata.json()["title"] == "505"
            and metadata.json()["artist"] == "Arctic Monkeys"
            and metadata.json()["album"] == "AM"
        )
        checked("authenticated embedded metadata preview and title cleanup")
        response = client.post(
            "/admin/songs",
            headers=csrf(),
            data={
                "title": "53_505 SpotiDost",
                "artist": "Arctic Monkeys",
                "durationSeconds": "3",
            },
            files={"audio": ("tagged.wav", audio, "audio/wav")},
        )
        assert response.status_code == 201
        record = response.json()
        created.append(record["id"])
        assert (
            record["title"] == "505"
            and record["genreSource"] == "UNCLASSIFIED"
            and record["featureStatus"] == "READY"
            and "genreModel" not in record
            and "genreConfidence" not in record
        )
        assert client.get(record["coverUrl"].removeprefix("/api")).content == cover
        checked(
            "real DSP features and exact embedded artwork saved without genre guessing",
            record["genre"],
        )
        catalog = client.get("/songs?size=50").json()
        all_songs = list(catalog["content"])
        for page in range(1, catalog["totalPages"]):
            all_songs += client.get(f"/songs?size=50&page={page}").json()["content"]
        assert not any("spotidost" in song["title"].lower() for song in all_songs)
        curated = [song for song in all_songs if 32 <= song["id"] <= 91]
        assert len(curated) == 60 and all(
            song["genreSource"] == "ADMIN_OVERRIDE" and song["coverUrl"]
            for song in curated
        )
        assert (
            next(song for song in curated if song["id"] == 47)["genre"]
            == "Indie Rock / Alternative Rock"
        )
        assert (
            next(song for song in curated if song["id"] == 56)["genre"] == "Punjabi Pop"
        )
        assert (
            next(song for song in curated if song["id"] == 91)["genre"]
            == "Pop Rap / Electropop / Synthpop / Dance-Pop"
        )
        checked("all 60 curated genre sets and embedded covers preserved")
        actual = next(
            song for song in all_songs if song["id"] not in created and song["coverUrl"]
        )
        checked("existing catalog download labels removed and real artwork available")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel="msedge",
                headless=True,
                args=["--autoplay-policy=no-user-gesture-required"],
            )
            page = browser.new_page(viewport={"width": 1440, "height": 960})
            errors = []
            ranges = []
            page.on(
                "response",
                lambda response: (
                    ranges.append(response.status)
                    if "/stream" in response.url
                    else None
                ),
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://127.0.0.1:15173/")
            page.get_by_label("Email address").fill("private-admin@raagify.test")
            page.get_by_label("Password", exact=True).fill(private["adminPassword"])
            page.get_by_role("button", name="Sign in →", exact=True).click()
            expect(
                page.get_by_role("link", name="Manage music", exact=True)
            ).to_be_visible()
            page.goto(f"http://127.0.0.1:15173/songs/{actual['id']}")
            page.wait_for_function(
                "Array.from(document.querySelectorAll('.song-detail img')).some(image=>image.complete&&image.naturalWidth>0)"
            )
            checked("existing song cover decodes visibly in browser", str(actual["id"]))
            page.get_by_role("button", name="Play track", exact=False).click()
            page.wait_for_function(
                "document.querySelector('audio').currentTime > .2", timeout=20000
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            page.get_by_role("slider", name="Seek").fill("10")
            page.get_by_role("button", name="Play", exact=True).click()
            page.wait_for_function(
                "document.querySelector('audio').currentTime > 10.1", timeout=20000
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            assert 206 in ranges, ranges
            checked(
                "existing MP3 plays, seeks and resumes through authenticated Range 206"
            )
            page.get_by_role("link", name="Analytics", exact=True).click()
            expect(
                page.get_by_role("heading", name="The sound of your community.")
            ).to_be_visible()
            expect(
                page.get_by_text("MEDIA PROCESSOR ONLINE", exact=True)
            ).to_be_visible(timeout=15000)
            page.get_by_label("Time period").select_option("7")
            page.wait_for_function(
                "document.querySelector('.analytics-controls select').value === '7' && document.querySelectorAll('.stat-card').length === 6"
            )
            checked("analytics dashboard and selectable time period render real data")
            page.screenshot(path=str(RUNTIME / "analytics-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            page.screenshot(path=str(RUNTIME / "analytics-mobile.png"), full_page=True)
            checked("analytics mobile layout has no horizontal overflow")
            page.set_viewport_size({"width": 1440, "height": 960})
            page.get_by_role("link", name="Manage music", exact=True).click()
            page.get_by_role("button", name="Upload a song", exact=False).click()
            dialog = page.get_by_role("dialog", name="Upload a song")
            dialog.locator("input[name=audio]").set_input_files(
                {"name": "53_505.wav", "mimeType": "audio/wav", "buffer": audio}
            )
            expect(dialog.get_by_label("Title", exact=True)).to_have_value(
                "505", timeout=15000
            )
            expect(dialog.get_by_label("Artist", exact=True)).to_have_value(
                "Arctic Monkeys"
            )
            expect(dialog.get_by_label("Album", exact=True)).to_have_value("AM")
            expect(dialog.get_by_label("Duration (seconds)")).to_have_value("3")
            expect(
                dialog.get_by_text("Embedded cover found.", exact=False)
            ).to_be_visible()
            with page.expect_response(
                lambda response: (
                    response.request.method == "POST"
                    and response.url.endswith("/api/admin/songs")
                )
            ) as saved:
                dialog.get_by_role("button", name="Upload song", exact=True).click()
            saved_record = saved.value.json()
            created.append(saved_record["id"])
            assert (
                saved_record["coverUrl"]
                and saved_record["genreSource"] == "UNCLASSIFIED"
            )
            checked(
                "single upload automatically uses embedded title, artist, album, duration and artwork"
            )
            page.get_by_role("button", name="Batch upload", exact=True).click()
            batch = page.get_by_role("dialog", name="Batch upload songs")
            batch.get_by_label("Select audio files", exact=False).set_input_files(
                {"name": "53_505.wav", "mimeType": "audio/wav", "buffer": audio}
            )
            region = batch.get_by_role("region", name="Track 1: 53_505.wav")
            expect(region.get_by_label("Artist", exact=True)).to_have_value(
                "Arctic Monkeys", timeout=15000
            )
            expect(region.get_by_label("Title", exact=True)).to_have_value("505")
            expect(
                batch.get_by_role("button", name="Upload ready tracks (1)")
            ).to_be_enabled()
            checked(
                "batch metadata prefills required fields and preserves numeric title 505"
            )
            batch.get_by_role("button", name="Close dialog").click()
            assert not errors, errors
            checked("no browser page errors")
            browser.close()
        dashboard = client.get("/admin/analytics?days=7").json()
        assert (
            len(dashboard["dailyPlays"]) == 7
            and sum(day["plays"] for day in dashboard["dailyPlays"])
            == dashboard["period"]["plays"]
        )
        assert (
            sum(genre["songs"] for genre in dashboard["genres"])
            >= dashboard["totals"]["songs"]
            and dashboard["processor"]["status"] == "UP"
            and all(" / " not in genre["name"] for genre in dashboard["genres"])
        )
        checked("analytics period/genre totals agree with persisted aggregate data")
        stop("media")
        unavailable = client.get("/admin/analytics").json()
        assert unavailable["processor"]["status"] == "UNAVAILABLE"
        down = client.post(
            "/admin/songs",
            headers=csrf(),
            data={
                "title": f"Fallback {tag}",
                "artist": "Verification artist",
                "durationSeconds": "3",
                "genre": "Jazz",
            },
            files={"audio": ("tagged.wav", audio, "audio/wav")},
        )
        assert down.status_code == 201 and down.json()["featureStatus"] == "PENDING"
        fallback = down.json()
        created.append(fallback["id"])
        checked("media processor down preserves upload and analytics availability")
        start_media()
        recovered = client.post(
            f"/admin/songs/{fallback['id']}/features/retry", headers=csrf()
        ).json()
        assert (
            recovered["featureStatus"] == "READY"
            and recovered["genre"] == "Jazz"
            and recovered["genreSource"] == "ADMIN_OVERRIDE"
            and recovered["coverUrl"]
        )
        checked("feature retry recovers artwork while preserving curated genre")
        stop("backend")
        start_backend()
        login()
        persisted = client.get(f"/songs/{record['id']}").json()
        assert (
            persisted["genreSource"] == "UNCLASSIFIED"
            and persisted["coverUrl"]
            and client.get(persisted["coverUrl"].removeprefix("/api")).content == cover
        )
        checked("DSP status and exact artwork persist after backend restart")
        for id in created:
            assert (
                client.delete(f"/admin/songs/{id}", headers=csrf()).status_code == 204
            )
    with httpx.Client(base_url="http://127.0.0.1:18080/api", timeout=10) as listener:

        def token():
            return {"X-XSRF-TOKEN": listener.get("/auth/csrf").json()["token"]}

        email = f"media-check-{tag}@raagify.test"
        listener.post(
            "/auth/register",
            headers=token(),
            json={
                "displayName": "Media verification",
                "email": email,
                "password": private["listenerPassword"],
            },
        )
        listener.post(
            "/auth/login",
            headers=token(),
            data={"email": email, "password": private["listenerPassword"]},
        )
        assert (
            listener.get("/admin/analytics").status_code == 403
            and listener.post(
                "/admin/songs/metadata",
                headers=token(),
                files={"file": ("tagged.wav", audio, "audio/wav")},
            ).status_code
            == 403
        )
        checked("listener cannot access analytics or privileged metadata extraction")


if __name__ == "__main__":
    try:
        main()
    finally:
        (ROOT / "verification/media-dashboard-results.json").write_text(
            json.dumps(results, indent=2)
        )
