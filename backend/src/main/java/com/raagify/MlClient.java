package com.raagify;

import java.nio.file.Path;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
public class MlClient {
    public record Analysis(List<Double> vector, String predictedGenre, String genreSource,
                           boolean placeholder, boolean available) {}
    private final RestClient client;

    public MlClient(@Value("${app.ml.base-url}") String base,
                    @Value("${app.ml.connect-timeout-ms}") int connect,
                    @Value("${app.ml.read-timeout-ms}") int read) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connect); factory.setReadTimeout(read);
        this.client = RestClient.builder().baseUrl(base).requestFactory(factory).build();
    }

    public Analysis analyze(Path path) {
        try {
            var body = new LinkedMultiValueMap<String, Object>();
            body.add("file", new FileSystemResource(path));
            Analysis result = client.post().uri("/analyze-file").contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body).retrieve().body(Analysis.class);
            if (result == null || !result.available() || result.vector() == null || result.vector().size() != 27
                || result.vector().stream().anyMatch(v -> v == null || !Double.isFinite(v))
                || result.predictedGenre() == null || result.predictedGenre().isBlank() || result.predictedGenre().length() > 80)
                return unavailable();
            return new Analysis(result.vector(), result.predictedGenre(), result.placeholder() ? "PLACEHOLDER" : "MODEL", result.placeholder(), true);
        } catch (RestClientException error) { return unavailable(); }
    }

    private static Analysis unavailable() { return new Analysis(List.of(), null, "ML_UNAVAILABLE", true, false); }
}
