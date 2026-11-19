# REA full-stack blueprint

## One-page quick start

**Recommendation:** Start here; read a project analysis only for the feature you need. Read the evidence ledger for actual test results. Pin new Java code to **Java 21 + Spring Boot 3.5.0**, an explicit 3.5.x release shared with the office reference.

1. **Recommendation:** Define the idea, actors, ownership, entities, invariants and one acceptance scenario.
2. **Recommendation:** Use `starter/` as concrete code; adapt its nouns and business rules.
3. **Recommendation:** Choose session+CSRF for the browser starter; keep one coherent authentication model.
4. **Recommendation:** Create an isolated MySQL schema. Copy `.env.example` to `.env` and supply private values.
5. **Recommendation:** Build backend/tests and frontend/tests; then start the real pair.
6. **Recommendation:** Exercise register/login/role denial/create/restart/persistence before reporting success.
7. **Recommendation:** For music/media, also read `REA_MEDIA_AND_ML_ADDON.md` and its limits.

**Recommendation — Docker instructions (execution status in ledger):**

```powershell
Set-Location starter
Copy-Item .env.example .env
# Edit .env with database and bootstrap credentials.
docker compose up --build -d
docker compose --profile ml up --build -d
```

**Recommendation — local commands; MySQL/environment required:**

```powershell
Set-Location starter/backend
mvn test
mvn spring-boot:run
# Separate terminal:
Set-Location starter/frontend
npm install
npm test
npm run build
npm run dev -- --port 5173 --strictPort
```

**Observed:** Workspace verification uses `verification/run_command.py` and `tools/maven.py` to pin Java 21, isolate credentials, record logs, and handle Windows `!` paths. Exact results and commands are in the ledger; ordinary projects can use Maven directly.

**Observed:** Starter persistence uses Spring JDBC and transactions with Flyway. Both source applications use JPA/Hibernate. JDBC is a deliberate implementation choice, not a finding about those applications.

## Architecture summary

| Classification | Layer | Office original | College original | Starter |
| --- | --- | --- | --- | --- |
| Observed | UI | React/Vite/Redux | React/Vite/AuthContext | React/Vite/AuthContext |
| Observed | API client | Axios/Bearer JWT | Axios/session/CSRF | Axios/session/CSRF |
| Observed | Styling | Bootstrap, React Bootstrap, custom CSS | Bootstrap/custom CSS | Custom CSS |
| Observed | Java target | 21 | 25 | 21 |
| Observed | Boot target | 3.5.0 | 4.1.2 | 3.5.0 |
| Observed | Data | JPA/MySQL | JPA/MySQL | JDBC/MySQL/Flyway |
| Observed | Roles | ADMIN/EMPLOYEE | ADMIN/STUDENT/FACULTY | ADMIN/MEMBER |
| Observed | Main patterns | Tasks/checklists/approvals | Catalog/assignment/enrollment | Work items/checklists/media |

**Observed:** Original backends are layered monoliths, with independent databases and no inter-project calls. Their original defaults share backend 8080/frontend 5173. Revised test pairs use isolated ports/schemas.

**Recommendation:** Preserve `UI -> shared API client -> security -> validated controller -> transactional service -> repository/database -> response DTO -> UI`. Make every advertised action traverse the entire chain.

## Idea-to-domain method

**Recommendation:** Write a brief containing purpose, actors, record types, permitted actions, ownership, status transitions, dates, integration requirements and test scenarios. Use supplied requirements; state ordinary assumptions and proceed.

| Classification | Reusable pattern | Domain meaning | Adaptations |
| --- | --- | --- | --- |
| Recommendation | User + role + optional profile | Identity separate from domain data | Member/manager, patient/doctor |
| Recommendation | Course/resource | Discoverable catalog record | Room, service, workshop, track |
| Recommendation | Enrollment/assignment row | Relationship with attributes | Booking, membership, stewardship |
| Recommendation | Task + checklist | Parent with dependent children | Onboarding, fulfillment, service job |
| Recommendation | Attendance/activity | Dated event and eligibility rules | Check-in, listening/activity log |
| Recommendation | Leave/request | Authorized state decision | Expense, access, change request |
| Recommendation | Dashboard | Scoped aggregate | Own work; admin totals |

**Recommendation:** Adapt invariants to the idea. Bookings need capacity/overlap rules; commerce needs decimal money and verified payment events; media needs validated storage and seeking; ML needs a model contract and failure behavior.

**Recommendation:** Build one feature vertically first: authenticate -> create record -> list -> permitted update -> reload -> restart -> confirm persistence. Expand modules after this succeeds.

## Database and transaction rules

**Recommendation:** Define required fields, enum vocabularies, foreign keys, indexes, uniqueness, deletion behavior, audit timestamps and concurrency policy before coding screens.

**Observed:** `starter/backend/src/main/resources/db/migration/V1__init.sql` contains users, resources, memberships, work_items, checklist_points, requests, activity and media_files.

**Recommendation:** Use relationship rows when a relation has dates/status. Keep server-derived creator/owner IDs. Use unique constraints as final concurrent duplicate protection and map violations to 409.

**Recommendation:** In JPA, set the child foreign-key side as well as the parent's collection; cascade alone does not connect an unset child. In JDBC, insert parent and children within one transaction using the generated parent ID.

**Recommendation:** Use versions or locked/conditional updates for competing status decisions. Reject invalid transitions instead of overwriting them silently.

**Recommendation:** Use LocalDate for business dates and UTC timestamps for events; define the business timezone/holiday policy. Compute authoritative totals on the backend.

**Recommendation:** Use migrations for new schemas. Existing source copies preserve Hibernate-managed schema for targeted verification; do not run a new Flyway V1 blindly against an existing database.

## Authentication patterns

| Classification | Requirement | Session + CSRF | Bearer JWT |
| --- | --- | --- | --- |
| Recommendation | Browser credential | HttpOnly session cookie | Explicit storage decision |
| Recommendation | Client | withCredentials and agreed CSRF header | Authorization: Bearer |
| Recommendation | Writes | CSRF protection, including login/register | Assess actual credential transport |
| Recommendation | Logout | Invalidate server session/context | Deliberate refresh/revocation strategy |
| Recommendation | Changed roles/status | Fresh status checks and invalidation | Short expiry/token version/fresh user check |

**Recommendation:** Public registration always forces the least privileged role. Bootstrap admin privately. BCrypt-hash passwords, normalize email once, never serialize password hashes, and enforce active-account status.

**Recommendation:** Prefer the standard authentication filter for session login. A custom JSON controller must invoke session authentication strategy and save the context through its repository.

**Observed:** Starter login uses URL-encoded email/password through Spring's form filter. Revised college retains JSON login with its session safeguards. These are different request contracts.

**Recommendation:** Fetch CSRF before unsafe calls and refresh after authentication/logout. Separate 401 identity expiry, 403 access denial, and connection failures. Avoid automatic retries of non-idempotent writes.

**Recommendation:** UI guards improve navigation; backend roles and object ownership decide access. Fetching all records then filtering in React does not secure another user's records.

**Recommendation:** OAuth requires verified provider identity, approved app account, database role authorities, a consistent CurrentUser resolver and denial/activation/link policies. Test the provider flow separately.

## API contract rules

**Recommendation:** For every endpoint specify method/path, roles, object scope, request DTO, response DTO/status, validation and failure behavior. Update Java and JSX field names together.

| Classification | Endpoint pattern | Contract rule |
| --- | --- | --- |
| Recommendation | POST register | Force role; validate; 201 safe response |
| Recommendation | POST login / GET me / POST logout | Coherent credential format and lifecycle |
| Recommendation | GET collection/detail | Server ownership scope; explicit projection/pagination |
| Recommendation | POST core record | 201; atomic children; principal-derived creator |
| Recommendation | PATCH status | Allowed transition; ownership; concurrency conflict |
| Recommendation | GET dashboard | Named counts scoped by role |
| Recommendation | POST upload / GET stream | Size/type/path policy; Range behavior; ownership |

**Recommendation:** Return one stable DTO shape for reads and mutations. Do not expose persistence graphs or rely on accidental getter/lazy-loading behavior.

**Recommendation:** Use `@Valid @RequestBody` with `@NotBlank`, `@Email`, `@Size`, `@NotNull`, `@Positive` and nested `@Valid`. A declared validation dependency does not validate a request by itself.

**Recommendation:** Global exceptions return `{code,message,fieldErrors}`: 400 invalid input, 401 unauthenticated, 403 denied, 404 missing, 409 duplicate/version/transition conflict, generic 500 for unexpected faults.

**Observed:** Concrete examples are in starter's AuthController, WorkController, ApiExceptionHandler and tests; copied office DTO/controllers also demonstrate validation.

## Frontend rules

**Recommendation:** Keep auth in one provider; wait for restoration before route decisions. Give every list/form independent loading, error, empty, success and submitting states.

**Recommendation:** Use labeled controlled inputs; disable duplicate submits; await successful writes before closing; reconcile real response data; cancel obsolete fetches.

**Recommendation:** With Redux Toolkit, use `.unwrap()` when surrounding try/catch must catch a rejected thunk. Guard missing entities/arrays in reducers.

**Recommendation:** Keep paths/roles consistent between router, sidebar and profile links. Match import case exactly for Linux/container builds.

**Recommendation:** Native audio uses a same-origin authenticated streaming URL. A browser audio element cannot attach the office Axios Bearer interceptor automatically.

## Acceptance checklist

| Classification | Verify against the real pair | Required evidence |
| --- | --- | --- |
| Recommendation | Backend/frontend compile and tests | Exact commands and exit codes |
| Recommendation | MySQL startup/migrations | Intended schema/version and migration result |
| Recommendation | Register/login/me/logout | Credential/session behavior and denial after logout |
| Recommendation | Missing/wrong role and another owner's ID | 401/403 or deliberate 404 without data/write leakage |
| Recommendation | Primary record and children | Persisted linked rows; no ownerless/duplicate rows |
| Recommendation | Invalid and duplicate writes | Stable 400/409 response; form remains usable |
| Recommendation | State/date/concurrency rules | Server invariant enforced |
| Recommendation | Restart persistence | Same record after process restart |
| Recommendation | Navigation and browser seeking | Actual browser behavior, beyond build/unit tests |
| Recommendation | ML success/down/timeout | Real service response and documented fallback |
| Recommendation | Docker deployment | Executed build/up if daemon available |

**Recommendation:** Use isolated databases, meaningful security/transaction tests and browser smoke checks. Mark unexecuted behavior Unverified with a specific reason. A bundle build or mocked test is not evidence of end-to-end operation.

## Ready-to-use agent prompt

**Recommendation — copy and adapt:**

```text
Read REA_BLUEPRINT.md first, then REA_EVIDENCE_LEDGER.md. Consult the office
or college analysis only for relevant detailed evidence. For media/music,
read REA_MEDIA_AND_ML_ADDON.md and inspect starter/.

Build a working frontend and backend for: <IDEA AND REQUIREMENTS>.
Pin Java 21 + Spring Boot 3.5.0 and compatible React/Vite dependencies unless
my requirements specify another stack. Define actors, schema, ownership,
DTO/API contracts, invariants and acceptance flows first. Use one auth model.
Implement real UI -> secured API -> transactional service -> MySQL flows.
Correct source defects; preserve useful patterns and adapt domain rules.

Deliver code, migrations/setup, env examples, admin provisioning, README,
and exact executed checks. Verify role denial, core writes and persistence
after restart. Label claims Observed, Inference, Recommendation or Unverified.
Never equate placeholders, mocks or a frontend build with a working app.
```
