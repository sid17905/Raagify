"""Observe sidebar containment on the live application at desktop/mobile sizes."""

import json
from playwright.sync_api import sync_playwright, expect
from runtime import ROOT, RUNTIME, credentials


def main():
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto("http://127.0.0.1:15173/")
        page.get_by_label("Email address").fill("private-admin@raagify.test")
        page.get_by_label("Password", exact=True).fill(credentials()["adminPassword"])
        page.get_by_role("button", name="Sign in →", exact=True).click()
        expect(page.get_by_role("link", name="Manage music")).to_be_visible()
        sizes = [
            (1440, 960),
            (1280, 800),
            (1280, 720),
            (1024, 600),
            (900, 480),
            (751, 600),
            (750, 844),
            (390, 844),
        ]
        for width, height in sizes:
            page.set_viewport_size({"width": width, "height": height})
            for route in ["/", "/browse", "/likes", "/playlists", "/recent", "/admin"]:
                page.goto(f"http://127.0.0.1:15173{route}")
                expect(page.locator("main h1").first).to_be_visible()
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                ), (width, height, route)
                assert page.locator(".sidebar nav a").count() == 7
                sidebar = page.locator(".sidebar")
                sidebar.evaluate(
                    "element => { element.scrollTop = element.scrollHeight; }"
                )
                expect(page.get_by_role("button", name="Sign out")).to_be_visible()
                metrics = page.evaluate("""() => {
                    const box = selector => document.querySelector(selector).getBoundingClientRect();
                    const sidebar = box('.sidebar'), note = box('.sidebar-note'), wave = box('.mini-wave');
                    const profile = box('.profile'), player = box('.player');
                    return { sidebarRight: sidebar.right, noteVisible: note.height > 0,
                        noteBottom: note.bottom, waveLeft: wave.left, waveRight: wave.right,
                        profileTop: profile.top, profileBottom: profile.bottom, playerTop: player.top };
                }""")
                if metrics["noteVisible"]:
                    assert page.locator(".mini-wave > span").count() == 8
                    assert metrics["waveRight"] <= metrics["sidebarRight"]
                    assert metrics["waveLeft"] >= 0
                    assert metrics["noteBottom"] <= metrics["profileTop"] + 1
                else:
                    assert width <= 750 or height <= 820
                assert metrics["profileBottom"] <= metrics["playerTop"] + 1
                results.append(
                    {
                        "classification": "Observed",
                        "viewport": [width, height],
                        "route": route,
                        "passed": True,
                        "noteVisible": metrics["noteVisible"],
                    }
                )
            if (width, height) in [(1440, 960), (1280, 720), (390, 844)]:
                page.screenshot(path=str(RUNTIME / f"sidebar-{width}x{height}.png"))
        assert not page_errors, page_errors
        browser.close()
    (ROOT / "verification" / "sidebar-results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(
        f"Observed: {len(results)} live route/viewport checks passed; no horizontal page overflow, sidebar decoration contained, sign-out clear of player, no page errors."
    )


if __name__ == "__main__":
    main()
