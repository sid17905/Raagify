# REA evidence ledger and verification results

**Observed:** This ledger records the revised copies and starter, not a certification of the untouched original projects or every possible feature. Java/backend, database, HTTP and browser claims below refer to named executions. Failed attempts are retained.

**Observed:** The complete original guide was read in line-numbered chunks, including rereading the truncated middle range. The saved file has 1,357 logical lines and a trailing newline (1,358 when counting the final empty line). Its verbatim archive SHA-256 is `23836df01cdfb8e921c0e309a2081fe890e7ea6ca6d33ad33890724c9ee793f9`.

**Observed:** Labels mean: Observed = source or recorded execution; Inference = expected but unexercised consequence; Recommendation = proposed design/action; Unverified = requested behavior that could not be exercised with the available external environment. Table labels apply to their claim cells; code blocks inherit their preceding label.

## What moved from Unverified to Verified

| Classification | Item | Previous state | Final result | Evidence |
| --- | --- | --- | --- | --- |
| Observed | Java 21 runtime | Target mismatch / prerequisite | Verified: installed Java 21.0.10 used for compile and startup | [environment-facts](verification/environment-facts.log) |
| Observed | Isolated MySQL | Not installed/tested | Verified: portable MySQL 8.4.0, port 33307, three isolated schemas | [environment-facts](verification/environment-facts.log) |
| Observed | Office backend compile/tests | Never run | Verified: 6 tests, 0 failures, real MySQL | [office-maven-test](verification/office-maven-test.log) |
| Observed | College backend compile/tests | Java 25/Boot 4 mismatch; never run | Verified: Java 21/Boot 3.5.0, 5 tests, 0 failures | [college-maven-test-corrected](verification/college-maven-test-corrected.log) |
| Observed | Office frontend install/build | Dependencies absent; never built | Verified: npm install; production build, 439 modules | [build notes](verification/office-changes.md), [install log](verification/office-npm-install.log) |
| Observed | College copied frontend | Only original frontend previously built | Verified: copied frontend install/build, 116 modules | [college-frontend-build](verification/college-frontend-build.log) |
| Observed | Office real API and restart | Never started / no database test | Verified: register, login, role denial, linked task write, safe DTOs, restart persistence | [office-live-smoke](verification/office-live-smoke.log) |
| Observed | College real API and restart | Never started / no database test | Verified: register, login, role denial, course/enrollment writes, duplicate409, restart persistence | [college-live-smoke](verification/college-live-smoke.log) |
| Observed | Starter backend/Flyway | Suggested only | Verified: V1 applied; 9 Java/MySQL/HTTP-client tests passed | [starter-maven-test](verification/starter-maven-test.log) |
| Observed | Starter frontend tests/build | Suggested only | Verified: 6 tests and production build | [frontend-tests-recorded](verification/frontend-tests-recorded.log) |
| Observed | Python service tests | Suggested only | Verified: 3 pytest tests | [python-tests-final](verification/python-tests-final.log) |
| Observed | Multipart and Range HTTP | No implementation | Verified: safe upload, MIME/signature denial, exact closed/suffix/open range bytes, 206/416 | [starter-live-smoke](verification/starter-live-smoke.log) |
| Observed | Spring -> actual Python / down fallback | No integration | Verified: actual FastAPI response and unavailable fallback; separate read-timeout test | [starter-live-smoke](verification/starter-live-smoke.log) |
| Observed | Native React audio seeking | Not exercised in browser | Verified: headless Edge WAV decode/playback/seek/resume and native206 | [browser-audio](verification/browser-audio.log) |
| Observed | Broken office dashboard | Only source inference | Verified: real admin login, dashboard render/reload, zero page errors | [office-browser](verification/office-browser.log) |
| Observed | Office import case | 12 source mismatches | Verified: original12; revised0 across84 active relative imports | [office-imports](verification/office-imports.log) |
| Observed | Maven original transitive versions | Unresolved | Verified: dependency:tree resolved both original POMs | [office-original-dependencies](verification/office-original-dependencies.log), [college-original-dependencies](verification/college-original-dependencies.log) |
| Observed | Compose syntax/env interpolation | Suggested only | Verified configuration; container runtime remains Unverified | [compose-config](verification/compose-config.log) |

**Observed:** Test totals are 20 Java tests (office 6 + college 5 + starter 9), 6 frontend tests, and 3 Python tests: 29 passing tests. Real HTTP assertions additionally passed office 11, college 22 and starter 43, including repeated CSRF fetches. Browser checks are separate from those unit/integration counts.

**Observed:** Native audio evidence is a generated three-second PCM WAV in headless Microsoft Edge: duration=3, currentTime advanced, seek to2 seconds completed, playback resumed, native stream received206, and no page errors were recorded. This establishes the tested browser/format behavior; it does not establish physical speaker output, every codec/device, or trained-model quality.

## Remaining externally blocked checks

| Classification | Behavior | Why it remains unverified | Recorded attempt / boundary |
| --- | --- | --- | --- |
| Unverified | Docker container build/up and volume restart | Docker client is installed, but neither default nor Desktop Linux engine pipe was available; Desktop was launched hidden and 18 engine readiness probes still failed | verification/docker-retry.log and docker-retry-results.json; Compose config validates |
| Unverified | Real Google provider callback/login/role/denial | No live Google client credentials or registered callback were supplied; Google is opt-in in the copied backend/frontend | Local password/session flows tested; source safeguards compiled; no external-provider success claim |
| Observed | Trained music ML predictions/accuracy | No trained model, weights or dataset were supplied; starter Python computes deterministic RMS features | Actual service transport/fallback tested; a trained-model implementation is future Recommendation |
| Observed | Untested UI/domain extensions | Browser coverage is office admin/dashboard and starter auth/upload/audio; source absence of full attendance editing, account linking, quotas, grading and similar modules remains documented | Source findings retained; no claim that every advertised future module was implemented/tested |

**Recommendation:** Enable a working Docker engine and rerun Compose build/up before claiming container deployment. Configure real Google credentials and callback plus required activation/link/profile workflows before claiming provider integration. Add domain-specific models/features with their own tests when required.

## Environment and exact setup

**Observed:** Java 21.0.10 was already installed and was reused. MySQL 8.4.0 portable archive and Maven3.9.9 were downloaded; their identities are in verification/environment-results.json. Node 24.14.0 and Python 3.14.3 were used. Python tests used FastAPI 0.141.1/Uvicorn 0.52.4/pytest 9.1.1/HTTPX 0.28.1/Pydantic 2.13.5, now pinned in requirements.txt.

**Observed:** Portable archive URLs used:

- **Observed:** `https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-8.4.0-winx64.zip`
- **Observed:** `https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.9/apache-maven-3.9.9-bin.zip`

**Observed — executed initialization/provisioning commands:**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\projectexcelr!\verification\start-mysql.ps1'
python verification\provision_mysql.py
```

**Observed:** Initialization used mysqld --initialize-insecure only for the new isolated local data directory, then set a generated root password and database-limited test account. Schemas are rea_office_test, rea_college_test and rea_starter_test; app test ports are18081/18082/18083 and browser proxy15173. No original/project production database was used.

**Observed:** Private credentials are generated in ignored verification/runtime-secrets.json and injected as environment values by run_command.py. They are not copied into guides, public examples, API results or source patches.

**Observed:** Maven required a per-execution R: alias for this workspace's `!` paths; Java Path.toRealPath for temporary-repository JARs also failed while workspace-local paths worked. The final launcher uses the workspace-local Maven/repository through the alias and serializes builds. No system Java installation or execution-policy setting was changed.

## Exact executed command register

**Observed:** The machine-readable register is verification/commands.jsonl. Each row contains the command argument array, working directory, exit code, UTC timestamp, duration and log. Child Java server launches have no terminal exit code in that register; their health/API/restart outcomes are in the live result JSON files. The command table below is generated directly from that register.

| Classification | Name | Exact command | CWD | Exit | Log |
| --- | --- | --- | --- | --- | --- |
| Observed | college-maven-test | `python tools\maven.py -f revised-projects\college\backend\pom.xml test` | `.` | 1 | [college-maven-test.log](verification/college-maven-test.log) |
| Observed | college-maven-diagnostic | `python tools\maven.py -e -f revised-projects\college\backend\pom.xml -DskipTests compile` | `.` | 1 | [college-maven-diagnostic.log](verification/college-maven-diagnostic.log) |
| Observed | college-maven-workspace-repo | `python tools\maven.py -e -f revised-projects\college\backend\pom.xml -DskipTests compile` | `.` | 1 | [college-maven-workspace-repo.log](verification/college-maven-workspace-repo.log) |
| Observed | college-maven-forked-compiler | `python tools\maven.py -Dmaven .repo.local=C:\Users\user\AppData\Local\Temp\rea-projectexcelr-runtime\m2 -Dmaven .compiler.fork=true -f revised-projects\college\backend\pom.xml -DskipTests compile` | `.` | 1 | [college-maven-forked-compiler.log](verification/college-maven-forked-compiler.log) |
| Observed | college-maven-alias | `python tools\maven.py -e -f revised-projects\college\backend\pom.xml -DskipTests compile` | `.` | 1 | [college-maven-alias.log](verification/college-maven-alias.log) |
| Observed | starter-maven-test | `python tools\maven.py -f starter\backend\pom.xml test` | `.` | 0 | [starter-maven-test.log](verification/starter-maven-test.log) |
| Observed | college-maven-test-final | `python tools\maven.py -f revised-projects\college\backend\pom.xml test` | `.` | 1 | [college-maven-test-final.log](verification/college-maven-test-final.log) |
| Observed | office-maven-test | `python tools\maven.py -f revised-projects\office\backend\pom.xml test` | `.` | 0 | [office-maven-test.log](verification/office-maven-test.log) |
| Observed | college-maven-test-corrected | `python tools\maven.py -f revised-projects\college\backend\pom.xml test` | `.` | 0 | [college-maven-test-corrected.log](verification/college-maven-test-corrected.log) |
| Observed | office-package | `python tools/maven.py -f revised-projects/office/backend/pom.xml -DskipTests package` | `.` | 0 | [office-package.log](verification/office-package.log) |
| Observed | college-package | `python tools/maven.py -f revised-projects/college/backend/pom.xml -DskipTests package` | `.` | 0 | [college-package.log](verification/college-package.log) |
| Observed | starter-package | `python tools/maven.py -f starter/backend/pom.xml -DskipTests package` | `.` | 0 | [starter-package.log](verification/starter-package.log) |
| Observed | office-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\revised-projects\office\backend\target\office-management-backend-0.0.1-SNAPSHOT.jar` | `./revised-projects/office/backend` | None | [office-live-server.log](verification/office-live-server.log) |
| Observed | office-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\revised-projects\office\backend\target\office-management-backend-0.0.1-SNAPSHOT.jar` | `./revised-projects/office/backend` | None | [office-live-server.log](verification/office-live-server.log) |
| Observed | office-live-smoke | `python verification/live_smoke.py --project office` | `.` | 0 | [office-live-smoke.log](verification/office-live-smoke.log) |
| Observed | college-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\revised-projects\college\backend\target\college-management-system-0.0.1-SNAPSHOT.jar` | `./revised-projects/college/backend` | None | [college-live-server.log](verification/college-live-server.log) |
| Observed | college-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\revised-projects\college\backend\target\college-management-system-0.0.1-SNAPSHOT.jar` | `./revised-projects/college/backend` | None | [college-live-server.log](verification/college-live-server.log) |
| Observed | college-live-smoke | `python verification/live_smoke.py --project college` | `.` | 0 | [college-live-smoke.log](verification/college-live-smoke.log) |
| Observed | starter-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\starter\backend\target\rea-starter-0.0.1-SNAPSHOT.jar` | `./starter/backend` | None | [starter-live-server.log](verification/starter-live-server.log) |
| Observed | python-tests-final | `python -m pytest -q` | `./starter/ml-service` | 0 | [python-tests-final.log](verification/python-tests-final.log) |
| Observed | starter-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\starter\backend\target\rea-starter-0.0.1-SNAPSHOT.jar` | `./starter/backend` | None | [starter-live-server.log](verification/starter-live-server.log) |
| Observed | starter-live-smoke | `python verification/live_smoke.py --project starter --keep-server` | `.` | 0 | [starter-live-smoke.log](verification/starter-live-smoke.log) |
| Observed | browser-audio | `python verification\browser_audio.py` | `.` | 0 | [browser-audio.log](verification/browser-audio.log) |
| Observed | frontend-tests-final | `npm.cmd test` | `./starter/frontend` | 0 | [frontend-tests-final.log](verification/frontend-tests-final.log) |
| Observed | frontend-build-final | `npm.cmd run build` | `./starter/frontend` | 0 | [frontend-build-final.log](verification/frontend-build-final.log) |
| Observed | college-npm-install | `npm.cmd install --cache E:\projectexcelr!\tools\npm-cache --no-audit --no-fund` | `./revised-projects/college/frontend` | 0 | [college-npm-install.log](verification/college-npm-install.log) |
| Observed | college-frontend-build | `npm.cmd run build` | `./revised-projects/college/frontend` | 0 | [college-frontend-build.log](verification/college-frontend-build.log) |
| Observed | frontend-tests-recorded | `npm.cmd test` | `./starter/frontend` | 0 | [frontend-tests-recorded.log](verification/frontend-tests-recorded.log) |
| Observed | frontend-build-recorded | `npm.cmd run build` | `./starter/frontend` | 0 | [frontend-build-recorded.log](verification/frontend-build-recorded.log) |
| Observed | compose-config | `E:\Docker\App\resources\cli-plugins\docker-compose.exe --env-file starter\.env.example -f starter\docker-compose.yml config --quiet` | `.` | 0 | [compose-config.log](verification/compose-config.log) |
| Observed | office-imports | `python verification\check_office_imports.py` | `.` | 0 | [office-imports.log](verification/office-imports.log) |
| Observed | office-start | `"C:\Program Files\Java\jdk-21.0.10\bin\java.exe" -Dfile.encoding=UTF-8 -jar R:\revised-projects\office\backend\target\office-management-backend-0.0.1-SNAPSHOT.jar` | `./revised-projects/office/backend` | None | [office-live-server.log](verification/office-live-server.log) |
| Observed | office-browser | `python verification\browser_office.py` | `.` | 0 | [office-browser.log](verification/office-browser.log) |
| Observed | office-original-dependencies | `python tools/maven.py -f Office_Management_App-main/Office_Management_BackendApp/pom.xml dependency:tree` | `.` | 0 | [office-original-dependencies.log](verification/office-original-dependencies.log) |
| Observed | college-original-dependencies | `python tools/maven.py -f ReactJavaDemoApplication-main/college-management-system/pom.xml dependency:tree` | `.` | 0 | [college-original-dependencies.log](verification/college-original-dependencies.log) |
| Observed | environment-facts | `python verification\environment_probe.py` | `.` | 0 | [environment-facts.log](verification/environment-facts.log) |
| Observed | docker-retry | `python verification\retry_docker.py` | `.` | 1 | [docker-retry.log](verification/docker-retry.log) |
| Observed | delivery-validation | `python verification\validate_delivery.py` | `.` | 0 | [delivery-validation.log](verification/delivery-validation.log) |
| Observed | test-teardown | `python verification\stop_test_services.py` | `.` | 0 | [test-teardown.log](verification/test-teardown.log) |

**Observed:** Office npm install was executed separately before the register helper existed: `npm.cmd install --cache E:\projectexcelr!\tools\npm-cache --no-audit --no-fund`, cwd revised-projects/office/frontend, exit0, 250 packages; log verification/office-npm-install.log. Office build was executed as `npm.cmd run build`, cwd revised-projects/office/frontend, exit0, Vite 8.0.16/439 modules; recorded worker notes and artifacts are in verification/office-changes.md. The final per-file corrections do not change that built office source.

## Failed attempts and corrections

| Classification | Attempt | Actual failure | Correction / final evidence |
| --- | --- | --- | --- |
| Observed | Initial Maven startup | `!` archive path interpreted incorrectly | Per-process drive alias and workspace-local runtime; all final compiles/tests pass |
| Observed | Temporary Maven repo compile | JAR metadata real-path AccessDenied; read probe could read bytes | Workspace-local repo plus alias; serial builds |
| Observed | Forked diagnostic command | PowerShell split dotted -D options into separate arguments | Direct Python argument arrays; diagnostic retained |
| Observed | College compile | Generic wildcard capture in Google authority list | Explicit ArrayList<GrantedAuthority>; compiled after fix |
| Observed | College first full suite | 5 tests/1 failure: fixture assumed different bootstrap credentials | Unique BCrypt admin fixture; corrected5/5 pass |
| Observed | Frontend log wrapper | npm exited0 but printing Unicode checkmarks raised cp1252 error | UTF-8 output; final wrapper/test/build commands exit0 |
| Observed | Docker default invocation | Default config read denied / engine pipe absent | Local config and plugin path validate Compose; Desktop retry still engine unavailable |

## Preserved finding IDs

| Classification | Original ID | Retained finding | Updated evidence / scope |
| --- | --- | --- | --- |
| Observed | F01 | Two independent project pairs | Original source layouts and copied-source notes |
| Observed | F02 | Direct stacks/libraries | Original manifests/locks retained; both original dependency graphs now resolved |
| Observed | F03 | Components/state/router/styles | Full office/college source sections retained |
| Observed | F04 | Backend modules/schema/API/algorithms | Original86 Java files; revised local behavior exercised |
| Observed | F05 | JWT versus session/CSRF/OAuth | Original configurations retained; revised local flows tested |
| Observed | F06 | Duplicate43-file office React copy | Original retained;17 duplicate roots/files removed only from copied backend |
| Observed | F07 | Original12 case mismatches | Repeated original12/revised0 scan; office build passed |
| Observed | F08 | Dashboard/DTO/checklist defects | Original findings retained; corrected copy tested and patched |
| Observed | F09 | Public role, raw user, ownership gaps | Original source findings retained; copied role/DTO/owner checks tested |
| Inference | F10 | Original Google identity/authority/status consequences | Source safeguards corrected; real Google remains Unverified without credentials |
| Observed | F11 | College frontend bundle | Original result retained; copied frontend build also passed |
| Observed | F12 | Java 21 versus Java 25 target | Original target retained; copied college/starter migrated and compiled on21 |
| Observed | F13 | Previously absent runtime/persistence evidence | Replaced for revised copies by real MySQL, API and restart results |
| Recommendation | F14 | Reusable analogous-project method | 188-line blueprint, retained reference examples and concrete starter |

**Observed:** The untouched originals' defects remain evidence; successful revised/starter executions do not erase those findings. The original full report remains verbatim in docs/archive. Source-only projections and untested consequences remain labelled Inference rather than being promoted to runtime facts.

**Observed — teardown:** Verification services were stopped after testing; installed portable binaries and isolated test data were retained. See verification/teardown-results.json and the recorded teardown command.
