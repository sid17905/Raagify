"""Observe real player covers and error-free session restoration in Edge."""

import json
import uuid
from playwright.sync_api import sync_playwright, expect
from runtime import ROOT, credentials


def main():
    results = []

    def checked(name):
        results.append({"classification": "Observed", "check": name, "passed": True})
        print(f"Observed: PASS {name}", flush=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(
            base_url="http://127.0.0.1:15173",
            viewport={"width": 1440, "height": 960},
        )
        failures, errors = [], []
        page.on(
            "response",
            lambda response: (
                failures.append((response.status, response.url))
                if response.status >= 400
                else None
            ),
        )
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:15173/")
        expect(page.get_by_role("button", name="Sign in →", exact=True)).to_be_visible()
        assert page.request.get("/api/auth/session").json() == {"user": None}
        assert page.request.get("/favicon.ico").status == 200
        assert page.request.get("/favicon.svg").status == 200
        assert page.locator(".player-art img").count() == 0
        checked("signed-out startup and favicon resources succeed without 401/404")
        page.get_by_label("Email address").fill("private-admin@raagify.test")
        page.get_by_label("Password", exact=True).fill(credentials()["adminPassword"])
        page.get_by_role("button", name="Sign in →", exact=True).click()
        expect(
            page.get_by_role("link", name="Manage music", exact=True)
        ).to_be_visible()
        page.reload()
        expect(
            page.get_by_role("link", name="Manage music", exact=True)
        ).to_be_visible()
        checked("signed-in session restores on reload")
        page.goto("http://127.0.0.1:15173/songs/47")
        page.locator(".song-detail .cover img").click()
        art = page.locator(".player-art img")
        expect(art).to_have_attribute("src", "/api/songs/47/cover")
        page.wait_for_function(
            "document.querySelector('.player-art img')?.naturalWidth > 0"
        )
        page.wait_for_function("document.querySelector('audio').currentTime > .1")
        checked("505 embedded cover decodes in the player during real MP3 playback")
        page.get_by_role("button", name="Show album cover for 505", exact=True).click()
        panel = page.get_by_role("complementary", name="Now playing details")
        expect(panel).to_be_visible()
        expect(panel.locator("img")).to_have_attribute("src", "/api/songs/47/cover")
        page.wait_for_function(
            "document.querySelector('.now-playing-cover img')?.naturalWidth > 0"
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(ROOT / "pics/nowplayingpanel.png"))
        checked("clicking the player title opens a real album cover in the right panel")
        page.get_by_role("button", name="Next", exact=True).click()
        expect(art).not_to_have_attribute("src", "/api/songs/47/cover")
        expect(panel.locator("img")).not_to_have_attribute("src", "/api/songs/47/cover")
        page.wait_for_function(
            "document.querySelector('.player-art img')?.naturalWidth > 0"
        )
        page.get_by_role("button", name="Previous", exact=True).click()
        expect(art).to_have_attribute("src", "/api/songs/47/cover")
        expect(panel.locator("img")).to_have_attribute("src", "/api/songs/47/cover")
        page.wait_for_function(
            "document.querySelector('.player-art img')?.naturalWidth > 0"
        )
        page.get_by_role("button", name="Pause", exact=True).click()
        expect(art).to_be_visible()
        checked("next/previous update covers and pause keeps current artwork")
        page.keyboard.press("Escape")
        expect(panel).to_have_count(0)
        expect(
            page.get_by_role("button", name="Show album cover for 505", exact=True)
        ).to_be_focused()
        page.locator(".player-art img").click()
        page.wait_for_function("!document.querySelector('audio').paused")
        page.get_by_role("button", name="Pause", exact=True).click()
        checked(
            "Escape closes the panel with focus restored and player artwork starts playback"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        box = art.bounding_box()
        assert box["width"] == box["height"] == 35
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        checked("cover fits the mobile player without overflow")
        page.get_by_role("button", name="Show album cover for 505", exact=True).click()
        expect(panel).to_be_visible()
        bounds = panel.bounding_box()
        player_box = page.locator(".player").bounding_box()
        assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= 390
        assert bounds["y"] + bounds["height"] <= player_box["y"]
        page.get_by_role("button", name="Close now playing details", exact=True).click()
        expect(panel).to_have_count(0)
        checked("right panel fits mobile and stays clear of playback controls")
        page.set_viewport_size({"width": 1440, "height": 960})
        # Intentionally supply an undecodable image, without a failed HTTP status,
        # to exercise the cover fallback separately from normal resource loading.
        page.route(
            "**/api/songs/47/cover",
            lambda route: route.fulfill(
                status=200, content_type="image/png", body=b"invalid image"
            ),
        )
        page.get_by_role("button", name="Next", exact=True).click()
        page.get_by_role("button", name="Previous", exact=True).click()
        expect(page.locator(".player-art")).to_have_text("♫")
        assert page.locator(".player-art img").count() == 0
        page.unroute("**/api/songs/47/cover")
        page.get_by_role("button", name="Next", exact=True).click()
        page.wait_for_function(
            "document.querySelector('.player-art img')?.naturalWidth > 0"
        )
        checked("broken artwork falls back to the note and recovers on track change")
        for route, selector, label in [
            ("/", ".song-card .cover img", "discovery card"),
            ("/browse", ".song-row .cover img", "browse row"),
            ("/admin", ".admin-row .cover img", "admin catalog"),
            ("/admin/analytics", ".popular-list .cover img", "analytics popular song"),
        ]:
            page.goto(route)
            cover = page.locator(selector).first
            expect(cover).to_be_visible()
            source = cover.get_attribute("src")
            cover.click()
            expect(art).to_have_attribute("src", source)
            page.wait_for_function(
                "document.querySelector('audio').currentTime > .1 && !document.querySelector('audio').paused"
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            checked(f"clicking {label} artwork plays the matching real song")
        song = page.request.get("/api/songs/89").json()
        token = page.request.get("/api/auth/csrf").json()["token"]
        headers = {"X-XSRF-TOKEN": token}
        added_like = not song["liked"]
        if added_like:
            assert page.request.post("/api/likes/89", headers=headers).status == 201
        playlist = page.request.post(
            "/api/playlists",
            headers=headers,
            data={"name": f"Cover click check {uuid.uuid4().hex[:8]}"},
        ).json()
        assert (
            page.request.post(
                f"/api/playlists/{playlist['id']}/songs/89", headers=headers
            ).status
            == 201
        )
        for route, label in [
            ("/likes", "liked song"),
            (f"/playlists/{playlist['id']}", "playlist song"),
        ]:
            page.goto(route)
            cover = page.locator(".song-row .cover img[alt='Actor cover']")
            expect(cover).to_be_visible()
            cover.click()
            expect(art).to_have_attribute("src", "/api/songs/89/cover")
            page.wait_for_function(
                "document.querySelector('audio').currentTime > .1 && !document.querySelector('audio').paused"
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            checked(f"clicking {label} cover plays Actor")
        assert (
            page.request.delete(
                f"/api/playlists/{playlist['id']}", headers=headers
            ).status
            == 204
        )
        if added_like:
            assert page.request.delete("/api/likes/89", headers=headers).status == 204
        page.get_by_role("button", name="Sign out", exact=True).click()
        expect(page.get_by_role("button", name="Sign in →", exact=True)).to_be_visible()
        page.reload()
        expect(page.get_by_role("button", name="Sign in →", exact=True)).to_be_visible()
        assert not failures, failures
        assert not errors, errors
        checked(
            "login, reload, playback and logout have no failed HTTP resources or page errors"
        )
        browser.close()
    (ROOT / "verification/player-artwork-results.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
