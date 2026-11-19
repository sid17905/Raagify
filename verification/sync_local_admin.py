"""Apply an explicitly requested password change to the isolated local admin."""

import json
import os
from pathlib import Path
import subprocess
import httpx
import pymysql
from runtime import ROOT, RUNTIME, FLAGS, credentials, stop, start_backend


def main():
    private = credentials()
    password = private["adminPassword"]
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise SystemExit(
            "adminPassword must have 12+ characters and at most 72 UTF-8 bytes"
        )
    source = RUNTIME / "HashPassword.java"
    source.write_text("""import java.nio.charset.StandardCharsets;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
class HashPassword {
    public static void main(String[] args) throws Exception {
        String password = new String(System.in.readAllBytes(), StandardCharsets.UTF_8);
        System.out.print(new BCryptPasswordEncoder().encode(password));
    }
}
""")
    crypto = next(
        (ROOT / ".cache/m2/org/springframework/security/spring-security-crypto").rglob(
            "*.jar"
        )
    )
    logging = next((ROOT / ".cache/m2/org/springframework/spring-jcl").rglob("*.jar"))
    encoded = subprocess.run(
        [
            r"C:\Program Files\Java\jdk-21.0.10\bin\java.exe",
            "--class-path",
            os.pathsep.join(map(str, [crypto, logging])),
            str(source),
        ],
        input=password.encode("utf-8"),
        capture_output=True,
        check=True,
        creationflags=FLAGS,
    ).stdout.decode("utf-8")
    if not encoded.startswith("$2a$") or len(encoded) != 60:
        raise SystemExit("Password encoding failed")
    connection = pymysql.connect(
        host="127.0.0.1",
        port=33317,
        user="raagify_test",
        password=private["dbPassword"],
        database="raagify_test",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE email=%s AND role='ADMIN'",
                ("private-admin@raagify.test",),
            )
            existing = cursor.fetchone()
            if not existing:
                raise SystemExit("The isolated local administrator does not exist")
            # Keep a private rollback copy. Never copy this into source/evidence logs.
            (RUNTIME / "admin-password-rollback.json").write_text(
                json.dumps({"previousHash": existing[0]})
            )
            stop("backend")
            cursor.execute(
                "UPDATE users SET password_hash=%s WHERE email=%s AND role='ADMIN'",
                (encoded, "private-admin@raagify.test"),
            )
            connection.commit()
    finally:
        connection.close()
    start_backend()
    with httpx.Client(base_url="http://127.0.0.1:18080/api", timeout=10) as client:
        token = client.get("/auth/csrf").json()["token"]
        response = client.post(
            "/auth/login",
            data={"email": "private-admin@raagify.test", "password": password},
            headers={"X-XSRF-TOKEN": token},
        )
        assert response.status_code == 200
        assert client.get("/auth/me").json()["role"] == "ADMIN"
    print(
        "Observed: applied the requested local admin password, restarted Spring, verified login 200 and ADMIN identity. Password/hash were not logged."
    )


if __name__ == "__main__":
    main()
