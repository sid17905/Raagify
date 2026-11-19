package com.raagify;

import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class ApiExceptionHandler {
    public record ApiError(String code, String message, Map<String, String> fieldErrors) {}

    @ExceptionHandler(ApiException.class)
    ResponseEntity<ApiError> domain(ApiException ex) {
        return ResponseEntity.status(ex.status()).body(new ApiError(code(ex.status()), ex.getMessage(), Map.of()));
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiError> validation(MethodArgumentNotValidException ex) {
        var fields = new LinkedHashMap<String, String>();
        ex.getBindingResult().getFieldErrors().forEach(e -> fields.putIfAbsent(e.getField(), e.getDefaultMessage()));
        return ResponseEntity.badRequest().body(new ApiError("VALIDATION", "Check the submitted fields", fields));
    }
    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<ApiError> malformed(HttpMessageNotReadableException ex) {
        return ResponseEntity.badRequest().body(new ApiError("INVALID_JSON", "Invalid request body", Map.of()));
    }
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<ApiError> conflict(DataIntegrityViolationException ex) {
        return ResponseEntity.status(409).body(new ApiError("CONFLICT", "The record conflicts with existing data", Map.of()));
    }
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    ResponseEntity<ApiError> tooLarge(MaxUploadSizeExceededException ex) {
        return ResponseEntity.status(413).body(new ApiError("FILE_TOO_LARGE", "Upload exceeds the configured request limit", Map.of()));
    }
    @ExceptionHandler({org.springframework.web.method.annotation.MethodArgumentTypeMismatchException.class,
        org.springframework.web.bind.MissingServletRequestParameterException.class})
    ResponseEntity<ApiError> invalidParameter(Exception ex) {
        return ResponseEntity.badRequest().body(new ApiError("BAD_REQUEST", "Invalid or missing request parameter", Map.of()));
    }
    @ExceptionHandler(Exception.class)
    ResponseEntity<ApiError> unexpected(Exception ex) {
        org.slf4j.LoggerFactory.getLogger(getClass()).error("Unexpected request failure", ex);
        return ResponseEntity.internalServerError().body(new ApiError("INTERNAL_ERROR", "The request could not be completed", Map.of()));
    }
    private static String code(int status) {
        return switch (status) { case 400 -> "BAD_REQUEST"; case 401 -> "UNAUTHENTICATED"; case 403 -> "FORBIDDEN"; case 404 -> "NOT_FOUND"; case 409 -> "CONFLICT"; default -> "REQUEST_REJECTED"; };
    }
}
