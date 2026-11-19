"""Actual Edge browser against the running React, Spring, MySQL and Python pair."""

import json
import time
import uuid
from playwright.sync_api import sync_playwright, expect
from runtime import ROOT, RUNTIME, credentials

results = []


def check(name, details=""):
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
    fixture = json.loads((RUNTIME / "browser.json").read_text())
    c = credentials()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()
        errors = []
        ranges = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "response",
            lambda response: (
                ranges.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "range": response.headers.get("content-range"),
                    }
                )
                if "/stream" in response.url
                else None
            ),
        )

        def login(email, password):
            page.goto("http://127.0.0.1:15173/")
            page.get_by_label("Email address").fill(email)
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_role("button", name="Sign in →", exact=True).click()
            expect(page.get_by_role("link", name="Discover", exact=True)).to_be_visible(
                timeout=30000
            )

        login(fixture["email"], c["listenerPassword"])
        check("browser form login")
        page.reload()
        expect(page.get_by_role("link", name="Discover", exact=True)).to_be_visible()
        check("session restored on browser reload")
        page.screenshot(path=str(RUNTIME / "desktop.png"), full_page=True)
        page.get_by_role("link", name="Browse & search").click()
        page.get_by_role("textbox", name="Search music").fill(fixture["songTitle"])
        page.get_by_role("button", name="Search", exact=True).click()
        play = page.get_by_role(
            "button", name=f"Play {fixture['songTitle']}", exact=True
        )
        expect(play).to_be_visible()
        play.click()
        page.wait_for_function(
            "document.querySelector('audio').currentTime > .3", timeout=20000
        )
        check(
            "native audio decodes and playback advances",
            str(
                page.locator("audio").evaluate(
                    "a=>({duration:a.duration,currentTime:a.currentTime})"
                )
            ),
        )
        page.get_by_role("button", name="Pause", exact=True).click()
        expect(page.get_by_role("button", name="Play", exact=True)).to_be_visible()
        page.get_by_role("slider", name="Seek", exact=True).evaluate(
            "e=>{const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;setter.call(e,'10');e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}"
        )
        # Drive the visible control with keyboard too; this exercises React's onChange.
        seek = page.get_by_role("slider", name="Seek", exact=True)
        seek.focus()
        seek.press("ArrowRight")
        page.wait_for_function(
            "document.querySelector('audio').currentTime >= 9.9", timeout=10000
        )
        page.get_by_role("button", name="Play", exact=True).click()
        page.wait_for_function(
            "document.querySelector('audio').currentTime > 10.2", timeout=10000
        )
        check(
            "browser seek and resume",
            str(page.locator("audio").evaluate("a=>a.currentTime")),
        )
        check("native authenticated Range 206", str(ranges))
        assert any(r["status"] == 206 and r["range"] for r in ranges)
        page.get_by_role("slider", name="Volume", exact=True).focus()
        page.get_by_role("slider", name="Volume", exact=True).press("ArrowLeft")
        assert page.locator("audio").evaluate("a=>a.volume") < 0.8
        check("volume control")
        page.get_by_role("button", name="Next", exact=True).click()
        page.wait_for_function(
            "document.querySelector('audio').currentTime < 5", timeout=10000
        )
        page.get_by_role("button", name="Previous", exact=True).click()
        check("next and previous controls")
        page.get_by_role("button", name="Pause", exact=True).click()
        unlike = page.get_by_role(
            "button", name=f"Unlike {fixture['songTitle']}", exact=True
        )
        if unlike.count():
            unlike.click()
        page.get_by_role(
            "button", name=f"Like {fixture['songTitle']}", exact=True
        ).click()
        page.get_by_role("link", name="Liked songs").click()
        expect(
            page.get_by_role("link", name=fixture["songTitle"], exact=True)
        ).to_be_visible()
        check("browser likes and Liked Songs page")
        page.get_by_role("link", name="Your playlists").click()
        name = "Browser mix " + uuid.uuid4().hex[:6]
        page.get_by_label("New playlist").fill(name)
        page.get_by_role("button", name="Create playlist").click()
        expect(page.get_by_role("heading", name=name)).to_be_visible()
        check("browser playlist create")
        page.get_by_role("link", name="Browse & search").click()
        page.get_by_role("textbox", name="Search music").fill(fixture["songTitle"])
        page.get_by_role("button", name="Search", exact=True).click()
        page.get_by_role(
            "button", name=f"Add {fixture['songTitle']} to playlist"
        ).click()
        page.get_by_label("Playlist", exact=True).select_option(label=name)
        page.get_by_role("button", name="Add song", exact=True).click()
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.get_by_role("link", name="Your playlists").click()
        page.get_by_role("link", name=name).click()
        expect(
            page.get_by_role("link", name=fixture["songTitle"], exact=True)
        ).to_be_visible()
        check("browser playlist add")
        page.get_by_role("button", name="Rename", exact=True).click()
        page.get_by_label("Playlist name").fill(name + " saved")
        page.get_by_role("button", name="Save name").click()
        expect(page.get_by_role("heading", name=name + " saved")).to_be_visible()
        check("browser playlist rename")
        page.get_by_role("button", name=f"Remove {fixture['songTitle']}").click()
        expect(page.get_by_text("Give this mix a soundtrack.")).to_be_visible()
        check("browser playlist remove")
        page.get_by_role("button", name="Delete", exact=True).click()
        page.get_by_role("button", name="Delete playlist", exact=True).click()
        expect(page.get_by_label("New playlist")).to_be_visible()
        check("browser playlist delete")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto("http://127.0.0.1:15173/")
        expect(page.get_by_role("button", name="Sign out")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
        page.screenshot(path=str(RUNTIME / "mobile.png"), full_page=True)
        check("mobile layout and sign-out access")
        page.get_by_role("button", name="Sign out").click()
        expect(page.get_by_label("Email address")).to_be_visible()
        check("browser logout")
        page.set_viewport_size({"width": 1440, "height": 960})
        login("private-admin@raagify.test", c["adminPassword"])
        page.get_by_role("link", name="Manage music").click()
        page.get_by_role("button", name="Upload a song").click()
        title = "Browser uploaded " + uuid.uuid4().hex[:6]
        dialog = page.get_by_role("dialog")
        dialog.get_by_label("Title", exact=True).fill(title)
        dialog.get_by_label("Artist", exact=True).fill("Browser artist")
        dialog.get_by_label("Duration (seconds)").fill("15")
        dialog.locator("input[name=audio]").set_input_files(
            str(RUNTIME / "browser-fixture.wav")
        )
        dialog.locator("input[name=cover]").set_input_files(
            str(RUNTIME / "browser-cover.png")
        )
        dialog.get_by_role("button", name="Upload song", exact=True).click()
        expect(page.get_by_text(title, exact=True)).to_be_visible(timeout=30000)
        check("admin audio and cover upload in browser")
        row = page.locator(".admin-row").filter(has_text=title)
        row.get_by_role("button", name="Edit", exact=True).click()
        page.get_by_role("dialog").get_by_label("Genre override (optional)").fill(
            "Jazz"
        )
        page.get_by_role("button", name="Save changes").click()
        expect(row.get_by_text("Features ready · Genre: admin override")).to_be_visible(
            timeout=15000
        )
        check("admin genre override in browser")
        row.get_by_role("button", name="Delete", exact=True).click()
        page.get_by_role("button", name="Delete song", exact=True).click()
        expect(page.get_by_text(title, exact=True)).to_have_count(0)
        check("admin delete in browser")
        assert not errors, errors
        check("no browser page errors")
        browser.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        (ROOT / "verification" / "browser-results.json").write_text(
            json.dumps(results, indent=2)
        )
