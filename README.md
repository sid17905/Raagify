# Raagify

**Observed (source):** A full-stack music streaming application with listener registration/session login, catalog search, authenticated Range audio, likes, private ordered playlists, listening history, recommendations, and an administrator upload/metadata panel. Java 21 + Spring Boot 3.5.0, MySQL/Flyway, React/Vite, Python FastAPI.

**Observed:** Existing partial `backend/` and `frontend/` changes were retained and completed. Reference session/CSRF, validated upload, bounded Range streaming, RestClient timeout and native-audio patterns were adapted to the music domain. Historical REA guides and the old reference changelog are kept locally and excluded from Git. Raagify's own run steps and verification evidence are included here.

**Observed:** Actual executed checks and failures are recorded in [verification/REPORT.md](verification/REPORT.md), [verification/commands.jsonl](verification/commands.jsonl), and `verification/logs/`. A frontend build and isolated client tests are not end-to-end evidence. See the report for real MySQL, HTTP, ML failure and browser results.

**Observed:** No genre model was supplied. MFCC, spectral centroid, tempo and chroma are extracted from real decoded audio. The genre result is explicitly `Unclassified / PLACEHOLDER`; an administrator can override it. Model setup and the exact API/schema are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Local setup

**Recommendation:** Use Java 21, Maven 3.9.9+, MySQL 8.4, Node 24 and Python 3.12+. Keep one project database separate from other applications. Create it with a database administrator, using your own private password:

```sql
CREATE DATABASE raagify CHARACTER SET utf8mb4;
CREATE USER 'raagify'@'localhost' IDENTIFIED BY 'your-private-password';
GRANT ALL ON raagify.* TO 'raagify'@'localhost';
```

**Recommendation:** Copy `.env.example` to `.env` and replace all placeholder passwords and the admin email. Match DB_PASSWORD to the MySQL account. Use a private administrator email distinct from public listener accounts. Relative media paths are relative to the backend working directory. Run all the following commands from the repository root in separate terminals as indicated.

**Recommendation - Windows PowerShell:** Load the environment in each service terminal (the env file uses literal, unquoted values):

```powershell
Copy-Item .env.example .env
# Edit .env before proceeding.
Get-Content .env | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
```

**Recommendation - macOS/Linux:** Export the service values explicitly with shell-safe quoting, or use a dotenv runner. The example JDBC URL contains shell metacharacters, so do not source the unquoted `.env.example` as a shell script.

**Recommendation - backend terminal:**

```powershell
mvn -f backend/pom.xml spring-boot:run
```

**Observed (source):** Flyway applies V1 to the configured schema at startup and validates existing migration checksums. Use a fresh schema; do not apply V1 to a database managed by another project. The app requires DB_PASSWORD. Default backend address is http://127.0.0.1:8080.

**Recommendation - ML terminal:**

```powershell
python -m venv ml-service/.venv
ml-service/.venv/Scripts/python.exe -m pip install -r ml-service/requirements.txt
ml-service/.venv/Scripts/python.exe -m uvicorn app:app --app-dir ml-service --host 127.0.0.1 --port 8000
# macOS/Linux: use ml-service/.venv/bin/python instead.
```

**Recommendation - frontend terminal:**

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev -- --port 5173 --strictPort
# macOS/Linux: npm instead of npm.cmd.
```

**Observed (source):** Open http://localhost:5173. Vite proxies `/api` to DEV_API_TARGET, default http://127.0.0.1:8080. Audio and API requests use the same browser origin and session. Register publicly for a listener account, or sign in with the bootstrapped administrator. The collection starts empty; upload your own authorized audio from Manage music.

## Private administrator bootstrap

**Recommendation:** Set ADMIN_EMAIL, ADMIN_PASSWORD (12+ characters, at most 72 UTF-8 bytes), and optionally ADMIN_NAME before starting Spring. Sign in through the regular login screen, then open Manage music. After the account is created, remove ADMIN_PASSWORD from subsequent runtime configuration if desired.

**Observed (source):** Bootstrap creates an ADMIN only if its email does not exist. It never promotes a listener, and startup rejects an existing listener at the bootstrap email. Existing administrator passwords are not reset by subsequent startup. Registration forces LISTENER regardless of request role fields. BCrypt hashes and storage paths never appear in response DTOs.

**Observed (local verification setup):** For the already-running app at http://127.0.0.1:15173, the administrator email is `private-admin@raagify.test`. Its generated password is the `adminPassword` value in the ignored local file `verification/runtime/secrets.json`. Sign out of a listener account, then use the same login form with those administrator credentials. Open Manage music -> Upload a song. These local verification credentials are not shipped in Git; a fresh installation uses your own ADMIN_EMAIL/ADMIN_PASSWORD.

**Recommendation (local verification only):** If you intentionally change `adminPassword` in that secrets file, run `python verification/sync_local_admin.py` to update the existing isolated administrator hash, restart Spring and verify login. A normal server restart does not reset an existing account's password from bootstrap settings. This helper only targets `private-admin@raagify.test` in the local `raagify_test` schema.

**Observed (source):** Upload audio plus an optional cover, supply title, artist and duration in seconds, and optionally album/genre. Successful analysis stores READY features; unavailable/timed-out ML still saves the upload with PENDING features. Similar and personal recommendations use genre fallback, with popularity for new users. Pending tracks have a Retry features action. Admin genre overrides survive retries.

**Observed (source):** Manage music -> Batch upload accepts up to 25 WAV/MP3/OGG files per batch, with a 25 MiB limit per file. Titles are prefilled from filenames and durations are read from local audio when supported. Review title, artist and duration before publishing; album, genre and artwork are optional. Apply shared artist/album/genre values to unsaved tracks, then adjust individual tracks. Upload ready tracks saves them sequentially through the same protected upload API. Successful rows remain saved when another file fails, and retries skip successful rows. Use Edit in Manage music to change saved details later.

**Observed (source):** Queued files remain in the current browser tab until saved; closing the dialog or reloading loses unsaved selections. Network/server failures with an unknown outcome are not automatically retried: check the refreshed collection before selecting the file again. Server-rejected tracks can be corrected/replaced and retried. Each upload retains backend role/CSRF, signature/size validation and ML fallback behavior.

**Observed:** [Batch verification](verification/BATCH_UPLOAD.md) records 10 passing frontend tests and 11 real browser/API checks, including partial failure, retry, metadata edits and role denial.

**Recommendation:** For pretrained genre classification candidates and their required adapters, see [docs/PRETRAINED_GENRE.md](docs/PRETRAINED_GENRE.md). The running service remains explicitly PLACEHOLDER until a compatible model is installed and tested.

**Observed (source):** MySQL records and media files persist across normal process restarts. Browser sessions and player queues are in memory; after restarting Spring, sign in again. Reloading the browser while Spring remains running restores its existing session.

## Docker Compose

**Recommendation:** After editing `.env`, run:

```powershell
docker compose --env-file .env -f compose.yaml up --build -d
# Open http://localhost:5173
# Exercise fallback:
docker compose -f compose.yaml stop ml
# Restore service, then use Retry features in the admin panel:
docker compose -f compose.yaml start ml
# Preserve DB and uploaded music when stopping:
docker compose -f compose.yaml down
```

**Observed (source):** Compose includes all three application services plus MySQL, same-origin Nginx API/media proxy, a MySQL health dependency, and named database/media volumes. Optional model files mount read-only under `/models`; set COMPOSE_GENRE_MODEL_PATH=/models/model.joblib with its matching manifest.

**Observed:** Compose configuration was validated. Container build/up was attempted and failed because the Docker engine pipe was unavailable. **Unverified:** Container runtime and Compose volume restart behavior remain unverified; local process/MySQL persistence has separate evidence in the report.

## Repeat the checks

**Recommendation:** For backend integration tests, point DB_URL/DB_USER/DB_PASSWORD at a dedicated database named `raagify_test`, provision a private test ADMIN_EMAIL/ADMIN_PASSWORD, and run the actual Python ML service at ML_BASE_URL first. These tests create data and fail if the test schema/real ML service is unavailable.

```powershell
mvn -f backend/pom.xml test
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
ml-service/.venv/Scripts/python.exe -m pytest -q ml-service
```

**Observed (verification tooling):** Optional `tools/maven.py` supports the portable Maven 3.9.9 directory used on this host. The `verification/runtime.py` helper runs task-owned MySQL on 33317, Spring on 18080, Python on 18000 and Vite on 15173; its data and generated credentials are ignored under `verification/runtime/`. It requires the indicated portable MySQL binary (or VERIFY_MYSQL_HOME) and Python httpx/PyMySQL/psutil/playwright. Do not point this helper at production data. The exact executed commands and host-specific prerequisites are in the report.

**Recommendation - this verification host:**

```powershell
python verification/runtime.py setup
python verification/runtime.py backend-tests
python verification/runtime.py frontend-tests
python verification/runtime.py python-tests
python verification/runtime.py package
python verification/runtime.py start
python verification/live_smoke.py
python verification/browser_smoke.py
python verification/runtime.py stop
```

**Unverified:** Other audio codecs, physical speaker output, trained genre accuracy and production deployment are not established by the tested WAV/Edge scenario.

## GitHub delivery

**Observed:** Source and evidence were committed in the isolated `.cache/publish` checkout because root `.git` writes are restricted in this environment. The GitHub repository was empty when inspected. A push to `https://github.com/sid17905/Raagify.git` was attempted and failed: Windows Credential Manager could not persist credentials and Git could not obtain a username non-interactively. GitHub CLI also reported invalid stored authentication. See `verification/logs/git-push.log`.

**Recommendation:** Reauthenticate from your normal terminal, then push the completed local checkout:

```powershell
gh auth login --hostname github.com
git -c http.sslBackend=openssl -C .cache/publish push -u origin main
```

**Observed:** `Raagify.bundle`, when present in the delivery workspace, is an export of the local Git history. It excludes private runtime credentials and data and can be cloned into another directory if the isolated checkout is unavailable.
