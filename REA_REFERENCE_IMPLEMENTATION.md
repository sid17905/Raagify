# Retained reference implementation recommendations

**Recommendation:** These are the original longer examples, retained so the 188-line blueprint can stay compact. Use concrete starter source and current ledger results instead of assuming these illustrative snippets were compiled. New projects are pinned to Java 21 and Boot 3.5.0.

## Reusable blueprint: build a working project from an idea

**Recommendation:** Everything in this section is a **recommended reconstruction design**. It is self-contained guidance for a coding agent, not a claim that these additions exist in either repository.

### 1. Convert the idea into a concrete domain

**Recommendation:** Write a short implementation brief containing product purpose, actors/roles, main records, actions, ownership, lifecycle states, required integrations, and success scenarios. Infer reasonable defaults where requirements permit. Keep a domain-specific vocabulary; preserve the architectural patterns rather than blindly renaming every entity.

| Classification | Pattern learned here | Meaning | Example adaptations |
| --- | --- | --- | --- |
| Recommendation | User + role + optional role profile | Authentication identity distinct from domain profile | Customer/staff, patient/doctor, member/manager |
| Recommendation | Course / catalog resource | Something discoverable that can be joined or assigned | Service, workshop, room, subscription plan |
| Recommendation | StudentCourse relationship | A user-to-resource relation carrying its own dates/status | Booking, enrollment, subscription, participation |
| Recommendation | FacultyCourse relationship | Who may manage a resource | Instructor assignment, provider coverage, team stewardship |
| Recommendation | Task + TaskPoint | Parent work item with child checklist | Order fulfillment, onboarding, service job, project task |
| Recommendation | Attendance | Dated event with uniqueness and eligibility rules | Check-in, visit, activity log, daily report |
| Recommendation | LeaveRequest | Request followed by authorized decision | Expense approval, booking change, access request |
| Recommendation | Role dashboard | Scoped aggregate projection | Own bookings; staff open jobs; admin system totals |

**Recommendation:** For a scheduling idea, define time-slot capacity and overlap constraints; an academic-session uniqueness rule is insufficient. For commerce, model money in fixed-precision decimals, payment states and verified webhooks. For healthcare, define record visibility and audit trails. For content or collaboration, add file/version permissions and realtime only when requested. These requirements extend the shared SPA/REST/database foundation.

**Recommendation:** A useful default MVP is: local registration/login/logout, role navigation, admin-managed core resource, user-owned relationship/request, one permitted state change, own-record list/detail, dashboard and profile. Every required action needs an endpoint, persistence, a usable UI control, validation, and error feedback.

### 2. Choose one coherent stack and repository structure

**Recommendation:** For a small management app, use React + Vite + JavaScript/JSX, React Router, Axios, Bootstrap/handwritten CSS; Spring Boot + Java, Spring Web MVC, Security, Validation, Data JPA and MySQL. Use Context for auth and local state first, as the college app does. Add Redux Toolkit when shared business state across many screens justifies its complexity. Avoid copying unused chart/calendar/drag libraries.

**Recommendation:** Select a mutually compatible supported Java/Spring Boot/Maven combination and verify it. Java 21 + Boot 3.5-style APIs match the office reference; the college declares a different Java/Boot generation. Do not mix their starter names/security APIs without checking that chosen generation. Commit frontend lockfiles and the backend wrapper. Version numbers in this report describe the supplied snapshot, not a universal package recommendation.


**Recommendation — original example/source projection:**

```text
new-project/
  README.md                   # prerequisites, setup, credentials provisioning, run/tests
  .gitignore                  # env secrets, node_modules, dist, target
  frontend/
    package.json, package-lock.json, vite.config.js, .env.example
    src/
      main.jsx, App.jsx, styles.css
      api/client.js           # base URL, auth/CSRF, shared error extraction
      auth/AuthContext.jsx, ProtectedRoute.jsx
      components/AppLayout.jsx, Loading.jsx, ErrorAlert.jsx
      features/auth/Login.jsx, Register.jsx
      features/resources/List.jsx, Editor.jsx, Detail.jsx
      features/requests/MyRequests.jsx, ReviewRequests.jsx
      features/dashboard/Dashboard.jsx
  backend/
    pom.xml, mvnw, mvnw.cmd, .mvn/wrapper/
    src/main/java/com/example/app/
      Application.java
      config/SecurityConfig.java
      auth/AuthController.java, AccountService.java, CurrentUser.java
      users/User.java, UserRepository.java, UserResponse.java
      resources/Resource.java, ResourceRepository.java
      resources/ResourceService.java, ResourceController.java, dto/
      requests/Request.java, RequestService.java, RequestController.java
      common/ApiExceptionHandler.java
    src/main/resources/application.properties
    src/main/resources/db/migration/   # if adding Flyway
    src/test/java/...                 # business/security/integration checks
```

**Recommendation:** Package by feature or use controller/service/repository/entity folders consistently. Keep Java sources in src/main/java and React in its own frontend directory. Do not reproduce the office's duplicated source tree.

### 3. Model the database before the screens

**Recommendation:** Define fields, required constraints, indexes, relations, deletion policies and state transitions. Use generated IDs, enum strings, consistent date/time types, and explicit foreign keys. Identity has a password hash that is never a response field. Use link tables when a relation has attributes; a booking/enrollment is a first-class record, not just a list of IDs inside User.

**Recommendation:** For the reference work-management domain:


**Recommendation — original example/source projection:**

```text
users(id, full_name, email UNIQUE, password_hash, role, status, created_at)
resources(id, name, description, active)
memberships(id, user_id FK, resource_id FK, period, status,
            UNIQUE(user_id, resource_id, period))
work_items(id, title, description, assignee_id FK, created_by_id FK,
           status, priority, start_date, due_date, version, created_at)
checklist_points(id, work_item_id FK NOT NULL, title, completed)
requests(id, owner_id FK, start_date, end_date, reason, status,
         decided_by_id FK NULL, decided_at NULL, version)
activity(id, membership_id FK, event_date, status, recorded_by_id FK,
         UNIQUE(membership_id, event_date))
```

**Recommendation:** Resolve who owns each relationship. In JPA, the side with the foreign key must be set. For a new task with points, construct the parent, set `point.setWorkItem(parent)` for every point, add them to the parent list, and save once inside a service transaction. Both sides must agree; cascade alone does not fill an unset child FK.

**Recommendation:** Protect duplicate business operations with a database unique constraint as well as a user-friendly precheck. Two concurrent requests can both pass a precheck. Catch the resulting integrity violation and map it to 409. Use `@Version` for updates where concurrent status decisions matter; a version conflict should not silently overwrite another decision.

**Recommendation:** Use `LocalDate` for leave/attendance calendar dates. Define a business timezone and weekday/holiday policy. Use `Instant`/UTC for audit/event timestamps and convert for display. Compute totals server-side; browser calculations are previews. Define restrictive deletion/reassignment behavior when records have dependents.

**Recommendation:** For a new deployment, add Flyway or Liquibase and schema migrations; use `ddl-auto=validate` once migrations own the schema. This is a recommended extension: neither supplied project currently includes migration tooling.

### 4. Freeze frontend/backend contracts

**Recommendation:** Write a contract table before implementation: method/path, permitted roles, ownership, request DTO, success DTO/status, validation and failure statuses. The field names in JSX and Java records must agree. Return DTOs consistently for both reads and mutations; avoid office's mixing of flat DTOs and raw entities.

**Recommendation:** Example contract for a new work-item module, **not either repository's existing API**:

| Classification | Request | Access and rule | Input | Success |
| --- | --- | --- | --- | --- |
| Recommendation | GET `/api/auth/csrf` | Public | None | **Inference:** 200 `{token}` |
| Recommendation | POST `/api/auth/register` | Public; server forces MEMBER | Registration DTO | **Inference:** 201 safe account/message; no password/hash |
| Recommendation | POST `/api/auth/login` | Public; ACTIVE account | Chosen login format | **Inference:** 200, authenticated session, safe account via `/me` |
| Recommendation | GET `/api/auth/me` | Signed in; ACTIVE | None | **Inference:** 200 `{id,fullName,email,role,status}` |
| Recommendation | POST `/api/auth/logout` | CSRF-checked | None | **Inference:** 204; session invalidated |
| Recommendation | GET `/api/users/assignable` | ADMIN | Optional search | **Inference:** 200 minimal active-user DTOs |
| Recommendation | GET `/api/work-items` | ADMIN gets all, MEMBER gets own | Optional page/search/status | **Inference:** 200 `{items,page,size,totalElements}` |
| Recommendation | POST `/api/work-items` | ADMIN | `{title,description,assigneeId,dueDate,points}` | **Inference:** 201 WorkItemResponse |
| Recommendation | PATCH `/api/work-items/{id}/status` | ADMIN or assignee; allowed transition | `{status,version}` | **Inference:** 200 WorkItemResponse |
| Recommendation | GET `/api/dashboard` | Signed in; scope by role | None | **Inference:** 200 named counts |

**Recommendation:** Example response:


**Recommendation — original example/source projection:**

```json
{
  "id": 7,
  "title": "Prepare an event",
  "description": "Arrange venue and materials",
  "assigneeId": 2,
  "assigneeName": "Example Member",
  "status": "PENDING",
  "dueDate": "2026-12-05",
  "version": 0,
  "points": [{"id": 31, "title": "Confirm venue", "completed": false}]
}
```

**Recommendation:** Standardize an error envelope such as `{code,message,fieldErrors}`. Use 400 for invalid input, 401 for missing/expired identity, 403 for denied permission, 404 for missing or deliberately concealed inaccessible records, 409 for duplicates/version/transition conflicts, and 500 with a generic message for unexpected failures. Preserve internal details in controlled logs, not in API responses.

### 5. Implement authentication completely

**Recommendation:** Choose **session + CSRF** for a browser SPA served with its backend, following the college integration but fixing its custom-login shortcomings. Choose bearer JWT if the product needs stateless API/mobile clients, following the office mechanics but fixing public role assignment, status, storage and ownership gaps. Never combine a JWT frontend interceptor with a session-only backend and assume authentication is connected.

| Classification | Requirement | Session design | JWT design |
| --- | --- | --- | --- |
| Recommendation | Credential | HttpOnly server session cookie | Signed access token |
| Recommendation | Frontend client | withCredentials + CSRF on unsafe requests | Authorization: Bearer header |
| Recommendation | CSRF | Keep enabled; fetch token and attach agreed header | Evaluate how credentials are transported; tokens in cookies still need CSRF protection |
| Recommendation | Logout | Invalidate server session/security context | Remove token plus deliberate refresh/revocation design |
| Recommendation | Role/status updates | Recheck current account where needed; expire invalid sessions | Short lifetime or fresh account/token-version check; signed old claims can be stale |
| Recommendation | Browser storage | Do not store session credential in localStorage | Make explicit XSS/storage tradeoff; never casually expose refresh credentials |

**Recommendation:** Public registration must force the least privileged role. Bootstrap one admin through environment-controlled initialization, never a public ADMIN dropdown. Hash passwords with BCrypt/appropriate encoder; validate password size including byte limits if using BCrypt. Normalize email once before uniqueness checks, lookup and storage. Account status must be enforced at authentication and protected operations.

**Recommendation:** For session login, use a standard Spring Security authentication filter or invoke the configured SessionAuthenticationStrategy and SecurityContextRepository properly. This ensures session ID rotation, context persistence and CSRF token lifecycle. Merely assigning `SPRING_SECURITY_CONTEXT` as the college controller does is insufficient evidence that all normal login safeguards ran.

**Recommendation:** For OAuth, implement verified provider identity -> approved database user -> app role authorities -> consistent CurrentUser resolution before adding the login button. Handle denied/pending users by rejecting or clearing authentication. Add activation/profile-completion/account-link flows if required. Configure callback/redirect origins from validated server configuration. Test Google sub versus email mapping, role authorization and status denial; `/me` succeeding alone is insufficient.

### 6. Reference session-security wiring

**Recommendation:** This illustrative configuration uses **Boot 3.x / Security 6-style APIs** and standard form authentication. It deliberately changes the new login request to URL-encoded `email/password`, unlike the existing college JSON login. Keep this choice documented in the new contract and client. It demonstrates framework-managed session authentication; verify against the chosen versions. Omitted UserDetailsService/encoder beans must be implemented as described below.


**Recommendation — original example/source projection:**

```java
@Configuration
@EnableMethodSecurity
class SecurityConfig {
    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    SecurityFilterChain security(HttpSecurity http) throws Exception {
        // CSRF endpoint returns the raw token; client sends it in X-XSRF-TOKEN.
        // Keep this handler and frontend token transport in agreement.
        var csrfRepository = new CookieCsrfTokenRepository();
        var csrfHandler = new CsrfTokenRequestAttributeHandler();

        http.cors(Customizer.withDefaults())
            .csrf(csrf -> csrf
                .csrfTokenRepository(csrfRepository)
                .csrfTokenRequestHandler(csrfHandler))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                .requestMatchers("/api/health", "/api/auth/csrf",
                    "/api/auth/register", "/api/auth/login", "/error").permitAll()
                .anyRequest().authenticated())
            .formLogin(form -> form
                .loginProcessingUrl("/api/auth/login")
                .usernameParameter("email")
                .successHandler((req, res, auth) -> {
                    res.setContentType("application/json");
                    res.getWriter().write("{\"message\":\"Signed in\"}");
                })
                .failureHandler((req, res, error) -> {
                    res.setStatus(401);
                    res.setContentType("application/json");
                    res.getWriter().write("{\"code\":\"INVALID_LOGIN\",\"message\":\"Unable to sign in\"}");
                }))
            .httpBasic(basic -> basic.disable())
            .exceptionHandling(errors -> errors
                .authenticationEntryPoint((req, res, error) -> {
                    res.setStatus(401);
                    res.setContentType("application/json");
                    res.getWriter().write("{\"code\":\"UNAUTHENTICATED\",\"message\":\"Please sign in\"}");
                })
                .accessDeniedHandler((req, res, error) -> {
                    res.setStatus(403);
                    res.setContentType("application/json");
                    res.getWriter().write("{\"code\":\"FORBIDDEN\",\"message\":\"Access denied\"}");
                }))
            .logout(logout -> logout
                .logoutUrl("/api/auth/logout")
                .invalidateHttpSession(true)
                .clearAuthentication(true)
                .deleteCookies("JSESSIONID")
                .logoutSuccessHandler((req, res, auth) -> res.setStatus(204)));
        return http.build();
    }
}
```

**Recommendation:** Add a CorsConfigurationSource bean using configurable exact frontend origin, credentials=true, agreed methods, and Content-Type/X-XSRF-TOKEN headers. Use an appropriate same-origin reverse proxy in production; set session cookie HttpOnly/Secure/SameSite deliberately. This code does not itself provide rate limiting, account registration, role rules or business ownership.

**Recommendation:** Required accompanying backend auth implementation:

1. **Recommendation:** UserRepository finds normalized email; DatabaseUserDetailsService rejects non-ACTIVE accounts and returns password hash plus ROLE_ADMIN or ROLE_MEMBER.
2. **Recommendation:** AccountService.register validates fields, forces MEMBER, hashes password, saves in a transaction and maps a safe UserResponse. Duplicate races return 409.
3. **Recommendation:** AuthController exposes GET csrf(CsrfToken) -> `{token}` and GET me(Authentication) -> safe UserResponse. No custom login controller is needed for this form-filter recipe. No password/hash is serialized.
4. **Recommendation:** CurrentUser loads the app account from the authenticated principal, requires ACTIVE and supplies its stable ID to services. For OAuth, replace generic name resolution with a centralized provider/app identity resolver.
5. **Recommendation:** Admin provisioning reads secret/config values from the server environment, runs only when needed, and never accepts public elevation.

### 7. Reference frontend API and account flow

**Recommendation:** This client matches the **new form-filter recipe above**, not the original college JSON-login API. Axios token handling is centralized. Refresh CSRF after authentication/logout because security may clear the previous token.


**Recommendation — original example/source projection:**

```jsx
// src/api/client.js
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api",
  withCredentials: true,
  timeout: 15000,
});
let csrfToken;
let csrfRequest;

export async function refreshCsrf() {
  csrfToken = undefined;
  if (!csrfRequest) {
    csrfRequest = api.get("/auth/csrf")
      .then(({ data }) => { csrfToken = data.token; return csrfToken; })
      .finally(() => { csrfRequest = undefined; });
  }
  return csrfRequest;
}
api.interceptors.request.use(async (config) => {
  if (["post", "put", "patch", "delete"].includes(config.method?.toLowerCase())) {
    if (!csrfToken) await refreshCsrf();
    config.headers["X-XSRF-TOKEN"] = csrfToken;
  }
  return config;
});
export const errorMessage = (error) =>
  error.response?.data?.message || error.message || "Request failed";

export async function passwordLogin(email, password) {
  await refreshCsrf();
  await api.post("/auth/login", new URLSearchParams({ email, password }), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  await refreshCsrf();
  return (await api.get("/auth/me")).data;
}
export async function logoutSession() {
  await api.post("/auth/logout");
  await refreshCsrf();
}
```

**Recommendation:** Implement AuthProvider with `{user,initializing,loadError,login,register,logout}`. On startup, GET `/auth/me` with credentials after fetching CSRF. Treat 401 as signed out; retain connection errors separately. Login calls passwordLogin and sets account; logout clears account only after session invalidation succeeds, while reporting failures. On protected-request 401, clear account and redirect to login; retain 403 as access denial. Do not blindly retry writes after a CSRF/network failure.

**Recommendation:** Implement `ProtectedRoute({allowedRoles})` that waits for initialization, redirects no user to login, and shows/redirects on wrong role. Use constants for paths and roles so router/sidebar/profile links match. Route structure:


**Recommendation — original example/source projection:**

```text
/login, /register                  public
/dashboard                        any signed-in role
/admin/users, /admin/resources     ADMIN
/admin/work-items, /admin/reviews   ADMIN
/my/work-items, /my/requests        MEMBER, scoped by backend
/profile                          any signed-in role
```

**Recommendation:** The screen state model should contain data, loading, error, success and submitting separately. Use labeled controlled inputs; native validation plus fieldErrors from the server; disable double submission; await save before reset/close; cancel obsolete fetches; update or refetch the real server DTO after a mutation. Keep profile image inputs out of the UI until a real upload contract/storage/access policy exists.

### 8. Build one complete vertical feature

**Recommendation:** Implement one feature all the way through database, repository, service, controller, API client, form and list before expanding modules. The following service algorithm is explicit enough to adapt to any domain; IDs from requests are references to validate, never proof of authority.


**Recommendation — original example/source projection:**

```java
// Request/response records; Java imports and surrounding entity definitions omitted.
record NewPoint(@NotBlank @Size(max = 500) String title) {}
record CreateWorkItem(
    @NotBlank @Size(max = 200) String title,
    @Size(max = 2000) String description,
    @NotNull @Positive Long assigneeId,
    @NotNull LocalDate dueDate,
    @NotNull @Size(max = 50) List<@Valid NewPoint> points) {}
record ChangeStatus(@NotNull WorkStatus status, @NotNull Long version) {}
record PointResponse(Long id, String title, boolean completed) {}
record WorkItemResponse(Long id, String title, String description,
    Long assigneeId, String assigneeName, WorkStatus status, LocalDate dueDate,
    Long version, List<PointResponse> points) {}
```

**Recommendation:** Entity requirements: WorkItem has mandatory assignee/creator relations, `@Enumerated(STRING)` status, dueDate, creation timestamp, `@Version Long version`, and initialized child list with cascade/orphan removal. Point has mandatory owning work_item_id. Constructors/setters enforce non-null association state. Response mapping occurs while required relations are available, never by returning lazy entity graphs directly.

**Recommendation:** Transactional service implementation requirements:


**Recommendation — original example/source projection:**

```text
create(request):
  actor = CurrentUser.requireActive()
  require actor.role == ADMIN
  assignee = users.findById(request.assigneeId), else 404
  require assignee ACTIVE and allowed role
  validate dueDate and all requested point titles
  parent = WorkItem(title.trim(), description, actor, assignee, PENDING, dueDate)
  for each requested point:
    point = Point(trimmed title, false)
    point.setWorkItem(parent)
    parent.points.add(point)
  saved = workItems.saveAndFlush(parent) // one @Transactional service operation
  return mapToResponse(saved)            // contains all persisted point IDs

list(pageable, filter):
  actor = CurrentUser.requireActive()
  if ADMIN: return filtered repository page
  else: return repository page restricted to assigneeId == actor.id
  map DTOs in controlled fetch/query boundaries

changeStatus(id, request):
  actor = CurrentUser.requireActive()
  item = workItems.findById(id), else 404
  require actor ADMIN or item.assigneeId == actor.id
  require request.version == item.version
  require transition allowed by domain table
  item.status = request.status
  saveAndFlush and map response
  concurrent version conflict -> 409
```

**Recommendation:** Example status transitions for this particular work domain: PENDING -> IN_PROGRESS or CANCELLED; IN_PROGRESS -> COMPLETED or ON_HOLD; ON_HOLD -> IN_PROGRESS or CANCELLED; COMPLETED/CANCELLED terminal unless an explicit admin reopen operation is required. Approval domains instead use PENDING -> APPROVED/REJECTED, record actor and timestamp, and reject repeat decisions. Define each domain's states rather than copying one transition map everywhere.

**Recommendation:** Use method security such as `@PreAuthorize("hasRole('ADMIN')")` on create/admin endpoints, plus service-level object checks. Request validation requires `@Valid @RequestBody`. Map service return values to ResponseEntity with 201 on create and 200 on update. List responses use an explicit pagination DTO instead of leaking framework page/entity internals.

**Recommendation:** Minimal controller shape:


**Recommendation — original example/source projection:**

```java
@RestController
@RequestMapping("/api/work-items")
class WorkItemController {
    private final WorkItemService service;
    WorkItemController(WorkItemService service) { this.service = service; }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    ResponseEntity<WorkItemResponse> create(@Valid @RequestBody CreateWorkItem input) {
        var result = service.create(input);
        return ResponseEntity.created(URI.create("/api/work-items/" + result.id()))
            .body(result);
    }

    @GetMapping
    PageResponse<WorkItemResponse> list(Pageable pageable) {
        return service.list(pageable); // service always scopes non-admin data
    }

    @PatchMapping("/{id}/status")
    WorkItemResponse change(@PathVariable Long id,
                           @Valid @RequestBody ChangeStatus input) {
        return service.changeStatus(id, input);
    }
}
```

**Recommendation:** These snippets are structural examples, not a complete compiled application. The implementing agent must supply imports, entities, repositories, service, CurrentUser, PageResponse, advice and tests according to the stated contract. The acceptance scenarios below determine whether that implementation is complete.

**Recommendation:** Connected frontend implementation:

1. **Recommendation:** Admin page GETs assignable users and real work-item list. Create form sends the agreed title/assignee/due-date/point JSON through shared api. After HTTP 201, render the returned DTO or refetch, clear form and announce success.
2. **Recommendation:** Member page GETs the same list endpoint; the server restricts results to that member. Do not fetch all data and filter only in the browser.
3. **Recommendation:** A permitted status button sends `{status,version}` to PATCH, updates the displayed returned DTO and handles 409 by showing a reload/conflict message. Do not optimistically show success without a persisted response.
4. **Recommendation:** Detail/checklist reads use points from WorkItemResponse or an explicit point endpoint. Every enabled checkbox/action must call an implemented authorized endpoint and reconcile the response.
5. **Recommendation:** Refresh browser and restart backend: the same records and allowed states must remain in MySQL.

### 9. Integration, uploads and security fundamentals

**Recommendation:** Authentication answers who the caller is; authorization answers which action/data they may access. CORS controls browser cross-origin access, not malicious non-browser requests. UI role guards do not secure endpoints. DTOs restrict the input/output surface; validation and service invariants protect data; database constraints protect concurrent writes. Transactions keep dependent writes atomic.

**Recommendation:** If uploads are required, implement multipart endpoint with configured maximum size, allowlisted content types, byte/content validation, generated safe filenames/object keys, storage service and authorized retrieval. Avoid trusting client filename paths or exposing a whole upload directory by default. Wire the UI to that endpoint and show the persisted returned URL after reload. For a purely optional avatar, a locally generated fallback avoids sending user names to an external avatar service.

**Recommendation:** If an external integration is required, document its purpose, server-side credentials, request/response, timeout/retry behavior, failure handling and webhook signature/idempotency rules. The backend owns secrets; the frontend receives only public identifiers/URLs. The original apps have no payment, mail, object-store, queue or realtime service to reuse. Add the provider SDK only when the idea calls for it and implement both success and failure behavior.

**Recommendation:** Baseline reconstructed security: force public role; BCrypt password hashing; safe response DTOs; active-account checks; role + ownership checks; CSRF for session auth; exact CORS allowlist; standardized errors; request limits/validation; HTTPS and secure cookies; no exposed secrets; limited database user; conservative logs. Add audit events for sensitive status/role/approval changes. Account recovery/email verification/rate limiting are separate features to implement when requirements call for them; do not claim these original repositories already provide them.

### 10. Run and deploy a connected pair

**Recommendation:** Create README with exact tested prerequisites/versions, development schema creation, secret provisioning, admin initialization, commands and role workflow. Commit examples with placeholders, never actual credentials. Example configuration for a new implementation:


**Recommendation — original example/source projection:**

```properties
# backend application.properties -- proposed, not an existing config file
server.port=${SERVER_PORT:8080}
spring.datasource.url=${DB_URL}
spring.datasource.username=${DB_USERNAME}
spring.datasource.password=${DB_PASSWORD}
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.open-in-view=false
app.frontend-origin=${FRONTEND_ORIGIN:http://localhost:5173}
app.bootstrap-admin.email=${BOOTSTRAP_ADMIN_EMAIL:}
app.bootstrap-admin.password=${BOOTSTRAP_ADMIN_PASSWORD:}
```

**Recommendation:** This `ddl-auto=validate` setup requires migrations/schema provisioning first. If using a temporary isolated development schema with `update`, document that profile explicitly. DTO mapping/queries must load needed relations before the transaction ends with open-in-view disabled.


**Recommendation — original example/source projection:**

```dotenv
# frontend .env.example -- public values only
VITE_API_BASE_URL=http://localhost:8080/api
```

**Recommendation:** Development launch from the new repository:


**Recommendation — original example/source projection:**

```powershell
# Terminal 1: backend. Provide DB_URL, DB_USERNAME, DB_PASSWORD beforehand.
Set-Location backend
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run

# Terminal 2: frontend.
Set-Location frontend
npm.cmd ci
npm.cmd run dev -- --host localhost --port 5173 --strictPort

# Before delivery:
npm.cmd run build
```

**Recommendation:** Those are instructions for the newly built project, not tool results from this investigation. Use strictPort with an exact CORS origin. If another app occupies 8080/5173, choose a new pair and update every URL/CORS/cookie/OAuth setting. Do not accidentally connect a college frontend to the office backend just because both listen on 8080.

**Recommendation:** For production, build static frontend assets and serve behind an HTTPS reverse proxy; proxy `/api` and required auth paths to the Java service. Serve index.html for SPA routes while API misses remain JSON errors. Keep secrets in server configuration; configure cookies, trusted origins, OAuth callbacks, SQL logging and database backups. Add Docker/Compose/CI when requested or useful for reproducible delivery; neither original project supplies a complete deployment pipeline.

### 11. Acceptance checks and completion criteria

**Recommendation:** Use tests for material business/security behavior and a browser smoke test for the connected workflow. A compile check and mocks cannot prove database persistence, authentication or role separation.

| Classification | Check | Required result |
| --- | --- | --- |
| Recommendation | Clean frontend install/build and backend compile/tests | Agreed versions resolve; builds succeed; commands recorded |
| Recommendation | Health + database startup | Real server runs against intended isolated schema |
| Recommendation | Register/login/me/reload/logout | Account persists, session/token works, refresh restores identity, logout denies protected access |
| Recommendation | Missing identity / wrong role | Stable 401/403; no data returned or write accepted |
| Recommendation | Another user's IDs | Object-level denial; changing an ID cannot expose/edit another user's record |
| Recommendation | Create primary resource with children | One transaction; linked child FKs; no duplicate/ownerless rows |
| Recommendation | Form validation and error display | Invalid fields show clear server-consistent feedback; form remains available |
| Recommendation | Duplicate/concurrent write | Constraint/version conflict returns 409; no double enrollment/decision |
| Recommendation | Domain rule | Date/ownership/state/capacity rules enforced by backend and reflected in UI |
| Recommendation | Real user workflow | Admin creates -> member acts -> authorized actor decides/updates -> affected user sees result |
| Recommendation | Persistence | Browser reload and backend restart retain the same result |
| Recommendation | Route navigation | Every menu/profile link resolves; direct SPA reload works |
| Recommendation | UI completeness | No advertised action remains empty/unwired; loading/error/empty states work |
| Recommendation | OAuth if required | Identity/role/status/link/denial and callback behavior verified |
| Recommendation | Secrets/config | No passwords/signing keys in frontend, repository or response bodies |

**Recommendation:** Meaningful backend tests should cover service transactions and constraints plus HTTP authentication/CSRF/role/ownership behavior. Use an appropriate isolated MySQL/test database; Testcontainers is an optional added dependency when Docker is available. Frontend tests can verify account loading, error behavior and user actions; Playwright/equivalent can exercise the real pair. These test tools are recommendations, not original dependencies.

**Recommendation:** The final delivery should contain the implemented source, schema/migrations, example environment files, README, actual verification results, and any precisely bounded unresolved integration prerequisites. Complete required frontend **and** backend flows before reporting the app working.

### Ready-to-use prompt for another agent


**Recommendation — original example/source projection:**

```text
Read REA_FULLSTACK_PROJECT_GUIDE.md, including the reconstruction blueprint
and defects of the two source examples. Build a working full-stack project
for this idea: <INSERT IDEA AND REQUIREMENTS>.

Use React/Vite and a compatible Java/Spring Boot/MySQL stack unless my
requirements specify otherwise. Define roles, schema, DTO/API contracts,
ownership, state transitions and an acceptance flow first. Choose one auth
model and wire the frontend client correctly. Build all required actions
through UI -> secured API -> transactional service -> persistent database.
Use safe DTOs, server-derived identity and real role/object authorization.
Correct the documented source defects; preserve useful patterns.

Supply working frontend and backend, database setup/migrations, environment
examples, admin provisioning, README/run instructions and checks actually
executed. Verify login, role denial, domain mutations and reload persistence.
Do not treat mock data, an empty screen or a frontend build alone as a working
application. Adapt the business rules to my idea rather than copying college
or office rules without justification.
```
