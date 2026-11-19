# Change log

**Observed:** Changes below address the six requested improvements. Originals remain preserved; code corrections are applied in revised-projects copies. Exact source deltas are in patches/office.patch and patches/college.patch, including removed duplicate copy files. Runtime evidence is in REA_EVIDENCE_LEDGER.md.

| Classification | Point | Change and resulting behavior |
| --- | --- | --- |
| Observed | 1 | Reused installed Java 21; downloaded/provisioned MySQL 8.4.0 and Maven3.9.9; isolated three schemas/ports and private credentials |
| Observed | 1 | Compiled/tested/packaged/started office and college copies; tested actual register/login/role/core write/restart persistence |
| Observed | 1 | Office npm install/build; college copied frontend install/build; actual browser dashboard and native audio checks |
| Observed | 1 | Recorded exact commands, versions, pass/fail outcomes, failed attempts and archive identities |
| Observed | 2 | College copy Java 25/Boot 4.1.2 -> Java 21/Boot 3.5.0; starter pins21/3.5.0; updated starter names/test artifacts/wrapper and optional Google profile |
| Observed | 3 | Read complete 1,357-line guide; preserved verbatim archive; split 188-line blueprint, full office/college evidence, ledger and README index |
| Observed | 3 | Retained longer original reconstruction examples in REA_REFERENCE_IMPLEMENTATION.md; explicit claim labels and original/copy scope |
| Observed | 4 | Complete multipart MIME/signature/size validation, UUID storage names, persisted owner-scoped metadata and configured path |
| Observed | 4 | Bounded GET/HEAD Range audio,206/416, native React player; exact bytes and real WAV playback/seeking tested |
| Observed | 4 | RestClient -> FastAPI with connect/read timeouts and unavailable fallback; real HTTP/Python service tested; illustrative RMS clearly labelled |
| Observed | 5 | Concrete FlywayV1 with blueprint tables/media; applied to real MySQL |
| Observed | 5 | Compose MySQL/backend/frontend plus optional ML, Dockerfiles/env example/volumes/proxy/.dockerignore; configuration validates |
| Observed | 5 | Backend context/auth/role/object/upload/Range/timeout tests, frontend Axios/auth/player tests and Python tests;29 total pass |
| Observed | 6 | Removed duplicated React only from copied office backend; fixed12 original case mismatches and built revised frontend |
| Observed | 6 | Forced public role, safe DTOs, active-role/ownership checks, private admin bootstrap, validated inputs and400/404/409 advice |
| Observed | 6 | Fixed dashboard count/list, atomic checklist creation, reducer guards, Axios network handling, profile routes and rejected-form behavior |
| Observed | 6 | College session ID/CSRF/context persistence, safe user projection, attendance validation, error statuses, optional Google/UI/navigation fixes |

## Per-file source changes

**Observed:** Every changed/new/deleted first-party copied-source file is listed below. Package locks are retained as dependency-install evidence. Generated target/dist/node_modules are excluded from source deltas.

| Classification | Point | Action | Copy path |
| --- | --- | --- | --- |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/eslint.config.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/index.html` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/package-lock.json` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/package.json` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/pom.xml` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/public/favicon.svg` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/public/icons.svg` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/README.md` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Api/AxiosConfig.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/adminDashboard.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/adminProfile.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/footer.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/globalTable.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/login.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/navbar.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/sidebar.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/assets/AllPagesCss/signup.css` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Components/Common/ProtectedRoute.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Components/Common/RoleRoute.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Components/Layouts/Footer.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Components/Layouts/Navbar.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Components/Layouts/Sidebar.jsx` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/ConfigPack/AdminInitializer.java` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/ConfigPack/ApiExceptionHandler.java` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/ConfigPack/CurrentUser.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ConfigPack/JwtFilter.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ConfigPack/SecurityConfig.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/AttendanceController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/AuthController.java` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/HealthController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/LeaveController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/ReportController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/TaskController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/TaskPointController.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ControllerPack/UserController.java` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/DTOPack/ApiDtos.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/EntityPack/Attendance.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/EntityPack/Task.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/EntityPack/TaskPoint.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/EntityPack/User.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/RepositoryPack/UserRepository.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/java/BackendApp/ServicePack/AuthService.java` |
| Observed | 6 | Added | `revised-projects/office/backend/src/main/java/BackendApp/ServicePack/OfficeService.java` |
| Observed | 6 | Changed in copy | `revised-projects/office/backend/src/main/resources/application.properties` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/main.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/OfficeManagementApplication.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/AdminDashboard.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/AdminProfile.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/Attendance.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/Employees.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/Leaves.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Admin/Tasks.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Authentication/LoginPage.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Authentication/SignupPage.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Employee/EmployeeDashboard.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Employee/EmployeeProfile.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Employee/MyAttendance.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Employee/MyLeaves.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/Employee/MyTasks.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/LeaveManagement/ApplyLeaves.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/TaskManagement/CreateTaskPopup.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/TaskManagement/EditTaskPopup.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/UserManagement/AddEmployeePopup.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Pages/UserManagement/EditEmployeePopup.jsx` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/attendanceSlice.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/authSlice.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/employeeSlice.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/leaveSlice.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/store.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Redux/taskSlice.js` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/src/Routes/AppRoutes.jsx` |
| Observed | 6 | Added | `revised-projects/office/backend/src/test/java/BackendApp/OfficeSecurityIntegrationTests.java` |
| Observed | 6 | Removed in copy | `revised-projects/office/backend/vite.config.js` |
| Observed | 6 | Added | `revised-projects/office/frontend/.env.example` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Api/AxiosConfig.js` |
| Observed | 6 | Added | `revised-projects/office/frontend/src/Components/Common/EmployeePage.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Components/Common/RoleRoute.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Components/Layouts/Navbar.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Components/Layouts/Sidebar.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/main.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/OfficeManagementApplication.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Admin/AdminDashboard.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Admin/Attendance.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Admin/Employees.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Admin/Leaves.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Admin/Tasks.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Authentication/LoginPage.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Authentication/SignupPage.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Employee/EmployeeDashboard.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Employee/EmployeeProfile.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Employee/MyAttendance.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Employee/MyLeaves.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/Employee/MyTasks.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/LeaveManagement/ApplyLeaves.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/TaskManagement/CreateTaskPopup.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/UserManagement/AddEmployeePopup.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Pages/UserManagement/EditEmployeePopup.jsx` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/attendanceSlice.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/authSlice.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/employeeSlice.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/leaveSlice.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/store.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Redux/taskSlice.js` |
| Observed | 6 | Changed in copy | `revised-projects/office/frontend/src/Routes/AppRoutes.jsx` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/.mvn/wrapper/maven-wrapper.properties` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/pom.xml` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/main/java/com/example/college/common/ApiExceptionHandler.java` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/main/java/com/example/college/common/ConflictException.java` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/main/java/com/example/college/common/NotFoundException.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/config/DataInitializer.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/config/SecurityConfig.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/controller/AdminController.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/controller/AuthController.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/controller/FacultyController.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/dto/RegisterRequest.java` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/main/java/com/example/college/dto/UserResponse.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/entity/User.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/security/CurrentUser.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/security/GoogleLoginSuccessHandler.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/service/AccountService.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/java/com/example/college/service/CollegeService.java` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/main/resources/application-google.properties` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/main/resources/application.properties` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/test/java/com/example/college/CollegeApiIntegrationTests.java` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/backend/src/test/java/com/example/college/CollegeManagementSystemApplicationTests.java` |
| Observed | 2,6 | Added | `revised-projects/college/backend/src/test/resources/application-test.properties` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/frontend/.env.example` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/frontend/src/components/AppLayout.jsx` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/frontend/src/pages/AdminCourses.jsx` |
| Observed | 2,6 | Changed in copy | `revised-projects/college/frontend/src/pages/Login.jsx` |

## New starter and verification files

**Observed:** New starter files provide concrete implementation, configuration and tests. Verification helpers/results/logs provide recorded evidence; generated/private data stays excluded from source control.

| Classification | Point | Path |
| --- | --- | --- |
| Observed | 5 | `starter/.env.example` |
| Observed | 5 | `starter/.gitignore` |
| Observed | 5 | `starter/backend/.dockerignore` |
| Observed | 5 | `starter/backend/Dockerfile` |
| Observed | 5 | `starter/backend/pom.xml` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/Accounts.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/ApiException.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/ApiExceptionHandler.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/Application.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/AuthController.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/BootstrapAdmin.java` |
| Observed | 4,5 | `starter/backend/src/main/java/com/example/starter/MediaController.java` |
| Observed | 4,5 | `starter/backend/src/main/java/com/example/starter/MediaFiles.java` |
| Observed | 4,5 | `starter/backend/src/main/java/com/example/starter/MlClient.java` |
| Observed | 4,5 | `starter/backend/src/main/java/com/example/starter/MlController.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/SecurityConfig.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/WorkController.java` |
| Observed | 5 | `starter/backend/src/main/java/com/example/starter/WorkItems.java` |
| Observed | 5 | `starter/backend/src/main/resources/application.properties` |
| Observed | 5 | `starter/backend/src/main/resources/db/migration/V1__init.sql` |
| Observed | 4,5 | `starter/backend/src/test/java/com/example/starter/MlClientTest.java` |
| Observed | 5 | `starter/backend/src/test/java/com/example/starter/StarterIntegrationTest.java` |
| Observed | 5 | `starter/docker-compose.yml` |
| Observed | 5 | `starter/frontend/.dockerignore` |
| Observed | 5 | `starter/frontend/.env.example` |
| Observed | 5 | `starter/frontend/Dockerfile` |
| Observed | 5 | `starter/frontend/index.html` |
| Observed | 5 | `starter/frontend/nginx.conf` |
| Observed | 5 | `starter/frontend/package-lock.json` |
| Observed | 5 | `starter/frontend/package.json` |
| Observed | 5 | `starter/frontend/src/api/client.js` |
| Observed | 5 | `starter/frontend/src/App.jsx` |
| Observed | 5 | `starter/frontend/src/auth/AuthContext.jsx` |
| Observed | 4,5 | `starter/frontend/src/components/AudioPlayer.jsx` |
| Observed | 5 | `starter/frontend/src/main.jsx` |
| Observed | 5 | `starter/frontend/src/styles.css` |
| Observed | 5 | `starter/frontend/src/test/auth.test.jsx` |
| Observed | 5 | `starter/frontend/src/test/client.test.js` |
| Observed | 5 | `starter/frontend/src/test/player.test.jsx` |
| Observed | 5 | `starter/frontend/src/test/setup.js` |
| Observed | 5 | `starter/frontend/vite.config.js` |
| Observed | 4,5 | `starter/ml-service/.dockerignore` |
| Observed | 4,5 | `starter/ml-service/app.py` |
| Observed | 4,5 | `starter/ml-service/Dockerfile` |
| Observed | 4,5 | `starter/ml-service/requirements.txt` |
| Observed | 4,5 | `starter/ml-service/test_app.py` |
| Observed | 5 | `starter/README.md` |
| Observed | 3 | `README.md` |
| Observed | 3 | `REA_BLUEPRINT.md` |
| Observed | 3 | `REA_OFFICE_ANALYSIS.md` |
| Observed | 3 | `REA_COLLEGE_ANALYSIS.md` |
| Observed | 3 | `REA_EVIDENCE_LEDGER.md` |
| Observed | 3 | `REA_MEDIA_AND_ML_ADDON.md` |
| Observed | 3 | `REA_REFERENCE_IMPLEMENTATION.md` |
| Observed | 3 | `REA_FULLSTACK_PROJECT_GUIDE.md` |
| Observed | 3 | `docs/archive/REA_FULLSTACK_PROJECT_GUIDE.original.md` |
| Observed | 1,4,5,6 | `verification/run_command.py` |
| Observed | 1,4,5,6 | `verification/live_smoke.py` |
| Observed | 1,4,5,6 | `verification/browser_audio.py` |
| Observed | 1,4,5,6 | `verification/browser_office.py` |
| Observed | 1,4,5,6 | `verification/check_office_imports.py` |
| Observed | 1,4,5,6 | `verification/provision_mysql.py` |
| Observed | 1,4,5,6 | `verification/start-mysql.ps1` |
| Observed | 1,4,5,6 | `verification/environment_probe.py` |
| Observed | 1,4,5,6 | `verification/retry_docker.py` |
| Observed | 1,4,5,6 | `verification/build_docs.py` |
| Observed | 1,4,5,6 | `verification/build_media_doc.py` |
| Observed | 1,4,5,6 | `verification/finalize_documents.py` |
| Observed | 1,4,5,6 | `verification/validate_delivery.py` |
| Observed | 1,4,5,6 | `verification/stop_test_services.py` |
| Observed | 1,4,5,6 | `verification/commands.jsonl` |
| Observed | 1,4,5,6 | `tools/maven.py` |
| Observed | 1,4,5,6 | `.gitignore` |
| Observed | 1,4,5,6 | `verification/environment-results.json` |
| Observed | 1,4,5,6 | `verification/docker-retry-results.json` |
| Observed | 1,4,5,6 | `verification/browser-audio-results.json` |
| Observed | 1,4,5,6 | `verification/office-browser-results.json` |
| Observed | 1,4,5,6 | `verification/office-live-results.json` |
| Observed | 1,4,5,6 | `verification/college-live-results.json` |
| Observed | 1,4,5,6 | `verification/starter-live-results.json` |
| Observed | 1,4,5,6 | `verification/teardown-results.json` |
| Observed | 1,4,5,6 | `verification/office-removed-duplicate-paths.json` |
| Observed | 1,4,5,6 | `verification/office-import-case-fixes.txt` |
| Observed | 1,4,5,6 | `verification/office-import-validation.txt` |
| Observed | 1,4,5,6 | `verification/office-changed-source-files.txt` |

## Final verification table

| Classification | Requirement | Final state |
| --- | --- | --- |
| Observed | Point 1: backend/MySQL/core flows/restart | Verified for both revised copies |
| Observed | Point 2: Java 21/Boot 3.5.x | Verified compilation/startup with pinned3.5.0 |
| Observed | Point 3: short/split/preserved evidence | Delivered 188-line blueprint and all full analyses/index/archive |
| Observed | Point 4: upload/Range/Python/React | Verified Java/API/Python/React and real Edge WAV seek |
| Observed | Point 5: migrations and tests | Verified V1/MySQL and29 tests; concrete Compose/config supplied |
| Unverified | Point 5: actual Docker container startup | Engine unavailable after hidden Desktop launch and18 retry probes; config validation passed |
| Observed | Point 6: duplicate/import/role/DTO/dashboard/validation fixes | Applied to copies; tests/build/browser checks passed |

**Observed:** Remaining source feature absences and real Google-provider limits are retained in the analyses/ledger. No untouched original, every screen/codec/device or trained ML model is declared fully working.
