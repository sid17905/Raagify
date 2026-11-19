package com.raagify;

import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfTokenRequestAttributeHandler;

@Configuration
public class SecurityConfig {
    @Bean PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }

    @Bean
    UserDetailsService users(org.springframework.jdbc.core.JdbcTemplate jdbc) {
        return email -> jdbc.query("SELECT email,password_hash,role FROM users WHERE email=?",
            (rs, row) -> User.withUsername(rs.getString("email"))
                .password(rs.getString("password_hash")).roles(rs.getString("role")).build(),
            email.trim().toLowerCase(java.util.Locale.ROOT)).stream().findFirst()
            .orElseThrow(() -> new org.springframework.security.core.userdetails.UsernameNotFoundException("Account not found"));
    }

    @Bean
    SecurityFilterChain security(HttpSecurity http) throws Exception {
        var csrf = CookieCsrfTokenRepository.withHttpOnlyFalse();
        csrf.setCookieName("XSRF-TOKEN");
        csrf.setHeaderName("X-XSRF-TOKEN");
        http
            .csrf(c -> c.csrfTokenRepository(csrf).csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler()))
            .authorizeHttpRequests(a -> a
                .requestMatchers("/api/auth/csrf", "/api/auth/register", "/api/health", "/error").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/**").authenticated()
                .anyRequest().permitAll())
            .formLogin(f -> f.loginProcessingUrl("/api/auth/login")
                .usernameParameter("email").passwordParameter("password")
                .successHandler((request, response, auth) -> json(response, 200, "{\"authenticated\":true}"))
                .failureHandler((request, response, error) -> json(response, 401, "{\"code\":\"UNAUTHENTICATED\",\"message\":\"Invalid email or password\",\"fieldErrors\":{}}"))
                .permitAll())
            .logout(l -> l.logoutUrl("/api/auth/logout").invalidateHttpSession(true).clearAuthentication(true)
                .deleteCookies("JSESSIONID")
                .logoutSuccessHandler((request, response, auth) -> json(response, 200, "{\"authenticated\":false}")))
            .exceptionHandling(e -> e
                .authenticationEntryPoint((request, response, error) -> json(response, 401, "{\"code\":\"UNAUTHENTICATED\",\"message\":\"Authentication required\",\"fieldErrors\":{}}"))
                .accessDeniedHandler((request, response, error) -> json(response, 403, "{\"code\":\"FORBIDDEN\",\"message\":\"Access denied\",\"fieldErrors\":{}}")))
            .headers(h -> h.contentSecurityPolicy(c -> c.policyDirectives("default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'")));
        return http.build();
    }

    private static void json(HttpServletResponse response, int status, String body) throws IOException {
        response.setStatus(status);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write(body);
    }
}
