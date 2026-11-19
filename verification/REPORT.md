# Raagify verification report

**Observed:** This report records Raagify executions on 2026-11-19. The supplied REA ledger records another workspace and is not current-app evidence. Observed means source fact or actual execution; Inference means a reasoned but unexercised conclusion; Recommendation means a proposed action; Unverified means unexecuted behavior with its boundary.

## Results

| Classification | Check | Result / evidence |
| --- | --- | --- |
| Observed | Backend tests, Java 21 / Boot 3.5.0 | 9 passed: 7 real-server HTTP/MySQL integration tests + 2 cosine/HTTP-timeout tests. No in-memory DB or mocked application services. logs/backend-tests.log |
| Observed | Frontend tests | 5 passed: session restoration, login/CSRF/logout, connection errors, obsolete request cancellation, time formatting. These use isolated mocked client responses and establish client behavior only. logs/frontend-tests.log |
| Observed | Python tests | 4 passed with real WAV decode, 27 finite features, spectral centroid/chroma response, invalid audio, health/placeholder flags. logs/python-tests.log |
| Observed | Production frontend bundle | Build passed; compilation evidence only. logs/frontend-build.log |
| Observed | Backend package | Executable jar packaged successfully. logs/package.log |
| Observed | Real Flyway/MySQL | MySQL 8.4.0 on isolated 33317, raagify_test schema; V1 applied and later validated. Logs mysql-initialize.log, mysql.log and backend-tests.log |
| Observed | Live full-stack HTTP | 59 passing checks; live-results.json and logs/live-smoke.log |
| Observed | Actual Edge browser | 19 passing checks; browser-results.json and logs/browser-smoke.log |
| Observed | Compose config | Exit 0 using .env.example; logs/compose-config.log |
| Unverified | Compose build/up and volume restart | Up attempted, exit 1: missing npipe docker_engine. logs/compose-up.log |
| Observed | Genre model availability | No model supplied; real extracted features and explicit Unclassified/PLACEHOLDER genre, not trained classification |
| Unverified | Genre model loading/accuracy | No supplied weights, compatible model or dataset to execute |
| Unverified | Other codec/browser/device behavior | Native browser scenario is a generated 15-second mono PCM WAV in headless Edge; no physical speaker, MP3/OGG, or other device claim |

**Observed:** Test total is 18 (9 Java + 5 frontend + 4 Python). Live API and browser assertions are separate. A passing client mock or frontend bundle was not counted as a functioning full-stack feature.

**Observed:** The isolated database has persisted test fixtures under ignored verification/runtime/. No existing application schema was changed. Private generated credentials were injected into child process environments, excluded from source and logs, and checked for accidental log inclusion.

## Real-pair acceptance checks

- **Observed:** session login.
- **Observed:** registration forces LISTENER and safe DTO.
- **Observed:** session login.
- **Observed:** registration forces LISTENER and safe DTO.
- **Observed:** session login.
- **Observed:** anonymous catalog denial.
- **Observed:** missing CSRF denied.
- **Observed:** listener upload role denial.
- **Observed:** invalid request 400.
- **Observed:** audio and cover upload.
- **Observed:** actual Python extraction stored READY.
- **Observed:** genre prediction clearly placeholder.
- **Observed:** authenticated cover.
- **Observed:** audio and cover upload.
- **Observed:** actual Python extraction stored READY.
- **Observed:** authenticated cover.
- **Observed:** audio and cover upload.
- **Observed:** actual Python extraction stored READY.
- **Observed:** authenticated cover.
- **Observed:** wrong upload signature.
- **Observed:** wrong cover signature.
- **Observed:** upload size limit.
- **Observed:** paginated search by title.
- **Observed:** paginated search by artist.
- **Observed:** paginated search by genre.
- **Observed:** duplicate like 409.
- **Observed:** likes scoped to session.
- **Observed:** other user cannot unlike.
- **Observed:** playlist create.
- **Observed:** another owner's playlist denial GET /playlists/7.
- **Observed:** another owner's playlist denial PUT /playlists/7.
- **Observed:** another owner's playlist denial DELETE /playlists/7.
- **Observed:** another owner's playlist denial POST /playlists/7/songs/18.
- **Observed:** another owner's playlist denial PUT /playlists/7/songs/order.
- **Observed:** playlist add.
- **Observed:** duplicate playlist entry 409.
- **Observed:** playlist rename.
- **Observed:** playlist reorder.
- **Observed:** invalid reorder 400.
- **Observed:** playlist remove.
- **Observed:** history write.
- **Observed:** history session scope.
- **Observed:** recommendations exclude liked.
- **Observed:** new listener popular fallback.
- **Observed:** similar songs excludes source and limits ten.
- **Observed:** exact HTTP Range bytes=0-31.
- **Observed:** exact HTTP Range bytes=-16.
- **Observed:** exact HTTP Range bytes=32-.
- **Observed:** invalid range 416.
- **Observed:** ML service down upload succeeds pending.
- **Observed:** pending similar falls back to genre.
- **Observed:** ML read timeout upload succeeds pending - elapsed=5.20s.
- **Observed:** pending features retry preserves admin genre.
- **Observed:** session login.
- **Observed:** persistence after backend and MySQL restart.
- **Observed:** real MySQL Flyway V1 - (('1', 1),).
- **Observed:** playlist delete.
- **Observed:** unlike.
- **Observed:** logout invalidates session.

## Browser checks

- **Observed:** browser form login.
- **Observed:** session restored on browser reload.
- **Observed:** native audio decodes and playback advances - {'duration': 15, 'currentTime': 0.346787}.
- **Observed:** browser seek and resume - 10.213288.
- **Observed:** native authenticated Range 206 - [{'url': 'http://127.0.0.1:15173/api/songs/17/stream', 'status': 206, 'range': 'bytes 0-661543/661544'}].
- **Observed:** volume control.
- **Observed:** next and previous controls.
- **Observed:** browser likes and Liked Songs page.
- **Observed:** browser playlist create.
- **Observed:** browser playlist add.
- **Observed:** browser playlist rename.
- **Observed:** browser playlist remove.
- **Observed:** browser playlist delete.
- **Observed:** mobile layout and sign-out access.
- **Observed:** browser logout.
- **Observed:** admin audio and cover upload in browser.
- **Observed:** admin genre override in browser.
- **Observed:** admin delete in browser.
- **Observed:** no browser page errors.

**Observed:** Browser playback advanced above 0.3 seconds, seeking moved to 10 seconds, playback resumed above 10.2 seconds, and the native audio request returned 206 with Content-Range. This tests the seek control and authenticated Range transport; the small WAV was cached in full by the browser, so a distinct second network fetch for every seek is not claimed.

## Failed attempts retained

**Observed:** The first backend run had 1 failure out of 9: concurrent distinct playlist additions returned 409 due to a stale MySQL REPEATABLE READ snapshot established before the row lock. Playlist mutations were changed to READ COMMITTED while preserving the owner lock. The repeated 9-test run passed. logs/backend-tests-failed.log retains the failure.

**Observed:** The first expanded frontend run had 1 failure out of 5 because DOM cleanup was missing between tests. Explicit afterEach cleanup corrected the test harness; all 5 passed. logs/frontend-tests-failed.log retains the failure.

**Observed:** Initial browser runs failed on accessible selectors for navigation icons and a select label. Decorative nav icons were excluded from accessible names and the playlist select received an explicit label. The final browser run passed all recorded checks. logs/browser-smoke-failed.log and browser-smoke-selector-failed.log retain those failures.

**Observed:** The default Git HTTPS attempt failed with a Windows Schannel credential error. OpenSSL transport reached the empty supplied GitHub repository. Root .git metadata became read-only after initialization; an isolated publishing checkout was created under ignored .cache/publish. GitHub CLI reported invalid stored authentication. Final commit/push outcome is recorded separately in the delivery result.

## Exact executed check commands

**Observed:** The following table is generated from commands.jsonl. Server launches have no terminal exit in this register; health, real API, browser and restart checks establish their observed behavior. Credentials are environment variables and are not included in the recorded argv.

| Classification | Name | Exact command | Working directory | Exit |
| --- | --- | --- | --- | --- |
| Observed | mysql-initialize | `E:\projectexcelr!\tools\mysql-8.4.0-winx64\bin\mysqld.exe --no-defaults --basedir=E:\projectexcelr!\tools\mysql-8.4.0-winx64 --datadir=E:\Raagify\verification\runtime\mysql-data --initialize-insecure --console` | `E:\Raagify` | 0 |
| Observed | mysql | `E:\projectexcelr!\tools\mysql-8.4.0-winx64\bin\mysqld.exe --no-defaults --basedir=E:\projectexcelr!\tools\mysql-8.4.0-winx64 --datadir=E:\Raagify\verification\runtime\mysql-data --port=33317 --bind-address=127.0.0.1 --mysqlx=0 --console` | `E:\Raagify` | None |
| Observed | ml | `C:\Python314\python.exe -m uvicorn app:app --app-dir E:\Raagify\ml-service --host 127.0.0.1 --port 18000` | `E:\Raagify` | None |
| Observed | backend-tests | `C:\Python314\python.exe tools/maven.py -f backend/pom.xml test` | `E:\Raagify` | 1 |
| Observed | frontend-tests | `"C:\\Program Files\\nodejs\\npm.cmd" test` | `E:\Raagify\frontend` | 1 |
| Observed | backend-tests | `C:\Python314\python.exe tools/maven.py -f backend/pom.xml test` | `E:\Raagify` | 0 |
| Observed | frontend-tests | `"C:\\Program Files\\nodejs\\npm.cmd" test` | `E:\Raagify\frontend` | 0 |
| Observed | package | `C:\Python314\python.exe tools/maven.py -f backend/pom.xml -DskipTests package` | `E:\Raagify` | 0 |
| Observed | python-tests | `C:\Python314\python.exe -m pytest -q` | `E:\Raagify\ml-service` | 0 |
| Observed | backend | `"C:\\Program Files\\Java\\jdk-21.0.10\\bin\\java.exe" -Dfile.encoding=UTF-8 -jar E:\Raagify\backend\target\raagify-backend-1.0.0.jar` | `E:\Raagify` | None |
| Observed | frontend | `"C:\\Program Files\\nodejs\\node.exe" E:\Raagify\frontend\node_modules\vite\bin\vite.js --host 127.0.0.1 --port 15173 --strictPort` | `E:\Raagify\frontend` | None |
| Observed | ml | `C:\Python314\python.exe -m uvicorn app:app --app-dir E:\Raagify\ml-service --host 127.0.0.1 --port 18000` | `E:\Raagify` | None |
| Observed | mysql | `E:\projectexcelr!\tools\mysql-8.4.0-winx64\bin\mysqld.exe --no-defaults --basedir=E:\projectexcelr!\tools\mysql-8.4.0-winx64 --datadir=E:\Raagify\verification\runtime\mysql-data --port=33317 --bind-address=127.0.0.1 --mysqlx=0 --console` | `E:\Raagify` | None |
| Observed | compose-config | `E:\Docker\App\resources\cli-plugins\docker-compose.exe --env-file .env.example -f compose.yaml config --quiet` | `E:\Raagify` | 0 |
| Observed | compose-up | `E:\Docker\App\resources\cli-plugins\docker-compose.exe --env-file .env.example -f compose.yaml up --build -d` | `E:\Raagify` | 1 |
| Observed | backend | `"C:\\Program Files\\Java\\jdk-21.0.10\\bin\\java.exe" -Dfile.encoding=UTF-8 -jar E:\Raagify\backend\target\raagify-backend-1.0.0.jar` | `E:\Raagify` | None |
| Observed | live-smoke | `C:\Python314\python.exe verification/live_smoke.py` | `E:\Raagify` | 0 |
| Observed | browser-smoke | `C:\Python314\python.exe verification/browser_smoke.py` | `E:\Raagify` | 1 |
| Observed | browser-smoke | `C:\Python314\python.exe verification/browser_smoke.py` | `E:\Raagify` | 1 |
| Observed | frontend-build | `"C:\\Program Files\\nodejs\\npm.cmd" run build` | `E:\Raagify\frontend` | 0 |
| Observed | browser-smoke | `C:\Python314\python.exe verification/browser_smoke.py` | `E:\Raagify` | 0 |
| Observed | frontend-build | `"C:\\Program Files\\nodejs\\npm.cmd" run build` | `E:\Raagify\frontend` | 0 |
| Observed | frontend-build | `"C:\\Program Files\\nodejs\\npm.cmd" run build` | `E:\Raagify\frontend` | 0 |

**Observed - supplementary initial setup/checks:** `java -version` reported 21.0.10; `node --version` 24.14.0; `python --version` 3.14.3. Maven was absent from PATH, so Maven 3.9.9 was extracted from the retained portable archive and its dependency cache copied into this workspace. `npm.cmd install --cache E:\Raagify\.cache\npm --no-audit --no-fund` (cwd frontend) exited 0. `python -m pip install --target .cache\python soundfile==0.13.1 --no-deps` (cwd root) exited 0. The initial `python tools\maven.py -f backend\pom.xml -DskipTests package` exited 0 with no tests yet; that result was not counted as app verification. The initial `npm.cmd run build` and `npm.cmd test` (cwd frontend) exited 0 with only the original 1 format test; expanded final checks above supersede them. Initial `python -m pytest -q` (cwd ml-service, PYTHONPATH=.cache/python) passed 4; final recorded Python run also passed 4.

**Observed:** environment.json records actual Python package versions. requirements.txt matches those versions, with soundfile 0.13.1 installed into the workspace-local target. The host Python is 3.14.3; Docker targets 3.12 and remains unexecuted.

**Recommendation:** Enable the Docker engine, authenticate GitHub if publishing was blocked, and rerun the indicated external checks. Keep model accuracy and other-codec/device claims Unverified until separately exercised.

**Observed - final source review:** Frontend JavaScript/JSX/CSS was formatted with `npm.cmd exec --yes --cache E:\Raagify\.cache\npm --package=prettier@3.5.3 -- prettier --write src/**/*.{jsx,js,css} vite.config.js` (cwd frontend, exit 0). Python source was formatted with `python -m ruff format ml-service verification tools/maven.py tools/publish.py` (cwd root, exit 0). The final frontend bundle was rebuilt after formatting. `python tools/publish.py` staged source and evidence in the isolated checkout and passed `git diff --cached --check` for source files; verbatim execution logs were excluded from whitespace lint.
