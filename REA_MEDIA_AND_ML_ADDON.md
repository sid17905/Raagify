# Media and Python integration add-on

**Observed:** The original office and college sources do not implement audio upload/streaming or a Python ML integration. The concrete additions are in `starter/`; they are separate from the original evidence.

**Observed:** Starter Java is pinned to Java 21 + Spring Boot 3.5.0, uses Spring JDBC/MySQL/Flyway, and protects these routes with session authentication, CSRF on uploads/analysis, and owner/admin checks. Its React player uses the same-origin `/api` URL so the native audio request carries the session cookie.

**Recommendation:** Read the evidence ledger for exact executed commands. Source listings below are complete files from the tested starter. A source observation is not a claim that every codec/device/deployment was exercised.

## Contract and storage configuration

| Classification | Route | Behavior |
| --- | --- | --- |
| Observed | POST `/api/media` | Multipart `file`; returns 201 safe media metadata and streamUrl |
| Observed | GET `/api/media` | Lists the caller's media metadata |
| Observed | GET/HEAD `/api/media/{id}/stream` | Owner/admin; full response or single Range; invalid ranges 416 |
| Observed | POST `/api/ml/analyze` | Authenticated JSON samples; calls Python or returns explicit fallback |

**Observed:** Defaults: application audio size cap 4 MiB; servlet file cap 10 MB/request cap 11 MB; accepted MIME WAV/MP3/OGG; generated UUID storage filenames; metadata persisted in `media_files`. Client filenames are sanitized display names and never storage paths.

**Observed:** Upload validation checks MIME and container signature. It does not decode the entire file or prove that every byte is valid audio. Streaming reads only the requested interval using a 16 KiB buffer; it does not load an entire track into server memory.

**Observed:** The Range implementation supports closed `bytes=0-31`, suffix `bytes=-16`, and open-ended `bytes=32-`; returns 206 with Content-Range/Content-Length/Accept-Ranges; rejects invalid or multiple ranges with 416 and `Content-Range: bytes */total`.

**Recommendation:** For native authenticated audio, use the starter's same-origin session setup. The office Axios Bearer interceptor cannot inject a header into a native `<audio src>` request. A JWT media design needs a deliberate cookie or short-lived signed-URL scheme.

**Recommendation — server environment:**

```dotenv
MEDIA_STORAGE_PATH=/absolute/private/audio-directory
MEDIA_MAX_BYTES=4194304
ML_BASE_URL=http://127.0.0.1:8000
ML_CONNECT_TIMEOUT_MS=500
ML_READ_TIMEOUT_MS=1000
```

**Observed:** `starter/backend/src/main/resources/application.properties` binds those settings. RestClient's connection/read timeouts are configurable; service-down/read-timeout responses produce `{label:"unavailable",score:0,source:"fallback",available:false}` without blindly retrying the write.

## Complete multipart and storage implementation

### [MediaFiles.java](starter/backend/src/main/java/com/example/starter/MediaFiles.java)

**Observed — complete starter source:**

```java
package com.example.starter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
public class MediaFiles {
    public record Media(String id,String originalName,String contentType,long sizeBytes,String streamUrl) {}
    public record Stored(Media media,Path path) {}
    private static final Map<String,String> TYPES=Map.of("audio/wav","wav","audio/x-wav","wav","audio/mpeg","mp3","audio/ogg","ogg");
    private final JdbcTemplate jdbc;
    private final Accounts accounts;
    private final Path storage;
    private final long maxBytes;
    public MediaFiles(JdbcTemplate jdbc,Accounts accounts,@Value("${app.media.storage-path}") String directory,@Value("${app.media.max-bytes}") long maxBytes) throws IOException {
        this.jdbc=jdbc;this.accounts=accounts;this.storage=Path.of(directory).toAbsolutePath().normalize();this.maxBytes=maxBytes;
        Files.createDirectories(storage);
    }
    @Transactional
    public Media upload(MultipartFile file) throws IOException {
        var actor=accounts.current();
        if(file.isEmpty()) throw new ApiException(400,"Upload must contain audio");
        if(file.getSize()>maxBytes) throw new ApiException(413,"Audio exceeds configured size limit");
        String type=file.getContentType();
        if(type==null || !TYPES.containsKey(type)) throw new ApiException(400,"Only WAV, MP3 or OGG audio is accepted");
        byte[] prefix;
        try(var input=file.getInputStream()){prefix=input.readNBytes(12);}
        if(!validMagic(type,prefix)) throw new ApiException(400,"Content does not match the claimed audio type");
        String id=UUID.randomUUID().toString(), name=id+"."+TYPES.get(type);
        Path path=storage.resolve(name).normalize();
        if(!path.startsWith(storage)) throw new ApiException(400,"Invalid storage path");
        String original=file.getOriginalFilename()==null ? "audio" : file.getOriginalFilename().replace('\\','/');
        original=original.substring(original.lastIndexOf('/')+1).replaceAll("[\\r\\n\\p{Cntrl}]","");
        if(original.length()>200) original=original.substring(0,200);
        if(original.isBlank()) original="audio";
        try {
            try(var input=file.getInputStream()){Files.copy(input,path);}
            long actual=Files.size(path);
            if(actual>maxBytes) throw new ApiException(413,"Audio exceeds configured size limit");
            jdbc.update("INSERT INTO media_files(id,owner_id,original_name,storage_name,content_type,size_bytes) VALUES(?,?,?,?,?,?)",id,actor.id(),original,name,type,actual);
            return new Media(id,original,type,actual,"/api/media/"+id+"/stream");
        } catch(IOException|RuntimeException error){Files.deleteIfExists(path);throw error;}
    }
    public List<Media> list() {
        var actor=accounts.current();
        return jdbc.query("SELECT * FROM media_files WHERE owner_id=? ORDER BY created_at,id",(rs,n)->new Media(rs.getString("id"),rs.getString("original_name"),rs.getString("content_type"),rs.getLong("size_bytes"),"/api/media/"+rs.getString("id")+"/stream"),actor.id());
    }
    public Stored get(String id) throws IOException {
        var actor=accounts.current();
        try{UUID.fromString(id);}catch(IllegalArgumentException error){throw new ApiException(404,"Audio not found");}
        var rows=jdbc.query("SELECT * FROM media_files WHERE id=?",(rs,n)-> {
            if(actor.id()!=rs.getLong("owner_id") && !actor.role().equals("ADMIN")) throw new ApiException(403,"Audio belongs to another user");
            var media=new Media(id,rs.getString("original_name"),rs.getString("content_type"),rs.getLong("size_bytes"),"/api/media/"+id+"/stream");
            return new Stored(media,storage.resolve(rs.getString("storage_name")).normalize());
        },id);
        if(rows.isEmpty() || !rows.getFirst().path().startsWith(storage) || !Files.isRegularFile(rows.getFirst().path())) throw new ApiException(404,"Audio not found");
        return rows.getFirst();
    }
    private static boolean validMagic(String type,byte[] b) {
        if(type.equals("audio/wav") || type.equals("audio/x-wav")) return b.length>=12 && ascii(b,0,4).equals("RIFF") && ascii(b,8,4).equals("WAVE");
        if(type.equals("audio/ogg")) return b.length>=4 && ascii(b,0,4).equals("OggS");
        return b.length>=3 && (ascii(b,0,3).equals("ID3") || ((b[0]&255)==255 && (b[1]&224)==224));
    }
    private static String ascii(byte[] bytes,int offset,int size){return new String(bytes,offset,size,StandardCharsets.US_ASCII);}
}
```

### [MediaController.java](starter/backend/src/main/java/com/example/starter/MediaController.java)

**Observed — complete starter source:**

```java
package com.example.starter;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.StandardOpenOption;
import java.util.List;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/media")
public class MediaController {
    private final MediaFiles files;
    public MediaController(MediaFiles files){this.files=files;}
    @PostMapping(consumes="multipart/form-data") ResponseEntity<MediaFiles.Media> upload(@RequestParam("file") MultipartFile file) throws IOException {
        return ResponseEntity.status(201).body(files.upload(file));
    }
    @GetMapping List<MediaFiles.Media> list(){return files.list();}
    @RequestMapping(value="/{id}/stream",method={RequestMethod.GET,RequestMethod.HEAD})
    void stream(@PathVariable String id,HttpServletRequest request,HttpServletResponse response) throws IOException {
        var stored=files.get(id);long total=java.nio.file.Files.size(stored.path());
        response.setHeader("Accept-Ranges","bytes");response.setContentType(stored.media().contentType());
        response.setHeader("Cache-Control","private, no-cache");
        response.setHeader("X-Content-Type-Options","nosniff");
        String header=request.getHeader("Range");
        Range range;
        try{range=Range.parse(header,total);}catch(IllegalArgumentException error){
            response.setStatus(416);response.setHeader("Content-Range","bytes */"+total);return;
        }
        if(header!=null){response.setStatus(206);response.setHeader("Content-Range","bytes "+range.start()+"-"+range.end()+"/"+total);}
        response.setContentLengthLong(range.length());
        if(request.getMethod().equals("HEAD"))return;
        try(var channel=FileChannel.open(stored.path(),StandardOpenOption.READ)) {
            channel.position(range.start());long remaining=range.length();var buffer=ByteBuffer.allocate(16*1024);
            var output=response.getOutputStream();
            while(remaining>0){buffer.clear();buffer.limit((int)Math.min(buffer.capacity(),remaining));int read=channel.read(buffer);if(read<0)break;output.write(buffer.array(),0,read);remaining-=read;}
        }
    }
    record Range(long start,long end) {
        long length(){return end-start+1;}
        static Range parse(String header,long total) {
            if(total<=0)throw new IllegalArgumentException();
            if(header==null)return new Range(0,total-1);
            if(!header.matches("bytes=\\d*-\\d*"))throw new IllegalArgumentException();
            String[] parts=header.substring(6).split("-",-1);
            try {
                if(parts[0].isEmpty()) {
                    if(parts[1].isEmpty())throw new IllegalArgumentException();
                    long suffix=Long.parseLong(parts[1]);if(suffix<=0)throw new IllegalArgumentException();
                    return new Range(Math.max(0,total-suffix),total-1);
                }
                long start=Long.parseLong(parts[0]);long end=parts[1].isEmpty()?total-1:Long.parseLong(parts[1]);
                if(start>=total || end<start)throw new IllegalArgumentException();
                return new Range(start,Math.min(end,total-1));
            }catch(NumberFormatException error){throw new IllegalArgumentException(error);}
        }
    }
}
```

### [MlClient.java](starter/backend/src/main/java/com/example/starter/MlClient.java)

**Observed — complete starter source:**

```java
package com.example.starter;

import java.util.List;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
public class MlClient {
    public record Samples(@NotEmpty @Size(max=8192) List<@NotNull Double> samples) {}
    public record Analysis(String label,double score,String source,boolean available) {}
    private final RestClient client;
    public MlClient(@Value("${app.ml.base-url}") String base,
        @Value("${app.ml.connect-timeout-ms}") int connect,@Value("${app.ml.read-timeout-ms}") int read) {
        var factory=new SimpleClientHttpRequestFactory();factory.setConnectTimeout(connect);factory.setReadTimeout(read);
        client=RestClient.builder().baseUrl(base).requestFactory(factory).build();
    }
    public Analysis analyze(Samples samples) {
        if(samples.samples().stream().anyMatch(v -> !Double.isFinite(v) || Math.abs(v)>1))throw new ApiException(400,"Samples must be finite and between -1 and 1");
        try {
            var result=client.post().uri("/analyze").body(samples).retrieve().body(Analysis.class);
            if(result==null) return unavailable();
            return result;
        }catch(RestClientException error){return unavailable();}
    }
    private static Analysis unavailable(){return new Analysis("unavailable",0,"fallback",false);}
}
```

### [MlController.java](starter/backend/src/main/java/com/example/starter/MlController.java)

**Observed — complete starter source:**

```java
package com.example.starter;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ml")
public class MlController {
    private final MlClient client;
    public MlController(MlClient client){this.client=client;}
    @PostMapping("/analyze") MlClient.Analysis analyze(@Valid @RequestBody MlClient.Samples samples){return client.analyze(samples);}
}
```

### [app.py](starter/ml-service/app.py)

**Observed — complete starter source:**

```python
"""Illustrative feature-analysis API. This is not a trained ML model."""
from math import sqrt
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="REA illustrative audio feature service")

class Samples(BaseModel):
    samples: list[float] = Field(min_length=1, max_length=8192)

    @field_validator("samples")
    @classmethod
    def bounded_finite_samples(cls, values):
        if any(not -1 <= value <= 1 for value in values):
            raise ValueError("samples must be finite values between -1 and 1")
        return values

@app.get("/health")
def health():
    return {"status": "UP"}

@app.post("/analyze")
def analyze(request: Samples):
    rms = sqrt(sum(value * value for value in request.samples) / len(request.samples))
    return {"label": "energetic" if rms >= 0.25 else "quiet", "score": rms,
            "source": "illustrative-feature-service", "available": True}
```

### [AudioPlayer.jsx](starter/frontend/src/components/AudioPlayer.jsx)

**Observed — complete starter source:**

```jsx
export default function AudioPlayer({id, title, baseURL = "/api"}) {
  return <figure className="audio-player">
    <figcaption>{title}</figcaption>
    <audio controls preload="metadata" src={`${baseURL.replace(/\/$/, "")}/media/${encodeURIComponent(id)}/stream`} aria-label={`Play ${title}`} />
  </figure>;
}
```

### [ApiExceptionHandler.java](starter/backend/src/main/java/com/example/starter/ApiExceptionHandler.java)

**Observed — complete starter source:**

```java
package com.example.starter;

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
    record ApiError(String code, String message, Map<String,String> fieldErrors) {}

    @ExceptionHandler(ApiException.class)
    ResponseEntity<ApiError> domain(ApiException ex) {
        return ResponseEntity.status(ex.status()).body(new ApiError("REQUEST_REJECTED", ex.getMessage(), Map.of()));
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiError> validation(MethodArgumentNotValidException ex) {
        var fields = new LinkedHashMap<String,String>();
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
    ResponseEntity<ApiError> uploadSize(MaxUploadSizeExceededException ex) {
        return ResponseEntity.status(413).body(new ApiError("FILE_TOO_LARGE", "Upload exceeds request limit", Map.of()));
    }
}
```

## Validation and error handling

**Observed:** The included advice maps field validation to 400, missing/domain records to the ApiException's status (including 404), integrity/version/transition conflict to 409, malformed JSON to 400 and upload limits to 413. Security handles 401/403 separately.

**Observed:** `WorkItems.Create` and `NewPoint` provide `@NotBlank`, `@Size`, `@NotNull`, `@Positive` and nested `@Valid`; WorkController applies `@Valid @RequestBody`. The copied office backend has request records in `BackendApp/DTOPack/ApiDtos.java`, DTO-returning controllers and its own global advice. The copied college applies `@Valid` to attendance and records business exceptions as 400/404/409.

**Recommendation:** Keep DTO, database and UI limits consistent; reject invalid requests before writes. Server-side identity determines creator/owner, not a client userId. Use transactions for parent/children and conditional/versioned status decisions.

## Python service and React wiring

**Observed:** Python computes RMS energy from up to 8192 bounded PCM samples and returns an illustrative quiet/energetic label. It is not a trained music classifier. No model weights or training data were supplied, so there is no trained-model accuracy claim.

**Observed:** The React upload UI posts FormData through the shared CSRF-aware Axios client, refreshes metadata and renders AudioPlayer. The analysis action downloads authorized audio, decodes it using AudioContext, sends PCM samples to Spring and renders the returned available/fallback state.

**Recommendation:** Substitute a real model behind the same validated Python contract when the idea requires predictions; version that model and verify its accuracy separately. Add production decode/transcode and larger storage policy when required by the product.

**Recommendation — reproducible service commands:**

```powershell
Set-Location starter/ml-service
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

**Observed:** The requirement pins match the host versions used for recorded Python tests: FastAPI 0.141.1, Uvicorn 0.52.4, HTTPX 0.28.1, pytest 9.1.1, Pydantic 2.13.5. Docker uses Python 3.12; host verification uses Python 3.14. Container execution is a separate ledger item.

## Verification evidence

**Observed:** Starter backend tests passed 9/9 against MySQL 8.4.0, including Flyway V1, authentication/CSRF, role/object scope, atomic points, upload rejection, safe filenames, exact Range bytes and a real HTTP stub for RestClient success/read timeout. Python tests passed 3/3; React/client/auth/player tests passed 6/6. Exact commands and live/browser results are consolidated in REA_EVIDENCE_LEDGER.md.

**Recommendation:** Do not expand these results into an all-codecs, all-browsers, trained-model or production-deployment claim. See the ledger for which native browser and live-service operations actually ran.
