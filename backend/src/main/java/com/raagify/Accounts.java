package com.raagify;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Locale;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Service
public class Accounts implements ApplicationRunner {
    public record UserDto(long id, String displayName, String email, String role) {}
    public record Register(@NotBlank @Size(max=100) String displayName,
                           @NotBlank @Email @Size(max=190) String email,
                           @NotBlank @Size(min=10, max=72) String password) {}
    private final JdbcTemplate jdbc;
    private final PasswordEncoder passwords;
    private final String adminEmail;
    private final String adminPassword;
    private final String adminName;

    public Accounts(JdbcTemplate jdbc, PasswordEncoder passwords,
                    @Value("${app.bootstrap.admin-email}") String adminEmail,
                    @Value("${app.bootstrap.admin-password}") String adminPassword,
                    @Value("${app.bootstrap.admin-name}") String adminName) {
        this.jdbc = jdbc; this.passwords = passwords; this.adminEmail = adminEmail;
        this.adminPassword = adminPassword; this.adminName = adminName;
    }

    @Transactional
    public UserDto register(Register request) {
        String email = normalize(request.email());
        if (request.password().getBytes(java.nio.charset.StandardCharsets.UTF_8).length > 72)
            throw new ApiException(400, "Password must be at most 72 UTF-8 bytes");
        if (jdbc.queryForObject("SELECT COUNT(*) FROM users WHERE email=?", Integer.class, email) > 0)
            throw new ApiException(409, "An account with that email already exists");
        jdbc.update("INSERT INTO users(display_name,email,password_hash,role) VALUES(?,?,?,'LISTENER')",
            request.displayName().trim(), email, passwords.encode(request.password()));
        return byEmail(email);
    }

    public UserDto current() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || "anonymousUser".equals(auth.getPrincipal()))
            throw new ApiException(401, "Authentication required");
        return byEmail(auth.getName());
    }

    public UserDto byEmail(String email) {
        return jdbc.query("SELECT id,display_name,email,role FROM users WHERE email=?",
            (rs, row) -> new UserDto(rs.getLong("id"), rs.getString("display_name"), rs.getString("email"), rs.getString("role")),
            normalize(email)).stream().findFirst().orElseThrow(() -> new ApiException(401, "Account no longer exists"));
    }

    @Override @Transactional
    public void run(ApplicationArguments args) {
        if (adminEmail == null || adminEmail.isBlank() || adminPassword == null || adminPassword.isBlank()) return;
        if (adminPassword.length() < 12 || adminPassword.getBytes(java.nio.charset.StandardCharsets.UTF_8).length > 72)
            throw new IllegalStateException("ADMIN_PASSWORD must contain at least 12 characters and at most 72 UTF-8 bytes");
        String email = normalize(adminEmail);
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM users WHERE email=?", Integer.class, email);
        if (count != null && count > 0 && !byEmail(email).role().equals("ADMIN"))
            throw new IllegalStateException("Bootstrap email already belongs to a listener; choose a private administrator email");
        if (count != null && count == 0) jdbc.update(
            "INSERT INTO users(display_name,email,password_hash,role) VALUES(?,?,?,'ADMIN')",
            adminName.trim(), email, passwords.encode(adminPassword));
    }

    private static String normalize(String email) { return email.trim().toLowerCase(Locale.ROOT); }
}

@RestController
@RequestMapping("/api/auth")
class AuthController {
    private final Accounts accounts;
    AuthController(Accounts accounts) { this.accounts = accounts; }

    @GetMapping("/csrf") java.util.Map<String, String> csrf(org.springframework.security.web.csrf.CsrfToken token) {
        return java.util.Map.of("headerName", token.getHeaderName(), "token", token.getToken());
    }
    @PostMapping("/register") org.springframework.http.ResponseEntity<Accounts.UserDto> register(@Valid @RequestBody Accounts.Register request) {
        return org.springframework.http.ResponseEntity.status(201).body(accounts.register(request));
    }
    @GetMapping("/me") Accounts.UserDto me() { return accounts.current(); }
    record SessionDto(Accounts.UserDto user) {}
    @GetMapping("/session") SessionDto session(Authentication authentication) {
        boolean signedIn = authentication != null && authentication.isAuthenticated()
            && !(authentication instanceof org.springframework.security.authentication.AnonymousAuthenticationToken);
        return new SessionDto(signedIn ? accounts.current() : null);
    }
}
