# Final media processor verification

**Observed — 19 November 2026:** Trained genre classification was removed; Python remains a model-free processor for embedded tags/covers and real DSP features. This report supersedes earlier classifier and initial-delivery claims. Historical reports/logs retain their original execution context.

**Observed:** The isolated local runtime uses MySQL 8.4 at `127.0.0.1:33317/raagify_test`, Spring at `18080`, FastAPI at `18000`, and Vite at `15173`. MySQL returned successful Flyway versions 1, 2 and 3. The 60 supplied songs (IDs 32–91) retained `ADMIN_OVERRIDE` genre sets and covers. Only identified synthetic verification tracks/accounts were cleaned up.

| Classification | Exact command from repository root | Result / evidence |
| --- | --- | --- |
| Observed | `python -c "import sys; from pathlib import Path; sys.path.insert(0,'verification'); from runtime import run; target=Path('backend/target').resolve(); assert Path.cwd().resolve() in target.parents; sys.exit(run('media-clean-package',[sys.executable,'tools/maven.py','-f','backend/pom.xml','clean','-DskipTests','package']))"` | Clean Java package passed; `logs/media-clean-package.log` |
| Observed | `python -c "import sys; sys.path.insert(0,'verification'); from runtime import start_media; start_media(); print('Observed: media processor healthy')"` | Processor health 200 |
| Observed | `python -c "import sys; sys.path.insert(0,'verification'); from runtime import start_backend; start_backend(); print('Observed: backend healthy; app http://127.0.0.1:15173')"` | Spring/DB health 200; V3 applied to real MySQL |
| Observed | `python verification/runtime.py backend-tests` | 10 tests passed; 8 integration tests use real MySQL/HTTP/media processor, 2 focused Java checks; `logs/backend-tests.log` |
| Observed | `python verification/runtime.py frontend-tests` | 13 component/unit tests passed; `logs/frontend-tests.log` |
| Observed | `python verification/runtime.py python-tests` | 5 processor tests passed using actual DSP decoding/metadata; `logs/python-tests.log` |
| Observed | `python -c "import sys; sys.path.insert(0,'verification'); from runtime import run; sys.exit(run('media-dashboard-smoke',[sys.executable,'verification/media_dashboard_smoke.py']))"` | 16 live API/browser checks passed; `logs/media-dashboard-smoke.log`, `media-dashboard-results.json` |
| Observed | `python -c "import sys; sys.path.insert(0,'verification'); from runtime import run; sys.exit(run('batch-upload-smoke',[sys.executable,'verification/batch_upload_smoke.py']))"` | 11 live batch checks passed; `logs/batch-upload-smoke.log`, `batch-results.json` |
| Observed | `python -c "import sys; sys.path.insert(0,'verification'); from runtime import run; sys.exit(run('sidebar-layout',[sys.executable,'verification/sidebar_layout.py']))"` | 48 live route/viewport combinations passed; `logs/sidebar-layout.log`, `sidebar-results.json` |
| Observed | `python verification/runtime.py frontend-build` | Vite build passed; packaging evidence only; `logs/frontend-build.log` |
| Observed | `E:\Docker\App\resources\cli-plugins\docker-compose.exe --env-file .env.example -f compose.yaml config --quiet` | Configuration passed; `logs/media-compose-config.log` |
| Observed | `E:\Docker\App\resources\cli-plugins\docker-compose.exe --env-file .env.example -f compose.yaml up --build -d` | Exit 1: Docker engine pipe unavailable; `logs/media-compose-up.log` |
| Observed | `python tools/readme_screenshots.py` | README gallery refreshed from existing files in `pics/` |

**Observed — backend integration:** Registration forces LISTENER, CSRF/session login/logout work, listener admin access is denied, other-owner playlist IDs are forbidden, duplicate likes/entries return 409, playlist CRUD/reorder and validation work, and session identity scopes likes/history. Real uploads store DSP features; search and authenticated Range checks pass. Similar results exclude the source and personal recommendations exclude liked songs. Analytics is restricted to ADMIN and validates period bounds. Focused Java checks use an intentionally slow HTTP server to exercise timeout/down handling; they are not model or end-to-end evidence.

**Observed — live media/dashboard:** Embedded metadata preview cleans `53_505` to `505`. Uploads save exact embedded artwork and finite DSP vectors without model/confidence fields. Existing MP3 artwork decodes in Edge; native playback advances, seeks to 10 seconds, resumes and receives authenticated HTTP 206. The analytics time selector and mobile layout work, UTC daily totals agree with persisted data, and individual genre counts overlap. Processor shutdown leaves uploads successful/PENDING and analytics accessible. Recovery restores artwork/features and preserves curated genres. DSP status and exact artwork survive a backend restart. Listeners receive 403 for analytics and metadata extraction. No browser page errors were observed.

**Observed — live batch:** Empty/missing-detail states, actual duration extraction, shared/per-track metadata, covers, partial success (`201,400,201`), replacement/retry without resubmitting saved rows, persisted edits, exact authenticated Range bytes, mobile layout, post-save editing and listener upload denial passed.

**Observed — layout:** Six routes at eight viewport sizes passed without horizontal page overflow. The eight-bar sidebar decoration stays contained, and sign-out remains clear of the player. No page errors were observed.

**Observed:** [curated-genres-results.json](curated-genres-results.json) records the user-supplied genre sets. The final live check asserts all 60 remain curated and checks `505`, `Sapphire` and `Lose My Mind` explicitly. These labels are administrator data, not inferred classification.

**Unverified:** Docker container runtime, physical speaker output, every codec/device and production deployment. Frontend component mocks and bundle compilation are reported separately from real MySQL/HTTP/Edge evidence. No trained classifier remains.

**Recommendation:** Run `python verification/media_dashboard_smoke.py` and `python verification/batch_upload_smoke.py` with this isolated runtime to repeat the live checks. The dashboard script deliberately restarts Spring and the processor, invalidating live sessions.
