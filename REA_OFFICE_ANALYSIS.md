# Office source evidence and applied-copy corrections

**Observed:** The detailed evidence below is retained from the original source snapshot; its paths and defects describe the untouched original. Executed checks apply to the clearly named revised copy or starter and are summarized in the ledger. Original response projections are Inference where derived from getters/configuration rather than exercised HTTP. Labels apply to the immediately following claim, list item, table row/cell or code block.

## Office management: Java backend evidence and reconstruction notes

**Observed:** Scope: `Office_Management_App-main/Office_Management_BackendApp/`. Evidence is source inspection, not a live successful execution. In source references below, `OB/` means this folder and `J/` means `OB/src/main/java/BackendApp/`. Dates: 2026-11-18. Secrets are deliberately omitted. Distinguish observed implementation from the recommended corrections below.

### Stack, dependencies and application structure

| Classification | Component | Observed version/use | Evidence |
| --- | --- | --- | --- |
| Observed | Java | Java 21 source/target | `OB/pom.xml`, java.version and compiler configuration |
| Observed | Spring Boot | 3.5.0; standalone Java application | `OB/pom.xml`; `J/OfficeManagementBackendApp.java:4` |
| Observed | Spring Web MVC | REST controllers, Jackson JSON, embedded server; Boot-managed dependency versions | `spring-boot-starter-web`; `J/ControllerPack/` |
| Observed | Spring Security | Filter chain, method/path authorization, BCrypt | `spring-boot-starter-security`; `J/ConfigPack/SecurityConfig.java:25` |
| Observed | Spring Data JPA / Hibernate | ORM, generated repository implementations and MySQL schema updating | `spring-boot-starter-data-jpa`; all `RepositoryPack` interfaces |
| Observed | MySQL Connector/J | Runtime database driver; MySQL on localhost:3306 | `OB/pom.xml`; `OB/src/main/resources/application.properties:5` |
| Observed | JJWT | `jjwt-api`, `jjwt-impl`, `jjwt-jackson` all 0.11.5; HS256 JWTs | `OB/pom.xml`; `J/ConfigPack/JwtUtil.java:28` |
| Observed | Jakarta Persistence | Entity, relation, lifecycle callback annotations | `J/EntityPack/` |
| Observed | Jakarta Validation starter | Declared, but no `@Valid` or constraint use found in inspected Java source | `OB/pom.xml`; bounded search `J/` |
| Observed | Lombok | Declared provided dependency; inspected entities/DTOs use explicit accessors | `OB/pom.xml`; `J/EntityPack/`, `J/DTOPack/` |
| Observed | Spring Boot Test starter | Declared test dependency; no Java test sources present in this project source tree | `OB/pom.xml`; bounded `OB/src/` inventory |
| Observed | Maven plugins | Spring Boot packaging and Maven compiler plugin | `OB/pom.xml` |

**Observed:** Transitive components such as Jackson, Hibernate, Tomcat and Spring Framework arrive through Boot starters. Their exact original-POM versions have now been resolved by dependency:tree; see the observed appendix below. Swagger URLs are permitted by the security configuration, but no OpenAPI/Swagger dependency exists in the POM. A `spring.thymeleaf.cache=false` setting does not establish a Thymeleaf dependency; the supplied UI is React.

**Observed:** The entry point uses `@SpringBootApplication` under package `BackendApp`, so component scanning discovers subpackages. `ControllerPack` receives HTTP requests; `ServicePack` performs business operations and DTO conversion; `RepositoryPack` extends `JpaRepository<entity, Long>`; `EntityPack` maps tables; `DTOPack` contains wire objects; `ConfigPack` configures JWT, passwords, CORS and static uploads. Injection mostly uses `@Autowired` fields; `TaskController` and `SecurityConfig` use constructor injection. `ReportService` is an empty class; the report controller directly calls repository counts instead of using that class.

**Observed:** The backend folder also contains a copied React/Vite project and frontend `src` folders. Java compilation uses `src/main/java`; those extra JSX files are not the backend architecture. Parent documentation should establish which frontend copy is authoritative.

### Database model

**Inference:** All primary IDs are `Long` with `GenerationType.IDENTITY` (MySQL generated identity). String-backed enums use `@Enumerated(EnumType.STRING)`. Default physical column names other than explicit joins are inferred from Spring/Hibernate naming conventions, not verified against a live schema.

| Classification | Entity / table | Fields and constraints | Relationships / lifecycle |
| --- | --- | --- | --- |
| Observed | `User` / `users` | `id`; `name`; `email` unique/not null; `contactNumber` unique; `password`; `designation`; `joiningDate: LocalDate`; `active: Boolean=true`; `profileImage: String LONGTEXT`; `role` | One user has many attendance and leave records with `cascade=ALL, orphanRemoval=true`; assignedTasks and createdTasks collections have no cascade. All four reverse collections have `@JsonIgnore`. Source `J/EntityPack/User.java:11`. |
| Observed | `Task` / `tasks` | `id`; `title`; `description` length 1000; `status`; `priority`; `startDate`, `endDate`, `createDate` as LocalDate | EAGER many-to-one `assignedUser` via `assigned_user_id`; EAGER many-to-one `createdBy` via `created_by`; one-to-many taskPoints with ALL cascade and orphan removal. `@PrePersist` replaces createDate with server `LocalDate.now()`. Source `J/EntityPack/Task.java:9`. |
| Observed | `TaskPoint` / `task_points` | `id`; `pointTitle` length 500; `completed: Boolean=false`; `remark` length 2000 | LAZY many-to-one task via `task_id`, `@JsonIgnore`. Source `J/EntityPack/TaskPoint.java:7`. |
| Observed | `Attendance` / `attendance` | `id`; `attendanceDate: LocalDate` not null; checkInTime/checkOutTime as LocalDateTime; status not null; workingHours Double; remarks length 500; createdAt/updatedAt | LAZY many-to-one user via mandatory `user_id`. PrePersist stamps both audit times; PreUpdate stamps updatedAt and computes elapsed minutes/60.0 when both times exist. No composite uniqueness declared for (user,date). Source `J/EntityPack/Attendance.java:9`. |
| Observed | `LeaveRequest` / `leave_requests` | `id`; `leaveType` not null; `startDate`/`endDate` LocalDate not null; reason length 1000; status not null/default PENDING | LAZY many-to-one user via mandatory `user_id`, with `@JsonIgnore`. No overlap or balance constraints. Source `J/EntityPack/LeaveRequest.java:8`. |

**Observed:** Enums: Role `ADMIN, EMPLOYEE`; TaskStatus `PENDING, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED`; TaskPriority `LOW, MEDIUM, HIGH, CRITICAL`; AttendanceStatus `PRESENT, ABSENT, HALF_DAY, LEAVE, WFH`; LeaveStatus `PENDING, APPROVED, REJECTED`. Sources: corresponding `J/EntityPack/*.java`.

**Inference:** Deleting a user cascades attendance/leave deletion, but tasks referencing that user are not automatically deleted or reassigned; a live relational FK can prevent deletion while those tasks remain. This is a schema/service inference and should be tested. Deleting a task cascades its task points.

**Observed:** `User.setProfileImage` strips literal quote characters and trims the string (`J/EntityPack/User.java:138`). The database allows LONGTEXT image representations, including data URL strings; no dedicated object-storage integration or multipart controller is found. Static `GET /uploads/**` maps to filesystem `uploads/` relative to the Java process working directory (`J/ConfigPack/WebConfig.java:13`), and that path is public in security. This provides serving only; there is no observed upload API.

### Wire formats and complete HTTP inventory

**Observed:** The backend listens on `http://localhost:8080` by current configuration. API prefix is `/api`. Requests and responses use JSON except controller String responses, which are plain text, and void responses, which have no body. Controllers return ordinary Java values without `ResponseEntity` or explicit status annotations; successful create and void operations consequently use default Spring success handling rather than a deliberately designed 201/204 contract. Error mapping is inconsistent: services commonly throw plain `RuntimeException`, and no custom global exception mapper was found. Invalid inputs/missing rows can therefore become framework error responses rather than meaningful 400/404 responses. `UserService.getUserById` and update return null for absent rows rather than throwing.

**Observed:** Notation: `A`=ADMIN; `E`=EMPLOYEE; `A/E`=either. Permission columns report the actual filter chain, not desired UI permissions. Every listed route corresponds to an annotated controller method.

| Classification | Method | Path | Actual allowed caller | Request | Response / source |
| --- | --- | --- | --- | --- | --- |
| Observed | POST | `/api/auth/register` | Public | User entity fields (including client role) | **Inference:** User entity; `AuthController.java:20` |
| Observed | POST | `/api/auth/login` | Public | `{email,password}` (`LoginRequest`) | **Inference:** `{token,userId,name,role}`; `AuthController.java:25`; `LoginResponse.java:5` |
| Observed | POST | `/api/auth/signup` | Public filter path, but service requires an admin Bearer header | `{name,email,password,role,profileImage}` (`UserDTO`); Authorization header required | **Inference:** Plain text `User Created Successfully`; `AuthController.java:32`; `AuthService.java:77` |
| Observed | POST | `/api/users` | A | User entity; password is plaintext on input | **Inference:** Saved User entity; `UserController.java:19` |
| Observed | GET | `/api/users` | A/E | None | **Inference:** User array; `UserController.java:25` |
| Observed | GET | `/api/users/{id}` | A/E | Numeric path ID | **Inference:** User or no body if absent; `UserController.java:31` |
| Observed | PUT | `/api/users/{id}` | A | User fields; omit/blank password to retain existing hash | **Inference:** User or no body if absent; `UserController.java:37` |
| Observed | DELETE | `/api/users/{id}` | A | Numeric ID | **Inference:** No body; `UserController.java:43` |
| Observed | POST | `/api/tasks` | A | Task entity; see example below | **Inference:** TaskDTO; `TaskController.java:30` |
| Observed | GET | `/api/tasks/statuses` | A/E | None | **Inference:** TaskStatus string array; `TaskController.java:37` |
| Observed | GET | `/api/tasks/priorities` | A/E | None | **Inference:** TaskPriority string array; `TaskController.java:42` |
| Observed | GET | `/api/tasks` | A/E | None | **Inference:** TaskDTO array; `TaskController.java:47` |
| Observed | GET | `/api/tasks/{id}` | A/E | Numeric ID | **Inference:** TaskDTO; `TaskController.java:52` |
| Observed | GET | `/api/tasks/user/{userId}` | A/E | Numeric user ID, no ownership restriction | **Inference:** TaskDTO array; `TaskController.java:59` |
| Observed | PUT | `/api/tasks/{id}` | A/E | Full editable Task entity fields | **Inference:** TaskDTO; `TaskController.java:66` |
| Observed | DELETE | `/api/tasks/{id}` | A | Numeric ID | **Inference:** Plain text `Task deleted successfully`; `TaskController.java:74` |
| Observed | POST | `/api/task-points/task/{taskId}` | A/E | `{pointTitle,completed,remark}` | **Inference:** TaskPoint entity without task; `TaskPointController.java:23` |
| Observed | PUT | `/api/task-points/{pointId}` | A/E | `{pointTitle,completed,remark}` (replace all three) | **Inference:** TaskPoint entity without task; `TaskPointController.java:39` |
| Observed | DELETE | `/api/task-points/{pointId}` | A | Numeric ID | **Inference:** No body; `TaskPointController.java:55` |
| Observed | GET | `/api/task-points/task/{taskId}` | A/E | Numeric task ID | **Inference:** TaskPoint array without task; `TaskPointController.java:69` |
| Observed | GET | `/api/task-points/{pointId}` | A/E | Numeric point ID | **Inference:** TaskPoint without task; `TaskPointController.java:83` |
| Observed | POST | `/api/attendance` | A | Attendance entity including `user:{id}`, date/times/status/remarks | **Inference:** Attendance entity; `AttendanceController.java:22` |
| Observed | GET | `/api/attendance` | A/E | None | **Inference:** AttendanceDTO array newest attendanceDate first; `AttendanceController.java:31` |
| Observed | GET | `/api/attendance/{id}` | A/E | Numeric ID | **Inference:** AttendanceDTO; `AttendanceController.java:39` |
| Observed | GET | `/api/attendance/user/{userId}` | A/E | Numeric user ID, no ownership restriction | **Inference:** AttendanceDTO array newest date first; `AttendanceController.java:48` |
| Observed | DELETE | `/api/attendance/{id}` | A | Numeric ID | **Inference:** Plain text `Attendance deleted successfully`; `AttendanceController.java:57` |
| Observed | POST | `/api/leaves` | A/E | LeaveRequest fields; user association has a serialization defect, below | **Inference:** LeaveRequest without user; `LeaveController.java:22` |
| Observed | GET | `/api/leaves` | A/E | None | **Inference:** LeaveDTO array; `LeaveController.java:31` |
| Observed | GET | `/api/leaves/{id}` | A/E | Numeric ID | **Inference:** LeaveDTO; `LeaveController.java:39` |
| Observed | PUT | `/api/leaves/{id}` | A | leaveType/reason/startDate/endDate; optional status | **Inference:** LeaveRequest without user; `LeaveController.java:48` |
| Observed | PUT | `/api/leaves/{id}/approve` | A | No body | **Inference:** LeaveRequest with APPROVED; `LeaveController.java:58` |
| Observed | PUT | `/api/leaves/{id}/reject` | A | No body | **Inference:** LeaveRequest with REJECTED; `LeaveController.java:67` |
| Observed | DELETE | `/api/leaves/{id}` | A | Numeric ID | **Inference:** No body; `LeaveController.java:76` |
| Observed | GET | `/api/reports/dashboard` | Any authenticated JWT principal | None | **Inference:** `{totalUsers,totalTasks,totalLeaves,totalAttendance}` numeric counts; `ReportController.java:31` |

**Observed:** Controller references above are inside `J/ControllerPack/`, DTO references inside `J/DTOPack/`, service references inside `J/ServicePack/`. There are 34 API methods: 3 auth, 5 user, 8 task, 5 task point, 5 attendance, 7 leave and 1 report. No employee-specific leave endpoint exists even though its repository has user filters. There is no annotated attendance PUT endpoint, logout endpoint, refresh-token endpoint, dedicated self-profile endpoint, health endpoint, export-report endpoint or upload endpoint in the inspected Java source. Permitting a path in SecurityConfig does not implement a controller for that path.

**Observed:** DTOs:


**Inference — original example/source projection:**

```text
TaskDTO = {id,title,description,status,priority,startDate,endDate,createDate,
           assignedUserId,assignedUserName,createdById,createdByName}
AttendanceDTO = {id,userId,employeeName,attendanceDate,checkInTime,checkOutTime,
                 workingHours,status,remarks}
LeaveDTO = {id,userId,employeeName,leaveType,startDate,endDate,totalDays,reason,status}
TaskPoint response = {id,pointTitle,completed,remark}
User response = {id,name,email,contactNumber,password,designation,joiningDate,
                 active,profileImage,role} // password hash exposure: fix before reuse
```

**Observed:** `AuthResponseDTO`, `LoginDTO`, `SignupDTO`, and `TaskPointDTO` also exist, but the annotated endpoints do not use them. Do not assume the shapes of these unused classes describe the live API. Jackson formats LocalDate as `YYYY-MM-DD` and LocalDateTime as an ISO date/time without explicit zone; exact runtime serialization was not observed.

**Observed:** Typical task request matching the current entity contract:


**Inference — original example/source projection:**

```json
{
  "title": "Prepare onboarding",
  "description": "Complete the onboarding checklist",
  "status": "PENDING",
  "priority": "HIGH",
  "startDate": "2026-11-18",
  "endDate": "2026-11-20",
  "assignedUser": {"id": 2},
  "createdBy": {"id": 1}
}
```

**Observed:** These numeric IDs must reference real persisted users. Because the source accepts JPA entities directly, resolution and relationship validity are not deliberately checked by the service. The recommended new-project contract should accept `assignedUserId`, load the managed user, and derive createdBy from the authenticated user instead of trusting an input ID.

### Business logic and fundamentals

**Observed:** Authentication: public register checks existing email, BCrypt hashes input password, defaults missing role to EMPLOYEE, then saves. Login looks up the exact submitted email, BCrypt verifies, issues a token with email subject and role claim, and returns user ID/name/role. It does not check `active`, normalize email, throttle attempts or verify email. Admin signup manually validates the header prefix, parses JWT to get email, loads that user, checks current database role equals ADMIN, checks email uniqueness, hashes password and saves name/email/role. It ignores `UserDTO.profileImage`. Sources: `J/ServicePack/AuthService.java:30`, `:50`, `:77`.

**Observed:** Users: admin create hashes the supplied password and saves without a duplicate-email precheck or default role. User update replaces name, email, contactNumber, designation, joiningDate, active and role unconditionally. It updates profileImage only when non-null and password only when nonblank. Supplying a partial user JSON can clear fields; this is replacement behavior rather than safe PATCH behavior. Missing user reads/updates return null. Source: `J/ServicePack/UserService.java:21`, `:38`.

**Observed:** Tasks: create saves the input; persistence stamps createDate. Reads use `findAll`, ID lookup, or derived query `findByAssignedUserId`. DTO mapping flattens user identities and role-independent display names. Update replaces title, description, status, priority, dates and assignedUser; it preserves existing createdBy and createDate. No date-order validation, status-transition restrictions, automatic completion, assignee role checks or ownership checks are implemented. Source: `J/ServicePack/TaskService.java:19`, `:43`, `:51`, `:73`.

**Observed:** Task points: add loads parent task and attaches it server-side; update replaces title, completed and remark. The point can be updated by an employee regardless of parent ownership. Completing all points does not automatically update parent task status. TaskPoint JSON excludes task to prevent recursion. Source: `J/ServicePack/TaskPointService.java:26`, `:45`.

**Observed:** Attendance: mark defaults missing status to PRESENT then saves. GET mapping uses existing workingHours or computes `Duration.between(checkInTime,checkOutTime).toMinutes()/60.0` if workingHours is null. Thus an initial insert with times can show calculated hours in a DTO without persisting them; entity PreUpdate recalculates on updates. A client-provided workingHours can override the GET fallback. There is no duplicate-day check despite repository availability, no clock-in/out route and no check for a negative time interval. Source: `J/ServicePack/AttendanceService.java:23`, `:79`; `J/EntityPack/Attendance.java:44`.

**Observed:** Leaves: apply rejects startDate after endDate, forces PENDING and saves. DTO totalDays is inclusive calendar days: `DAYS.between(startDate,endDate)+1`; weekends and holidays count. Update checks order only when both dates are present, then replaces dates/type/reason. Approve and reject simply overwrite status with no transition precondition or approval audit. There is no quota deduction, overlap detection, holiday/calendar service, or pending-only decision restriction. Sources: `J/ServicePack/LeaveService.java:23`, `:56`, `:92`, `:104`, `:135`.

**Observed:** Dashboard report: controller invokes four repository `count()` calls and returns lifetime totals, not role-specific or date-filtered statistics. No charts, downloadable formats, background jobs or report calculation service are implemented server-side. Source: `J/ControllerPack/ReportController.java:32`.

**Observed:** The fundamentals demonstrated are layered request handling, dependency injection/inversion of control, declarative REST mapping, ORM relationship ownership, generated queries from repository method names, persistence lifecycle hooks, stream mapping to DTOs, enums for state vocabularies, password hashing and signature-based bearer authentication. Cross-operation service transaction boundaries are not declared (`@Transactional` absent in inspected services); repository methods still have Spring Data transaction behavior. Future multi-write operations need an explicit service transaction.

### Authentication, integration and security defects

**Observed:** Observed security setup: CORS allows exactly `http://localhost:5173`, methods GET/POST/PUT/DELETE/PATCH/OPTIONS, all request headers, credentials and exposed Authorization header (`J/ConfigPack/CorsConfig.java:20`). Controllers redundantly use the same origin. The filter chain enables CORS, disables CSRF, uses STATELESS sessions, and inserts JwtFilter before UsernamePasswordAuthenticationFilter (`J/ConfigPack/SecurityConfig.java:25`, `:220`). JWT HMAC SHA-256 uses UTF-8 secret bytes, email subject, role claim, issuedAt and one-hour expiry (`J/ConfigPack/JwtUtil.java:19`, `:28`). Secrets must provide enough entropy and at least 32 bytes for HS256; do not reuse the checked-in value.

**Observed:** JwtFilter skips OPTIONS and `/api/auth/**`; for other paths it accepts a Bearer header, parses/verifies token, builds authority `ROLE_` + claim role, and puts email string principal into SecurityContext. Invalid tokens return 401 with no JSON body. No header leaves the request for filter-chain authorization. It does not load a fresh database user, verify active status, or revoke tokens after user deletion or role changes. A demoted/deleted/disabled user's old token can retain its claimed role until expiry. Sources: `J/ConfigPack/JwtFilter.java:31`, `:39`, `:54`, `:66`.

| Classification | Finding | Code evidence and implication | Required reconstruction correction |
| --- | --- | --- | --- |
| Observed | Public role escalation | **Inference:** `AuthService.register` accepts any non-null User.role (`:40`); `/api/auth/register` is public. Caller can submit ADMIN. | **Recommendation:** Public register must force the least privileged role; admin assignment requires trusted authorization or a controlled seed. |
| Observed | Password hash leakage | **Inference:** User.password has no ignore/write-only annotation; `User.getPassword` is public (`User.java:27`, `:102`); user APIs return entities. Attendance POST can also serialize its nested user. | **Recommendation:** Return safe user DTOs; accept password only as request data. Never return password/hash. |
| Observed | Missing object-level authorization | **Inference:** Employee GET is allowed across all users/tasks/attendance/leaves; employee PUT accepts every task's full fields and any task point. Services never compare subject to resource owner. | **Recommendation:** Scope repository access to principal/owner; check ownership in services; employee updates should accept only allowed fields. |
| Observed | Disabled-account control absent | **Inference:** `User.active` exists but login does not inspect it and JwtFilter does not load the user. | **Recommendation:** Enforce account status at login and during protected access; design token revocation/short expiry. |
| Observed | Unusable leave owner input | **Inference:** `LeaveRequest.user` has `@JsonIgnore` (`:34`), which ignores association in both serialization and normal deserialization; POST accepts that entity directly; `user_id` is mandatory. No controller/service sets user. | **Recommendation:** Use ApplyLeaveRequest DTO with date/type/reason; derive user from principal and assign managed User. This is a strong static integration inference requiring runtime confirmation. |
| Observed | Weak validation/error handling | **Inference:** Validation starter exists, but no `@Valid`, constraints or exception mapper in inspected Java source. Most business failures throw RuntimeException. | **Recommendation:** Validate required strings, dates, enums and ownership; map expected failures to 400/401/403/404/409 with a stable JSON envelope. |
| Observed | Embedded secrets | **Inference:** application.properties includes a database password and JWT secret in source. | **Recommendation:** Read environment variables/secrets, rotate exposed values, use a limited DB user; do not copy source values. |
| Observed | Incomplete REST capabilities | **Inference:** No attendance PUT route, employee leave route, refresh/logout, or file upload API. | **Recommendation:** Implement required flows in both server and UI; document actual routes rather than assuming security permissions implement them. |
| Observed | Authorization differs for profiles | **Inference:** All user PUTs require ADMIN. Employee self-profile editing through `/api/users/{id}` is denied by chain. | **Recommendation:** Add explicit self-profile update with restricted fields and ownership checks. |
| Observed | Reports lack a role rule | **Inference:** `/api/reports/**` falls into authenticated fallback, so employees can access global totals. | **Recommendation:** Decide/report role policy and implement it in security and service. |
| Observed | Permitted docs do not exist | **Inference:** Swagger paths allowed, but no matching OpenAPI dependency. | **Recommendation:** Add springdoc only if API docs are actually desired; do not claim Swagger is present. |

**Observed:** If the caller UI runs at 5174 because Vite selects an available port, or uses `127.0.0.1` instead of localhost, the exact CORS origin does not match. Configure one explicit frontend origin and consistent ports/hostnames. Public static uploads may expose files placed in that directory; add a real upload design with allowed types, maximum sizes, generated filenames, and a deliberate access policy if required by a new idea.

### Launch requirements, evidence limits and safe reproduction

**Observed — prior-pass verification limit:** Current config: MySQL `jdbc:mysql://localhost:3306/Office_Management_System`, database username set in source, password redacted; server port 8080; `spring.jpa.hibernate.ddl-auto=update`; SQL logging and formatted SQL on. The schema/database must exist before normal startup because the JDBC URL does not include database creation. `src/main/resources/data.sql` is empty (0 bytes), so there is no provided admin/demo-data SQL bootstrap. No Maven wrapper exists in this office backend folder; Maven must be installed or supplied separately. A prebuilt `target/office-management-backend-0.0.1-SNAPSHOT.jar` exists, but its presence does not prove it matches current source or works in this environment. No backend tests or successful runtime execution were established in this inspection. Current copied-source results are recorded in REA_EVIDENCE_LEDGER.md; this statement concerns the original analysis pass.

**Observed:** For local reproduction, install/use Java 21, Maven and MySQL, create a dedicated development schema/user, then override sensitive config. Example PowerShell (replace placeholders, in a fresh development database):


**Recommendation — original example/source projection:**

```powershell
Set-Location 'E:\projectexcelr!\Office_Management_App-main\Office_Management_BackendApp'
$env:SPRING_DATASOURCE_URL = 'jdbc:mysql://localhost:3306/Office_Management_System'
$env:SPRING_DATASOURCE_USERNAME = '<development_database_user>'
$env:SPRING_DATASOURCE_PASSWORD = '<development_database_password>'
$env:JWT_SECRET = '<random_secret_at_least_32_bytes>'
mvn test
mvn spring-boot:run
```

**Observed:** These are launch instructions, not claims that the commands ran successfully. Use controlled admin initialization after correcting public-role escalation; do not design a new system around the vulnerability as its bootstrap. For production use migration scripts (Flyway/Liquibase), restricted DB credentials, `ddl-auto=validate`, HTTPS, disabled verbose SQL logs, safe response DTOs, and automated business/security tests. Those tools/policies are recommendations, not current dependencies.

**Recommendation:** To reproduce the useful pattern for a different idea, replace User roles and the domain entities but keep `controller -> transactional service -> repository -> relational database`, request/response DTOs, one shared frontend API contract, a consistent auth model and ownership policy. First complete one persisted flow (authenticate -> create a domain record -> list it -> update allowed fields -> reload to verify persistence), then add approval/status workflows and dashboard projections. Test at least unauthorized access, cross-user IDs, validation failures, uniqueness/date rules, and reload persistence; a visual frontend plus mocked data is insufficient.

## Office project: frontend implementation

**Observed — prior-pass verification limit:** Unless a path starts with another project root, frontend evidence in this section is relative to `Office_Management_App-main/officeManagementApp/`. These are source observations; this frontend was not executed because its dependencies are not installed. Current copied-source results are recorded in REA_EVIDENCE_LEDGER.md; this statement concerns the original analysis pass.

### Frontend location and duplicate tree

**Recommendation:** Use `officeManagementApp/` as the frontend and `Office_Management_BackendApp/src/main/java/` as the backend. The backend directory also contains a complete Vite frontend: all **43 files under the standalone frontend's `src/`** were compared with their counterparts there and had identical SHA-256 hashes at inspection. Both frontend lockfiles resolve the same major application libraries. Treat the second React tree as a duplicate, not a second service. Do not maintain both when reconstructing.

### Libraries and tooling

**Observed:** Manifest ranges and resolved versions are distinct. Versions below come from `package.json` and `package-lock.json`, not an installed dependency tree.

| Classification | Library | Declared range | Lockfile version | Actual role in inspected source |
| --- | --- | --- | --- | --- |
| Observed | React / React DOM | `^19.2.6` each | `19.2.7` each | JSX, functional components, hooks, browser root |
| Observed | React Router DOM | `^7.17.0` | `7.17.0` | BrowserRouter, Routes, Navigate, Link, location/navigation hooks |
| Observed | Redux Toolkit | `^2.12.0` | `2.12.0` | configureStore, createSlice, createAsyncThunk |
| Observed | React Redux | `^9.3.0` | `9.3.0` | Provider, useSelector, useDispatch |
| Observed | Axios | `^1.17.0` | `1.17.0` | REST client and request/response interceptors |
| Observed | Bootstrap | `^5.3.8` | `5.3.8` | Imported stylesheet, grids, buttons, tables |
| Observed | React Bootstrap | `^2.10.10` | `2.10.10` | Modal, Form, Button, Row, Col in editor popups |
| Observed | React Icons | `^5.6.0` | `5.6.0` | Heroicons/Feather/FontAwesome navigation and actions |
| Observed | React Toastify | `^11.1.0` | `11.1.0` | ToastContainer and request/login notifications |
| Observed | `@hello-pangea/dnd` | `^18.0.1` | `18.0.1` | Declared; no matching imports in inspected frontend |
| Observed | Chart.js / react-chartjs-2 | `^4.5.1` / `^5.3.1` | `4.5.1` / `5.3.1` | Declared; dashboards use cards/tables, no chart imports |
| Observed | Framer Motion | `^12.40.0` | `12.40.0` | Declared; no matching imports |
| Observed | Lodash | `^4.18.1` | `4.18.1` | Declared; search/sort use native arrays |
| Observed | React Calendar | `^6.0.1` | `6.0.1` | Declared; no matching imports |
| Observed | Vite | `^8.0.12` | `8.0.16` | Dev server, production bundler |
| Observed | Vite React plugin | `^6.0.1` | `6.0.2` | React transformation and development refresh |
| Observed | ESLint | `^10.3.0` | `10.4.1` | Flat configuration with JS, hooks, refresh rules |
| Observed | Nodemon | `^3.1.14` | `3.1.14` | Optional `dev:nodemon` script wrapping Vite |

**Observed:** Remaining development declarations: `@eslint/js ^10.0.1`, `@types/react ^19.2.14`, `@types/react-dom ^19.2.3`, `eslint-plugin-react-hooks ^7.1.1`, `eslint-plugin-react-refresh ^0.5.2`, `globals ^17.6.0`. Type packages do not make this a TypeScript project; source is `.js`/`.jsx`.

**Observed:** Scripts: `npm run dev` and `npm start` launch Vite; `npm run build` builds `dist/`; `npm run preview` previews it; `npm run lint` runs ESLint. `vite.config.js` only registers the React plugin: no API proxy or fixed port. Keep the frontend on port 5173 when using current backend CORS. Exact Node engine compatibility must be checked against the selected Vite/plugin versions before installation.

### Component hierarchy and state ownership


**Inference — original example/source projection:**

```text
index.html (#root)
  src/main.jsx
    StrictMode
      Redux Provider (store)
        BrowserRouter
          OfficeManagementApplication
            ToastContainer (top-right, 3 seconds)
            AppRoutes
              public authentication pages
              ProtectedRoute -> RoleRoute -> admin/employee page
                Sidebar + main-content/Navbar/page-content/Footer
```

**Observed:** `src/Redux/store.js:11` registers five slices: `auth`, `employees`, `tasks`, `attendance`, `leaves`. Redux holds fetched/shared data; `useState` holds forms, selected rows, sorting, searches, expanded sections, and modal visibility. `useMemo` derives filtered/sorted arrays. Default serializability checking is disabled in the store; this is unnecessary for ordinary JSON and should be restored in a new implementation.

**Observed:** Authentication state starts empty even after refresh. Route guards read localStorage directly, so an old token can grant UI access while Redux has `user: null`. Prefer one explicit session bootstrap and one source of auth truth.

### Frontend route map and completeness

| Classification | URL | Component | Observed functionality |
| --- | --- | --- | --- |
| Observed | `/`, `/signup` | SignupPage | Required name/email/password; EMPLOYEE or ADMIN selection; dispatch register, navigate to login |
| Observed | `/login` | LoginPage | Email/password; dispatch login; route according to returned role |
| Observed | `/admin/admin-dashboard` | AdminDashboard | Fetch users/tasks/leaves, cards, selectable/searchable/sortable tables; has a startup runtime defect described below |
| Observed | `/admin/employees-list` | Employees | EMPLOYEE-only list, add/edit/delete modals, search/sort/row selection |
| Observed | `/admin/tasks` | Tasks | Fetch users/tasks/enums, create task with checklist, search/sort/list; edit/delete buttons reference missing handlers |
| Observed | `/admin/attendance` | Attendance | Fetched attendance table; search/sort; edit/delete buttons have no handlers |
| Observed | `/admin/leaves` | Leaves | List/apply/approve/reject; search/selection; some action affordances unfinished |
| Observed | `/admin/profile` | AdminProfile | Find current user in all-user list, display profile, local image preview |
| Observed | `/employee/employee-dashboard` | EmployeeDashboard | Static example counts 50/120/85/15; no dashboard API calls |
| Observed | `/employee/employee-profile` | EmployeeProfile | Layout and heading only |
| Observed | `/employee/mytasks` | MyTasks | Heading only |
| Observed | `/employee/myattendance` | MyAttendance | Heading only |
| Observed | `/employee/myleaves` | MyLeaves | Heading only |
| Observed | `*` | Inline fallback | 404 text |

**Observed:** Source: `src/Routes/AppRoutes.jsx`, `src/Pages/Employee/*`. Both Sidebar and Navbar send employees to `/employee/profile`, which is absent from the router; actual route is `/employee/employee-profile` (`src/Components/Layouts/Navbar.jsx:34`, `Sidebar.jsx:67`). `EditTaskPopup.jsx` returns an empty fragment. Notifications show a “Coming Soon” alert rather than fetching notifications.

### Authentication and Axios integration

**Observed:** `src/Api/AxiosConfig.js:7` sets `baseURL = http://localhost:8080/api`. A request interceptor reads localStorage `token` and sets `Authorization: Bearer <token>`. This frontend does not use the college app's cookie/CSRF scheme.

1. **Observed:** Signup sends `{name,email,password,role}` to `POST /api/auth/register`. The selection of ADMIN is accepted by the backend and is a security defect, not a safe reusable registration pattern.
2. **Observed:** Login sends `{email,password}` to `POST /api/auth/login`. The fulfilled reducer saves `token`, `role`, `userId` and serialized login response under `user` in localStorage; login page navigates to the role dashboard.
3. **Observed:** Logout removes stored identity/token and clears Redux auth; it makes no backend revocation request.
4. **Observed:** ProtectedRoute checks only token presence. RoleRoute compares its `role` prop against localStorage role, but AppRoutes passes the **current user's own role** to every route. Consequently both role trees pass the same comparison. A new implementation must use `allowedRoles={["ADMIN"]}` for admin routes and verify all permissions server-side.
5. **Observed:** On 401 **or 403**, the response interceptor removes token/role/userId and shows “Session expired.” It does not clear Redux or stored `user`, and it treats an authorization denial as an expired login. It dereferences `error.response.status` without guarding network errors. Use optional chaining, handle 401 and 403 separately, and sync auth state.

**Observed:** Sources: `authSlice.js:31`, `authSlice.js:107`, `ProtectedRoute.jsx:5`, `RoleRoute.jsx:7`, `AppRoutes.jsx:38`, `AxiosConfig.js:31` (all under `src/Redux`, `src/Components/Common`, or `src/Routes` as applicable).

### Frontend API adapter inventory

**Observed:** Every path below is appended to `http://localhost:8080/api`; the backend section documents which handlers actually exist and their authorization.

| Classification | Slice/action | Request | Payload/result handling |
| --- | --- | --- | --- |
| Observed | signupUser / loginUser | POST `/auth/register`, POST `/auth/login` | Form JSON; rejectWithValue preserves server body where available |
| Observed | fetchEmployees | GET `/users` | Replaces employees.list with response.data |
| Observed | addEmployee | POST `/users` | Full employee form; pushes returned User |
| Observed | updateEmployee | PUT `/users/{id}` | Submitted employee JSON; replaces matching id |
| Observed | deleteEmployee | DELETE `/users/{id}` | Removes id after success |
| Observed | uploadProfileImage | POST `/users/{id}/upload-image` | FormData `file`; reducer expects plain returned image path; **no matching backend endpoint** |
| Observed | updateProfileImage | PUT `/users/{id}/profile-image` | `{profileImage}`; **no matching backend controller endpoint** |
| Observed | fetchTaskStatuses / fetchTaskPriorities | GET `/tasks/statuses`, GET `/tasks/priorities` | Saves enum arrays for forms |
| Observed | fetchTasks | GET `/tasks` | Replaces tasks.list |
| Observed | createTask / updateTask / deleteTask | POST `/tasks`, PUT `/tasks/{id}`, DELETE `/tasks/{id}` | Create pushes, update replaces, delete removes |
| Observed | fetchTaskPoints | GET `/task-points/task/{taskId}` | Sets matching task.taskPoints |
| Observed | addTaskPoint | POST `/task-points/task/{taskId}` | Checklist JSON; pushes returned point under task |
| Observed | updateTaskPoint | PUT `/task-points/{pointId}` | Scans every task.taskPoints and replaces matching point |
| Observed | deleteTaskPoint | DELETE `/task-points/{pointId}` | Removes point from supplied task id |
| Observed | fetchAttendance | GET `/attendance` | Replaces attendance.list |
| Observed | markAttendance | POST `/attendance` | Thunk exists; no fulfilled reducer/list update or UI control |
| Observed | fetchLeaves / fetchLeaveById | GET `/leaves`, GET `/leaves/{id}` | Replaces list / selectedLeave |
| Observed | createLeave / updateLeave / deleteLeave | POST `/leaves`, PUT `/leaves/{id}`, DELETE `/leaves/{id}` | Push / replace / remove |
| Observed | approveLeave / rejectLeave | PUT `/leaves/{id}/approve`, PUT `/leaves/{id}/reject` | Changes local matching leave.status from returned entity |

**Observed:** Sources: all five files in `src/Redux/`. Most mutations have only fulfilled handlers; a reconstruction needs pending/rejected handling for every submit action.

### Business behavior traced from UI to persistence

**Observed:** **Employee editor.** Form fields are `name,email,contactNumber,password,designation,joiningDate,role,active`. Edit initializes from the selected User in `useEffect`; blank password is omitted so it can preserve the existing hash. Employees page dispatches add/update and closes immediately, without awaiting `.unwrap()`. Consequently errors can occur after the form disappears. Redux Toolkit thunks resolve to action objects on failure: ordinary try/catch does not catch a rejected thunk unless `.unwrap()` is used. Sources: `AddEmployeePopup.jsx:11`, `EditEmployeePopup.jsx:21`, `Employees.jsx:91`.

**Inference:** **Task creation.** CreateTaskPopup controls `title,description,priority,status,startDate,endDate,assignedUserId,taskPoints`. Blank checklist titles are removed; each nonblank item becomes `{pointTitle,completed:false,remark:""}`. Tasks page adds nested `assignedUser:{id}` and `createdBy:{id}` from localStorage, POSTs the parent, then POSTs each point sequentially, then refetches all tasks. The initial parent JSON also contains taskPoints. Backend TaskService directly saves that graph without setting each point's owning `task` association; cascade is enabled on the inverse collection. **Inference:** initial points can be persisted without a parent link, then the later point requests create new attached rows. There is no intentional atomic parent-and-children creation. TaskDTO also omits taskPoints, so refetching all tasks discards any checklist loaded into Redux unless a separate point fetch is used. For a new project, submit parent and children once in a transaction, set both relationship sides, and derive createdBy from the authenticated principal. Sources: `CreateTaskPopup.jsx:21,124`, `Tasks.jsx:173`, backend `ServicePack/TaskService.java:19`, `EntityPack/Task.java`, `EntityPack/TaskPoint.java`.

**Observed:** **Leave application.** Form requires a type (CASUAL/SICK/ANNUAL/EMERGENCY), dates with end >= start, and a nonblank reason. Inclusive day count is `ceil((end-start)/86400000)+1`, clamped to zero for invalid order. Submit includes `user:{id:Number(localStorage.userId)}`. Backend binds LeaveRequest directly while its user association is `@JsonIgnore`; this prevents the supplied user from being bound and conflicts with required user_id. GET returns LeaveDTO with employeeName and totalDays, while mutations return LeaveRequest without those display fields. The immediate refetch generally restores DTO fields, but temporary reducer entries have a different shape. Use a CreateLeaveRequest DTO and one consistent LeaveResponse DTO. Source: `ApplyLeaves.jsx:17,35,76,117`, `Leaves.jsx:189`; backend `EntityPack/LeaveRequest.java:34` and `DTOPack/LeaveDTO.java`.

**Observed:** **Attendance.** UI expects nested `user.name`, `attendanceDate`, `status`, `checkInTime`, `checkOutTime`, `workingHours`. GET actually returns AttendanceDTO with **flat employeeName/userId**; the rendered employee name and user sorting key are therefore absent. Use item.employeeName and sort by that field, or deliberately change both server and client to the same DTO. General Object.values(...).join(" ") search also fails to meaningfully flatten nested values. Source: `Attendance.jsx:73,231`; backend `DTOPack/AttendanceDTO.java`.

**Observed:** **Dashboard.** Counts are derived in the browser, not fetched from ReportController: employees with non-null role, total tasks, COMPLETED tasks, PENDING leaves, and tasks assigned to the current id. `ownTasks` is mistakenly assigned `.length`, then `filteredOwnTasks` spreads it as an array (`AdminDashboard.jsx:75,205`). A number is not iterable; this memo is evaluated on initial render, so it can crash the whole dashboard. Keep `ownTasks = tasks.filter(...)` and use `ownTasks.length` only for the count. Several edit/delete buttons also reference missing handlers. Source: `AdminDashboard.jsx:535,656,773` and `Tasks.jsx:336`.

**Observed:** **Profile images.** AdminProfile reads all users, selects the current id, displays `http://localhost:8080` plus stored image path or calls ui-avatars.com with the user's name. File selection creates a local object URL; upload dispatch is commented out. Persist by wiring the existing upload thunk and revoke object URLs on cleanup. Avoid sending personal names to a third party when implementing private deployments. Source: `AdminProfile.jsx:28,45,65`.

### Styling and frontend fundamentals

**Observed:** This is a client-rendered single-page application, not SSR. Bootstrap is combined with handwritten CSS in `src/assets/AllPagesCss/`: login/signup split panels, persistent sidebar/navbar/footer, profile cards, dashboard grids, global table/action/badge styles, and Toastify overrides. Breakpoints include 1200, 992, 768, 576 and 480px. Google Fonts supplies Poppins; Unsplash supplies remote authentication-page backgrounds; ui-avatars.com supplies fallback avatars. These are external resource requests, not backend modules. No Tailwind/component design-token system is used by the active office entry.

**Observed:** Fundamentals actually used: declarative rendering; component composition; controlled forms; effect-driven fetching; Redux async lifecycle; immutable array updates (with Immer inside slices); derived state/memoization; browser routing; bearer HTTP headers; multipart uploads; client-side validation; native filter/search/sort; responsive CSS. Checklist form copies the array but mutates an existing nested point object; clone the changed point as well in new code. No WebSocket/realtime, offline cache, SSR, automated frontend test suite, functional chart, drag-and-drop, or calendar implementation was found in this inspected frontend.

### Frontend defects and reconstruction requirements

| Classification | Finding | Evidence | Required behavior in a new working app |
| --- | --- | --- | --- |
| Observed | Dashboard spreads a number | AdminDashboard.jsx:75,205 | **Recommendation:** Separate task list from task count |
| Observed | Role guard accepts user's current role on every route | AppRoutes.jsx, RoleRoute.jsx | **Recommendation:** Explicit allowed roles per route; server authorization |
| Observed | Case-mismatched imports | main.jsx:20; OfficeManagementApplication.jsx:3; Redux slice imports; AppRoutes.jsx:20,22; Employees.jsx:23 | **Recommendation:** Match actual `Redux`, `Routes`, `Api/AxiosConfig`, `Components/Common` spelling |
| Observed | Employee profile links lead to 404 | Navbar.jsx:34; Sidebar.jsx:67 | **Recommendation:** Align router, menu and title keys |
| Observed | Unimplemented employee pages | Pages/Employee/* | **Recommendation:** Implement API-backed own-data screens |
| Observed | Unwired actions / empty edit modal | Admin attendance/tasks; EditTaskPopup.jsx | **Recommendation:** Every visible enabled button must perform its advertised operation |
| Observed | Leave payload/response mismatch | ApplyLeaves.jsx; Leaves.jsx; backend LeaveRequest | **Recommendation:** DTO contracts and authenticated ownership |
| Observed | Both image thunks have no backend endpoint | employeeSlice.js; backend UserController.java | **Recommendation:** Implement endpoints or remove unused thunks |
| Observed | Attendance user display expects nested user; GET returns flat DTO | Attendance.jsx; AttendanceDTO.java | **Recommendation:** Render and sort employeeName |
| Observed | Network error interceptor throws | AxiosConfig.js:35 | **Recommendation:** Guard absent response, retain original error |
| Observed | Redux point reducers assume task/taskPoints exist | taskSlice.js update/delete fulfilled cases | **Recommendation:** Check entities/arrays before lookup/update |
| Observed | Forms close despite rejection | editor/task/leave callbacks | **Recommendation:** Await successful `.unwrap()` before reset/close |
| Observed | Public ADMIN signup and token in browser storage | SignupPage.jsx; authSlice.js | **Recommendation:** Restrict role assignment; consciously choose token storage/auth strategy |

**Observed:** Static verification inspected **76 active relative import declarations**: no missing imports on the Windows filesystem, but **12 case mismatches** that affect case-sensitive hosts. Commented-out employee/task stylesheet imports were excluded. No office production build was claimed.

## Applied copy and current verification

# Office copy changes

**Observed — scope:** Changes were applied only to `revised-projects/office/backend` and `revised-projects/office/frontend`; the original `Office_Management_App-main` source remains the baseline for the historical analysis. The copied backend keeps Java/resources and removes the duplicated React tree. The 17 removed relative paths are recorded in `office-removed-duplicate-paths.json`.

**Observed — frontend verification:** `npm.cmd run build`, executed from `E:\projectexcelr!\revised-projects\office\frontend`, exited 0. Vite 8.0.16 transformed 439 modules and generated `dist/index.html`, `index-DvD-14F6.css` (259.13 kB) and `index-DRgvMZyF.js` (436.74 kB). This verifies bundling; it does not establish browser interaction success. The parent performed the dependency installation separately.

**Observed — imports:** A case-aware scan checked 84 active relative imports in the revised frontend and found zero missing/case-mismatched imports. Twelve original import declarations were corrected. `office-import-case-fixes.txt` has eleven replacement-prefix entries because the common component prefix fixes two declarations in AppRoutes. `office-import-validation.txt` records the revised scan result.

**Observed — source changes addressing point 6:**

| Classification | Copied source | Change observed in revised code |
| --- | --- | --- |
| Observed | Backend root / `src/` | Duplicated React folders, root package/lock/Vite/ESLint/index files and template README removed; preserved Java/resources/POM |
| Observed | `DTOPack/ApiDtos.java` | Explicit request/response records; Bean Validation constraints; minimal safe user DTO; consistent task/checklist/leave shapes |
| Observed | `ConfigPack/ApiExceptionHandler.java` | Invalid request/validation -> 400; missing -> 404; duplicate/dependent data -> 409; denied ownership -> 403 |
| Observed | `ConfigPack/CurrentUser.java` | Server-derived current account, ACTIVE check, administrator and object-owner guards |
| Observed | `ConfigPack/JwtFilter.java` | Verify signature/expiry and reload database account/role/status on protected requests; deleted/disabled accounts lose access |
| Observed | `ConfigPack/SecurityConfig.java` | Explicit public register/login/health only; admin signup protected; stable authentication/role errors; all core deletes admin-only |
| Observed | `ConfigPack/AdminInitializer.java` | Environment-configured admin bootstrap; no default password; no public administrator registration |
| Observed | `ServicePack/OfficeService.java` | Transactional safe DTO CRUD; principal-derived creator/leave owner; one parent/checklist save setting both JPA sides; scoped employee list/read/update; inactive assignee/date checks |
| Observed | `ControllerPack/*Controller.java` | All original business endpoints route through revised DTO/service layer, `@Valid`, consistent statuses; added `/api/health` and `/api/auth/me` |
| Observed | `EntityPack/User.java` | Password `@JsonIgnore` as defense in depth; public controllers never return User entities |
| Observed | `EntityPack/Task.java`, `TaskPoint.java` | Initialized checklist collection and mandatory owning task FK |
| Observed | `EntityPack/Attendance.java` | Database composite uniqueness for employee/date |
| Observed | `ServicePack/AuthService.java` | Legacy registration also forces EMPLOYEE; inactive-account rejection added; revised controllers use OfficeService |
| Observed | `application.properties` | DB/JWT/bootstrap secrets are environment values; SQL logging disabled and open-in-view disabled |
| Observed | Frontend entry/router/slices | Import casing matches actual paths; removed unused icon import; explicit ADMIN/EMPLOYEE route requirements |
| Observed | `Pages/Authentication/*` | Public ADMIN selector removed; password limits; await rejected thunks with unwrap; login errors displayed |
| Observed | `Api/AxiosConfig.js` | Configurable URL/timeout; safe no-response handling; distinguish 401/403; clear stored account on 401 |
| Observed | `Redux/authSlice.js`, `OfficeManagementApplication.jsx` | Account bootstrap through real `/auth/me`; session-expired event clears Redux and storage; token-bearing console logs removed |
| Observed | `Pages/Admin/AdminDashboard.jsx` | Real fetched lists/counts, separate own-task array/count, searchable sortable tables; removed undefined dashboard action handlers |
| Observed | `Pages/Admin/Tasks.jsx` | One parent/checklist create, edit/delete with real endpoints, persisted checklist toggles, wait for success before closing/resetting |
| Observed | `Redux/taskSlice.js` | Guard absent tasks/checklist arrays in point reducers |
| Observed | `Pages/Admin/Attendance.jsx` | Render/sort flat employeeName; unimplemented edit action explicitly disabled instead of presenting an enabled dead action |
| Observed | Sidebar/Navbar | Employee profile links now match `/employee/employee-profile` |
| Observed | Employee pages | API-backed own task/status/checklist, own attendance, own leave application/list, current profile and scoped dashboard counts replace placeholders/static counts |
| Observed | Employee editor and leave popups | Await successful writes; retain form and show error on rejection |

**Observed — revised API contracts:** Public registration takes `{name,email,password}` and ignores unknown client `role`; response status is 201 with safe UserResponse and role EMPLOYEE. Login remains JSON `{email,password}` and responds with `{token,userId,name,role}`. GET `/api/auth/me` returns safe current-account fields. POST `/api/tasks` takes `{title,description,status,priority,startDate,endDate,assignedUserId,taskPoints:[{pointTitle,completed,remark}]}` and derives createdBy. It returns 201 with taskPoints including their persisted IDs. PUT task uses the same DTO; employees may change only their own task status. Checklist title/creation/deletion administration is restricted; an assignee may mark their own existing points.

**Observed — leave contract:** POST `/api/leaves` takes `{leaveType,startDate,endDate,reason}`; nested input `user` is unnecessary and ignored. Owner is the current database user. Responses consistently contain `{id,userId,employeeName,leaveType,startDate,endDate,totalDays,reason,status}`. Approve/reject require ADMIN and PENDING; repeat decisions return 409. Employee GET leaves/tasks/attendance returns only that user's records. Administrator list endpoints still return all records permitted by that role.

**Observed — configuration:** Runtime accepts `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`, `SERVER_PORT`, required `JWT_SECRET`, optional `OFFICE_BOOTSTRAP_ADMIN_EMAIL` and `OFFICE_BOOTSTRAP_ADMIN_PASSWORD`. Bootstrap runs only for a missing configured admin email. JWT secret must satisfy the unchanged JJWT HS256 entropy/length requirement. The frontend accepts public `VITE_API_BASE_URL`.

**Observed — tests addressing points 1 and 6:** `OfficeSecurityIntegrationTests.java` defines six meaningful integration tests: context load; ignored ADMIN signup and safe response; login/role denial; one linked checklist save plus cross-user denial; 400/404/409 mapping; and disabled-account JWT denial. They require an actual MySQL `DB_URL` ending in isolated schema `rea_office_test` and `DB_USERNAME`/`DB_PASSWORD`; the test refuses other schema names before using create-drop. H2 is not used.

**Unverified — pending parent execution:** Backend compilation/MySQL test results and process-restart API persistence are recorded separately by the parent in the evidence ledger. This source-change note makes no claim that those backend checks passed before the parent executes them.

**Unverified — remaining scope:** Browser interaction of revised screens; external OAuth/media integrations; a complete attendance editor/creation UI; persistent profile-image upload; refresh-token/server logout/revocation; and strict state-transition/version/audit/leave-quota policies remain outside the executed office frontend build. Attendance editing has no backend PUT endpoint. The media addon/starter is a separate implementation, not an office endpoint.

**Recommendation:** Use the revised copy or generated patch, not the historical original, to adopt these corrections; keep the original findings as evidence of the supplied code. Browser/backend/API verification must be distinguished from this source and frontend-build evidence.

**Observed:** Exact commands, test counts and restart checks are in [REA_EVIDENCE_LEDGER.md](REA_EVIDENCE_LEDGER.md). Copy paths are under `revised-projects/`; original findings are retained.

## Resolved original Maven dependency versions

**Observed:** The original POM dependency graph resolved successfully without compiling the original college Java25 target. These versions describe that original POM, not the migrated copy. The exact command and complete tree are in the ledger.

| Classification | Artifact | Resolved version |
| --- | --- | --- |
| Observed | `org.springframework:spring-core` | `6.2.7` |
| Observed | `org.springframework.security:spring-security-core` | `6.5.0` |
| Observed | `org.hibernate.orm:hibernate-core` | `6.6.15.Final` |
| Observed | `org.apache.tomcat.embed:tomcat-embed-core` | `10.1.41` |
| Observed | `com.fasterxml.jackson.core:jackson-databind` | `2.19.0` |
| Observed | `com.fasterxml.jackson.core:jackson-annotations` | `2.19.0` |
| Observed | `com.mysql:mysql-connector-j` | `9.2.0` |
