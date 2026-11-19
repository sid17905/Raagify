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
public class MediaClient {
    public record Analysis(List<Double> vector, String genre, String genreSource, boolean available) {}
    public record EmbeddedArtwork(String coverContentType,String coverBase64) {}
    public record Health(String status) {}
    public record Metadata(String title,String artist,String album,String genre,Integer durationSeconds,String coverContentType,String coverBase64) {}
    private final RestClient client;
    private final RestClient healthClient;

    public MediaClient(@Value("${app.media.base-url}") String base,
                    @Value("${app.media.connect-timeout-ms}") int connect,
                    @Value("${app.media.read-timeout-ms}") int read) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connect); factory.setReadTimeout(read);
        this.client = RestClient.builder().baseUrl(base).requestFactory(factory).build();
        var healthFactory=new SimpleClientHttpRequestFactory();healthFactory.setConnectTimeout(Math.min(connect,750));healthFactory.setReadTimeout(1000);
        this.healthClient=RestClient.builder().baseUrl(base).requestFactory(healthFactory).build();
    }

    public Analysis analyze(Path path) {
        try {
            var body = new LinkedMultiValueMap<String, Object>();
            body.add("file", new FileSystemResource(path));
            Analysis result = client.post().uri("/analyze-file").contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body).retrieve().body(Analysis.class);
            if (result == null || !result.available() || result.vector() == null || result.vector().size() != 27
                || result.vector().stream().anyMatch(v -> v == null || !Double.isFinite(v))
                || result.genre() == null || result.genre().isBlank() || result.genre().length() > 80)
                return unavailable();
            if(result.genreSource()==null||!java.util.Set.of("METADATA","UNCLASSIFIED").contains(result.genreSource()))return unavailable();
            return result;
        } catch (RestClientException error) { return unavailable(); }
    }

    public EmbeddedArtwork artwork(Path path){
        try{var body=new LinkedMultiValueMap<String,Object>();body.add("file",new FileSystemResource(path));return client.post().uri("/artwork-file").contentType(MediaType.MULTIPART_FORM_DATA).body(body).retrieve().body(EmbeddedArtwork.class);}
        catch(RestClientException ex){return null;}
    }
    public Health health(){try{var health=healthClient.get().uri("/health").retrieve().body(Health.class);return health==null?new Health("UNAVAILABLE"):health;}catch(RestClientException ex){return new Health("UNAVAILABLE");}}
    public Metadata metadata(org.springframework.web.multipart.MultipartFile file){return metadataResource(file.getResource());}
    public Metadata metadata(Path path){return metadataResource(new FileSystemResource(path));}
    private Metadata metadataResource(org.springframework.core.io.Resource resource){try{var body=new LinkedMultiValueMap<String,Object>();body.add("file",resource);return client.post().uri("/metadata-file").contentType(MediaType.MULTIPART_FORM_DATA).body(body).retrieve().body(Metadata.class);}catch(RestClientException ex){return null;}}
    private static Analysis unavailable() { return new Analysis(List.of(), null, "UNAVAILABLE", false); }
}
