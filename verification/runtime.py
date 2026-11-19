"""Isolated local verification infrastructure; never touches an existing DB."""

from pathlib import Path
import json
import os
import secrets
import subprocess
import sys
import time
import httpx
import pymysql

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "verification" / "runtime"
LOGS = ROOT / "verification" / "logs"
RUNTIME.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def credentials():
    path = RUNTIME / "secrets.json"
    if not path.exists():
        path.write_text(
            json.dumps(
                {
                    "dbPassword": secrets.token_urlsafe(24),
                    "adminPassword": secrets.token_urlsafe(24),
                    "listenerPassword": secrets.token_urlsafe(18),
                }
            )
        )
    return json.loads(path.read_text())


def environment():
    c = credentials()
    env = os.environ.copy()
    env.update(
        DB_URL="jdbc:mysql://127.0.0.1:33317/raagify_test?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC",
        DB_USER="raagify_test",
        DB_PASSWORD=c["dbPassword"],
        ADMIN_EMAIL="private-admin@raagify.test",
        ADMIN_PASSWORD=c["adminPassword"],
        AUDIO_STORAGE_PATH=str(RUNTIME / "audio"),
        COVER_STORAGE_PATH=str(RUNTIME / "covers"),
        SERVER_PORT="18080",
        ML_BASE_URL="http://127.0.0.1:18000",
        ML_READ_TIMEOUT_MS="3000",
        DEV_API_TARGET="http://127.0.0.1:18080",
        PYTHONPATH=str(ROOT / ".cache" / "python"),
    )
    return env


def record(name, command, cwd, exit_code=None):
    with (ROOT / "verification" / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "classification": "Observed",
                    "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "name": name,
                    "command": list(map(str, command)),
                    "cwd": str(cwd),
                    "exitCode": exit_code,
                }
            )
            + "\n"
        )


def run(name, command, cwd=ROOT):
    # Preserve prior outcomes rather than overwriting the only evidence of a failure.
    existing = LOGS / f"{name}.log"
    if existing.exists():
        archive = LOGS / f"{name}-previous-{time.time_ns()}.log"
        existing.rename(archive)
    with (LOGS / f"{name}.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(
            list(map(str, command)),
            cwd=cwd,
            env=environment(),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=FLAGS,
        )
    record(name, command, cwd, result.returncode)
    print(
        f"Observed: {name}: exit {result.returncode}; verification/logs/{name}.log",
        flush=True,
    )
    return result.returncode


def launch(name, command, cwd=ROOT):
    log = (LOGS / f"{name}.log").open("a", encoding="utf-8")
    proc = subprocess.Popen(
        list(map(str, command)),
        cwd=cwd,
        env=environment(),
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=FLAGS,
    )
    log.close()
    record(name, command, cwd)
    path = RUNTIME / "processes.json"
    processes = json.loads(path.read_text()) if path.exists() else {}
    processes[name] = proc.pid
    path.write_text(json.dumps(processes))
    return proc


def stop(name):
    import psutil

    path = RUNTIME / "processes.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    pid = data.pop(name, None)
    if pid:
        try:
            process = psutil.Process(pid)
            # Ensure this is a task-owned process, including shell children.
            if "raagify" not in " ".join(process.cmdline()).lower() and name != "mysql":
                raise RuntimeError("Refusing to stop an unrelated process")
            for child in process.children(recursive=True):
                child.terminate()
            process.terminate()
            try:
                process.wait(10)
            except psutil.TimeoutExpired:
                process.kill()
        except psutil.NoSuchProcess:
            pass
    path.write_text(json.dumps(data))


def wait_http(url):
    for _ in range(60):
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service did not become ready: {url}")


def mysql():
    binary = Path(
        os.getenv("VERIFY_MYSQL_HOME", r"E:\projectexcelr!\tools\mysql-8.4.0-winx64")
    )
    data = (RUNTIME / "mysql-data").resolve()
    if ROOT not in data.parents:
        raise RuntimeError("Verification data must stay inside workspace")
    c = credentials()
    if not data.exists():
        code = run(
            "mysql-initialize",
            [
                binary / "bin" / "mysqld.exe",
                "--no-defaults",
                f"--basedir={binary}",
                f"--datadir={data}",
                "--initialize-insecure",
                "--console",
            ],
        )
        if code:
            raise RuntimeError("MySQL initialization failed")
    try:
        connection = pymysql.connect(
            host="127.0.0.1", port=33317, user="root", password=c["dbPassword"]
        )
        connection.close()
        return
    except pymysql.MySQLError:
        pass
    launch(
        "mysql",
        [
            binary / "bin" / "mysqld.exe",
            "--no-defaults",
            f"--basedir={binary}",
            f"--datadir={data}",
            "--port=33317",
            "--bind-address=127.0.0.1",
            "--mysqlx=0",
            "--console",
        ],
    )
    connection = None
    for _ in range(40):
        for password in (c["dbPassword"], ""):
            try:
                connection = pymysql.connect(
                    host="127.0.0.1",
                    port=33317,
                    user="root",
                    password=password,
                    autocommit=True,
                )
                break
            except pymysql.MySQLError:
                pass
        if connection:
            break
        time.sleep(1)
    if not connection:
        raise RuntimeError("MySQL did not start")
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (c["dbPassword"],)
        )
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS raagify_test CHARACTER SET utf8mb4"
        )
        cursor.execute(
            "CREATE USER IF NOT EXISTS 'raagify_test'@'localhost' IDENTIFIED BY %s",
            (c["dbPassword"],),
        )
        cursor.execute("GRANT ALL ON raagify_test.* TO 'raagify_test'@'localhost'")
    connection.close()
    print("Observed: isolated MySQL 8.4 on 33317; schema raagify_test", flush=True)


def start_ml():
    launch(
        "ml",
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--app-dir",
            str(ROOT / "ml-service"),
            "--host",
            "127.0.0.1",
            "--port",
            "18000",
        ],
    )
    wait_http("http://127.0.0.1:18000/health")


def start_backend():
    launch(
        "backend",
        [
            r"C:\Program Files\Java\jdk-21.0.10\bin\java.exe",
            "-Dfile.encoding=UTF-8",
            "-jar",
            ROOT / "backend" / "target" / "raagify-backend-1.0.0.jar",
        ],
    )
    wait_http("http://127.0.0.1:18080/api/health")


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "setup":
        mysql()
        start_ml()
    elif action == "start":
        start_backend()
        launch(
            "frontend",
            [
                r"C:\Program Files\nodejs\node.exe",
                ROOT / "frontend" / "node_modules" / "vite" / "bin" / "vite.js",
                "--host",
                "127.0.0.1",
                "--port",
                "15173",
                "--strictPort",
            ],
            ROOT / "frontend",
        )
        wait_http("http://127.0.0.1:15173")
    elif action == "backend-tests":
        sys.exit(
            run(
                action,
                [sys.executable, "tools/maven.py", "-f", "backend/pom.xml", "test"],
            )
        )
    elif action == "package":
        sys.exit(
            run(
                action,
                [
                    sys.executable,
                    "tools/maven.py",
                    "-f",
                    "backend/pom.xml",
                    "-DskipTests",
                    "package",
                ],
            )
        )
    elif action == "frontend-tests":
        sys.exit(
            run(action, [r"C:\Program Files\nodejs\npm.cmd", "test"], ROOT / "frontend")
        )
    elif action == "frontend-build":
        sys.exit(
            run(
                action,
                [r"C:\Program Files\nodejs\npm.cmd", "run", "build"],
                ROOT / "frontend",
            )
        )
    elif action == "python-tests":
        sys.exit(
            run(action, [sys.executable, "-m", "pytest", "-q"], ROOT / "ml-service")
        )
    elif action == "stop":
        for name in ["frontend", "backend", "ml", "mysql"]:
            stop(name)
