"""Real HTTP checks, actual media processor, downtime/timeout, and process/database restarts."""

import base64
import io
import json
import math
import struct
import threading
import time
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
import pymysql
from runtime import (
    ROOT,
    RUNTIME,
    LOGS,
    credentials,
    start_backend,
    start_media,
    stop,
    mysql,
    record,
)

BASE = "http://127.0.0.1:18080/api"
results = []


def check(name, condition, details=""):
    assert condition, name
    results.append(
        {
            "classification": "Observed",
            "check": name,
            "passed": True,
            "details": details,
        }
    )
    print(f"Observed: PASS {name} {details}", flush=True)


class Client:
    def __init__(self):
        self.http = httpx.Client(base_url=BASE, timeout=30)

    def get(self, path, **kw):
        return self.http.get(path, **kw)

    def write(self, method, path, **kw):
        token = self.get("/auth/csrf").json()["token"]
        return self.http.request(method, path, headers={"X-XSRF-TOKEN": token}, **kw)

    def login(self, email, password):
        r = self.write(
            "POST", "/auth/login", data={"email": email, "password": password}
        )
        check("session login", r.status_code == 200)

    def register(self, email, password):
        r = self.write(
            "POST",
            "/auth/register",
            json={
                "displayName": "Verification Listener",
                "email": email,
                "password": password,
                "role": "ADMIN",
                "id": 999999,
            },
        )
        check(
            "registration forces LISTENER and safe DTO",
            r.status_code == 201
            and r.json()["role"] == "LISTENER"
            and "passwordHash" not in r.json(),
        )
        self.login(email, password)

    def upload(self, title, genre="Jazz", audio=None, cover=True):
        files = {
            "audio": (
                "../../unsafe.wav",
                audio if audio is not None else fixture,
                "audio/wav",
            )
        }
        if cover:
            files["cover"] = ("../cover.png", png, "image/png")
        return self.write(
            "POST",
            "/admin/songs",
            data={
                "title": title,
                "artist": "Raagify verification",
                "album": "Isolated test audio",
                "durationSeconds": "15",
                "genre": genre,
            },
            files=files,
        )


def audio_fixture():
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(
            b"".join(
                struct.pack("<h", int(10000 * math.sin(2 * math.pi * 440 * i / 22050)))
                for i in range(22050 * 15)
            )
        )
    return out.getvalue()


fixture = audio_fixture()
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg=="
)


def main():
    c = credentials()
    tag = uuid.uuid4().hex[:10]
    admin = Client()
    admin.login("private-admin@raagify.test", c["adminPassword"])
    a = Client()
    b = Client()
    email = f"listener-{tag}@raagify.test"
    a.register(email, c["listenerPassword"])
    b.register(f"other-{tag}@raagify.test", c["listenerPassword"])
    anonymous = Client()
    check("anonymous catalog denial", anonymous.get("/songs").status_code == 401)
    check(
        "missing CSRF denied",
        anonymous.http.post("/auth/register", json={}).status_code == 403,
    )
    check("listener upload role denial", a.upload("Denied").status_code == 403)
    check(
        "invalid request 400",
        a.write("POST", "/playlists", json={"name": " "}).status_code == 400,
    )
    songs = []
    for title, genre in [
        ("Midnight current", ""),
        ("Amber skies", "Jazz"),
        ("Slow morning", "Jazz"),
    ]:
        r = admin.upload(title, genre)
        check("audio and cover upload", r.status_code == 201)
        data = r.json()
        songs.append(data)
        check("actual Python extraction stored READY", data["featureStatus"] == "READY")
        if not genre:
            check(
                "missing embedded genre remains explicitly unclassified",
                data["genreSource"] == "UNCLASSIFIED"
                and data["genre"] == "Unclassified",
            )
        check(
            "authenticated cover",
            a.get(data["coverUrl"].removeprefix("/api")).status_code == 200,
        )
    first, second, third = [s["id"] for s in songs]
    check(
        "wrong upload signature",
        admin.upload("Invalid", audio=b"not a WAV").status_code == 400,
    )
    invalid_cover = admin.write(
        "POST",
        "/admin/songs",
        data={"title": "Bad cover", "artist": "Test", "durationSeconds": "15"},
        files={
            "audio": ("ok.wav", fixture, "audio/wav"),
            "cover": ("cover.png", b"fake PNG", "image/png"),
        },
    )
    check("wrong cover signature", invalid_cover.status_code == 400)
    oversized = admin.upload("Oversized", audio=b"RIFF" + bytes(26214401))
    check("upload size limit", oversized.status_code == 413)
    for key, value in [
        ("title", "Midnight"),
        ("artist", "verification"),
        ("genre", "Jazz"),
    ]:
        r = a.get("/songs", params={"q": value, "size": 2})
        check(
            f"paginated search by {key}",
            r.status_code == 200
            and r.json()["totalElements"] > 0
            and len(r.json()["content"]) <= 2,
        )
    check(
        "duplicate like 409",
        a.write("POST", f"/likes/{first}", json={"userId": 999999}).status_code == 201
        and a.write("POST", f"/likes/{first}").status_code == 409,
    )
    check("likes scoped to session", b.get("/likes").json() == [])
    check(
        "other user cannot unlike",
        b.write("DELETE", f"/likes/{first}").status_code == 404,
    )
    r = a.write(
        "POST", "/playlists", json={"name": f"Persistent mix {tag}", "ownerId": 999999}
    )
    p = r.json()["id"]
    check("playlist create", r.status_code == 201)
    for method, path, kw in [
        ("GET", f"/playlists/{p}", {}),
        ("PUT", f"/playlists/{p}", {"json": {"name": "Stolen"}}),
        ("DELETE", f"/playlists/{p}", {}),
        ("POST", f"/playlists/{p}/songs/{second}", {}),
        ("PUT", f"/playlists/{p}/songs/order", {"json": {"songIds": []}}),
    ]:
        r = b.get(path) if method == "GET" else b.write(method, path, **kw)
        check(f"another owner's playlist denial {method} {path}", r.status_code == 403)
    check(
        "playlist add",
        a.write("POST", f"/playlists/{p}/songs/{first}").status_code == 201,
    )
    check(
        "duplicate playlist entry 409",
        a.write("POST", f"/playlists/{p}/songs/{first}").status_code == 409,
    )
    a.write("POST", f"/playlists/{p}/songs/{second}")
    check(
        "playlist rename",
        a.write("PUT", f"/playlists/{p}", json={"name": f"Saved mix {tag}"}).status_code
        == 200,
    )
    r = a.write("PUT", f"/playlists/{p}/songs/order", json={"songIds": [second, first]})
    check(
        "playlist reorder",
        r.status_code == 200 and r.json()["songs"][0]["id"] == second,
    )
    check(
        "invalid reorder 400",
        a.write(
            "PUT", f"/playlists/{p}/songs/order", json={"songIds": [first, first]}
        ).status_code
        == 400,
    )
    check(
        "playlist remove",
        a.write("DELETE", f"/playlists/{p}/songs/{first}").status_code == 200,
    )
    a.write("POST", f"/playlists/{p}/songs/{first}")
    check(
        "history write",
        a.write("POST", f"/songs/{second}/plays", json={"userId": 99999}).status_code
        == 204,
    )
    check(
        "history session scope",
        b.get("/history/recent").json() == []
        and a.get("/history/recent").json()[0]["id"] == second,
    )
    check(
        "recommendations exclude liked",
        all(s["id"] != first for s in a.get("/recommendations").json()),
    )
    popular = b.get("/recommendations").json()
    check(
        "new listener popular fallback",
        len(popular) > 0 and popular[0]["playCount"] >= popular[-1]["playCount"],
    )
    similar = a.get(f"/songs/{first}/similar").json()
    check(
        "similar songs excludes source and limits ten",
        0 < len(similar) <= 10 and all(s["id"] != first for s in similar),
    )
    for header, start, end in [
        ("bytes=0-31", 0, 32),
        ("bytes=-16", len(fixture) - 16, len(fixture)),
        ("bytes=32-", 32, len(fixture)),
    ]:
        r = a.get(f"/songs/{first}/stream", headers={"Range": header})
        check(
            f"exact HTTP Range {header}",
            r.status_code == 206
            and r.content == fixture[start:end]
            and r.headers["content-range"] == f"bytes {start}-{end - 1}/{len(fixture)}",
        )
    check(
        "invalid range 416",
        a.get(
            f"/songs/{first}/stream", headers={"Range": "bytes=999999999-"}
        ).status_code
        == 416,
    )
    stop("media")
    r = admin.upload("Pending jazz", "Jazz")
    check(
        "media processor service down upload succeeds pending",
        r.status_code == 201 and r.json()["featureStatus"] == "PENDING",
    )
    pending = r.json()["id"]
    check(
        "pending similar falls back to genre",
        a.get(f"/songs/{pending}/similar").json()[0]["genre"] == "Jazz",
    )

    class Slow(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            time.sleep(5)
            try:
                self.send_response(503)
                self.end_headers()
            except OSError:
                pass

        def log_message(self, *args):
            pass

    slow = ThreadingHTTPServer(("127.0.0.1", 18000), Slow)
    thread = threading.Thread(target=slow.serve_forever, daemon=True)
    thread.start()
    try:
        begin = time.monotonic()
        r = admin.upload("Timed out", "Jazz")
        elapsed = time.monotonic() - begin
        check(
            "media processor read timeout upload succeeds pending",
            r.status_code == 201
            and r.json()["featureStatus"] == "PENDING"
            and elapsed < 8,
            f"elapsed={elapsed:.2f}s",
        )
    finally:
        slow.shutdown()
        slow.server_close()
    start_media()
    r = admin.write("POST", f"/admin/songs/{pending}/features/retry")
    check(
        "pending features retry preserves admin genre",
        r.status_code == 200
        and r.json()["featureStatus"] == "READY"
        and r.json()["genre"] == "Jazz"
        and r.json()["genreSource"] == "ADMIN_OVERRIDE",
    )
    stop("backend")
    stop("mysql")
    mysql()
    start_backend()
    a.login(email, c["listenerPassword"])
    check(
        "persistence after backend and MySQL restart",
        a.get(f"/playlists/{p}").status_code == 200
        and len(a.get(f"/playlists/{p}").json()["songs"]) == 2
        and any(s["id"] == first for s in a.get("/likes").json())
        and a.get(f"/songs/{first}/stream").content == fixture,
    )
    connection = pymysql.connect(
        host="127.0.0.1",
        port=33317,
        user="raagify_test",
        password=c["dbPassword"],
        database="raagify_test",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT version,success FROM flyway_schema_history WHERE type='SQL'"
        )
        migrations = cursor.fetchall()
    connection.close()
    check(
        "real MySQL Flyway V1/V2/V3",
        all((str(version), 1) in migrations for version in (1, 2, 3)),
        str(migrations),
    )
    a.write("DELETE", f"/playlists/{p}")
    check("playlist delete", a.get(f"/playlists/{p}").status_code == 404)
    a.write("DELETE", f"/likes/{first}")
    check("unlike", all(s["id"] != first for s in a.get("/likes").json()))
    check(
        "logout invalidates session",
        a.write("POST", "/auth/logout").status_code == 200
        and a.get("/auth/me").status_code == 401,
    )
    (RUNTIME / "browser-fixture.wav").write_bytes(fixture)
    (RUNTIME / "browser-cover.png").write_bytes(png)
    (RUNTIME / "browser.json").write_text(
        json.dumps(
            {
                "email": email,
                "songId": first,
                "songTitle": songs[0]["title"],
                "tag": tag,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        (ROOT / "verification" / "live-results.json").write_text(
            json.dumps(results, indent=2)
        )
