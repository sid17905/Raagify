package com.raagify;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
public class Songs {
    public record SongDto(long id, String title, String artist, String album, String genre,
                          int durationSeconds, String streamUrl, String coverUrl,
                          String featureStatus, String genreSource, long playCount,
                          boolean liked, Instant createdAt) {}
    public record PageDto(List<SongDto> content, int page, int size, long totalElements, int totalPages) {}
    public record Update(@NotBlank @Size(max=160) String title,
                         @NotBlank @Size(max=160) String artist,
                         @Size(max=160) String album,
                         @Size(max=80) String genre,
                         @NotNull @Min(1) @Max(86400) Integer durationSeconds) {}
    public static class Upload {
        @NotBlank @Size(max=160) private String title;
        @NotBlank @Size(max=160) private String artist;
        @Size(max=160) private String album;
        @Size(max=80) private String genre;
        @NotNull @Min(1) @Max(86400) private Integer durationSeconds;
        @NotNull private MultipartFile audio;
        private MultipartFile cover;
        public String getTitle(){return title;} public void setTitle(String v){title=v;}
        public String getArtist(){return artist;} public void setArtist(String v){artist=v;}
        public String getAlbum(){return album;} public void setAlbum(String v){album=v;}
        public String getGenre(){return genre;} public void setGenre(String v){genre=v;}
        public Integer getDurationSeconds(){return durationSeconds;} public void setDurationSeconds(Integer v){durationSeconds=v;}
        public MultipartFile getAudio(){return audio;} public void setAudio(MultipartFile v){audio=v;}
        public MultipartFile getCover(){return cover;} public void setCover(MultipartFile v){cover=v;}
    }
    public record Stored(Path path, String contentType, long size) {}
    private static final Map<String,String> AUDIO_TYPES = Map.of(
        "audio/wav","wav", "audio/x-wav","wav", "audio/mpeg","mp3", "audio/ogg","ogg");
    private static final Map<String,String> COVER_TYPES = Map.of(
        "image/jpeg","jpg", "image/png","png", "image/webp","webp");
    private final JdbcTemplate jdbc;
    private final Accounts accounts;
    private final MlClient ml;
    private final ObjectMapper json;
    private final Path audioRoot;
    private final Path coverRoot;
    private final long audioMax;
    private final long coverMax;

    public Songs(JdbcTemplate jdbc, Accounts accounts, MlClient ml, ObjectMapper json,
                 @Value("${app.storage.audio-path}") String audioPath,
                 @Value("${app.storage.cover-path}") String coverPath,
                 @Value("${app.storage.audio-max-bytes}") long audioMax,
                 @Value("${app.storage.cover-max-bytes}") long coverMax) throws IOException {
        this.jdbc=jdbc; this.accounts=accounts; this.ml=ml; this.json=json;
        this.audioRoot=Path.of(audioPath).toAbsolutePath().normalize();
        this.coverRoot=Path.of(coverPath).toAbsolutePath().normalize();
        this.audioMax=audioMax; this.coverMax=coverMax;
        Files.createDirectories(audioRoot); Files.createDirectories(coverRoot);
    }

    public PageDto search(String query, int page, int size) {
        var actor=accounts.current();
        if(page<0) throw new ApiException(400,"Page must not be negative");
        if(size<1 || size>50) throw new ApiException(400,"Size must be between 1 and 50");
        if (query != null && query.length() > 200) throw new ApiException(400, "Search must be at most 200 characters");
        String q=query==null?"":query.trim().toLowerCase(Locale.ROOT), like="%"+q+"%";
        String where=" WHERE LOWER(s.title) LIKE ? OR LOWER(s.artist) LIKE ? OR LOWER(COALESCE(s.genre,'')) LIKE ? ";
        Long total=jdbc.queryForObject("SELECT COUNT(*) FROM songs s"+where,Long.class,like,like,like);
        var rows=jdbc.query("SELECT s.*, EXISTS(SELECT 1 FROM liked_songs l WHERE l.user_id=? AND l.song_id=s.id) liked FROM songs s"+where+" ORDER BY s.created_at DESC,s.id DESC LIMIT ? OFFSET ?",
            this::mapSong,actor.id(),like,like,like,size,(long)page*size);
        long count=total==null?0:total;
        return new PageDto(rows,page,size,count,(int)Math.ceil(count/(double)size));
    }

    public SongDto get(long id) {
        var actor=accounts.current();
        return jdbc.query("SELECT s.*, EXISTS(SELECT 1 FROM liked_songs l WHERE l.user_id=? AND l.song_id=s.id) liked FROM songs s WHERE s.id=?",
            this::mapSong,actor.id(),id).stream().findFirst().orElseThrow(()->new ApiException(404,"Song not found"));
    }

    @Transactional
    public SongDto upload(Upload request) throws IOException {
        var actor=accounts.current();
        if(!actor.role().equals("ADMIN")) throw new ApiException(403,"Admin access required");
        MultipartFile audio=request.getAudio(), cover=request.getCover();
        validate(audio,AUDIO_TYPES,audioMax,true);
        if(cover!=null && !cover.isEmpty()) validate(cover,COVER_TYPES,coverMax,false);
        String audioName=UUID.randomUUID()+"."+AUDIO_TYPES.get(audio.getContentType());
        String coverName=cover==null||cover.isEmpty()?null:UUID.randomUUID()+"."+COVER_TYPES.get(cover.getContentType());
        Path audioFile=resolve(audioRoot,audioName), coverFile=coverName==null?null:resolve(coverRoot,coverName);
        try {
            copy(audio,audioFile,audioMax);
            if(coverFile!=null) copy(cover,coverFile,coverMax);
            org.springframework.transaction.support.TransactionSynchronizationManager.registerSynchronization(
                new org.springframework.transaction.support.TransactionSynchronization() {
                    @Override public void afterCompletion(int status) {
                        if (status != STATUS_COMMITTED) { removeFile(audioFile); if (coverFile != null) removeFile(coverFile); }
                    }
                });
            MlClient.Analysis analysis=ml.analyze(audioFile);
            boolean ready=analysis.available() && analysis.vector()!=null && !analysis.vector().isEmpty();
            String supplied=clean(request.getGenre());
            String genre=supplied!=null?supplied:(ready?clean(analysis.predictedGenre()):null);
            String genreSource=supplied!=null?"ADMIN_OVERRIDE":(ready?analysis.genreSource():"PENDING");
            String vector=ready?json.writeValueAsString(analysis.vector()):null;
            jdbc.update("INSERT INTO songs(title,artist,album_name,genre,duration_seconds,audio_storage_name,audio_content_type,audio_size_bytes,cover_storage_name,cover_content_type,feature_vector,feature_status,genre_source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                request.getTitle().trim(),request.getArtist().trim(),clean(request.getAlbum()),genre,request.getDurationSeconds(),audioName,audio.getContentType(),Files.size(audioFile),coverName,coverName==null?null:cover.getContentType(),vector,ready?"READY":"PENDING",genreSource);
            Long id=jdbc.queryForObject("SELECT LAST_INSERT_ID()",Long.class);
            return get(id);
        } catch(IOException|RuntimeException error) {
            Files.deleteIfExists(audioFile); if(coverFile!=null) Files.deleteIfExists(coverFile); throw error;
        }
    }

    @Transactional
    public SongDto update(long id, Update request) {
        requireAdmin(); requireSong(id);
        int changed=jdbc.update("UPDATE songs SET title=?,artist=?,album_name=?,genre=?,duration_seconds=?,genre_source=CASE WHEN ? IS NOT NULL THEN 'ADMIN_OVERRIDE' ELSE genre_source END WHERE id=?",
            request.title().trim(),request.artist().trim(),clean(request.album()),clean(request.genre()),request.durationSeconds(),clean(request.genre()),id);
        if(changed==0) throw new ApiException(404,"Song not found");
        return get(id);
    }

    @Transactional
    public void delete(long id) throws IOException {
        requireAdmin();
        var files=jdbc.query("SELECT audio_storage_name,cover_storage_name FROM songs WHERE id=?",
            (rs,row)->List.of(rs.getString("audio_storage_name"),rs.getString("cover_storage_name") == null ? "" : rs.getString("cover_storage_name")),id);
        if(files.isEmpty()) throw new ApiException(404,"Song not found");
        jdbc.update("DELETE FROM songs WHERE id=?",id);
        Path audioFile = resolve(audioRoot,files.getFirst().get(0));
        Path coverFile = files.getFirst().get(1).isBlank() ? null : resolve(coverRoot,files.getFirst().get(1));
        org.springframework.transaction.support.TransactionSynchronizationManager.registerSynchronization(
            new org.springframework.transaction.support.TransactionSynchronization() {
                @Override public void afterCommit() { removeFile(audioFile); if (coverFile != null) removeFile(coverFile); }
            });
    }

    public Stored audio(long id) { return stored(id,true); }
    public Stored cover(long id) { return stored(id,false); }

    @Transactional
    public SongDto retryFeatures(long id) {
        requireAdmin(); SongDto song = get(id);
        var result = ml.analyze(audio(id).path());
        if (result.available()) {
            try {
                jdbc.update("UPDATE songs SET feature_vector=?,feature_status='READY',genre=CASE WHEN genre_source='ADMIN_OVERRIDE' THEN genre ELSE ? END,genre_source=CASE WHEN genre_source='ADMIN_OVERRIDE' THEN genre_source ELSE ? END WHERE id=?",
                    json.writeValueAsString(result.vector()),result.predictedGenre(),result.genreSource(),id);
            } catch (JsonProcessingException ex) { throw new ApiException(400,"Invalid feature response"); }
        }
        return get(id);
    }

    public List<Double> vector(long id) {
        var rows=jdbc.query("SELECT feature_vector FROM songs WHERE id=? AND feature_status='READY'",
            (rs,row)->rs.getString(1),id);
        if(rows.isEmpty() || rows.getFirst()==null) return List.of();
        try { return json.readValue(rows.getFirst(),new TypeReference<>(){}); }
        catch(JsonProcessingException error) { return List.of(); }
    }

    private Stored stored(long id, boolean audio) {
        accounts.current(); String rootName=audio?"audio_storage_name":"cover_storage_name";
        String typeName=audio?"audio_content_type":"cover_content_type";
        var rows=jdbc.query("SELECT "+rootName+","+typeName+(audio?",audio_size_bytes":"")+" FROM songs WHERE id=?",
            (rs,row)-> { String name=rs.getString(rootName); if(name==null) return null;
                Path path=resolve(audio?audioRoot:coverRoot,name);
                try { return new Stored(path,rs.getString(typeName),audio?rs.getLong("audio_size_bytes"):Files.size(path)); }
                catch(IOException e){throw new ApiException(404,"File not found");}},id);
        if(rows.isEmpty() || rows.getFirst()==null || !Files.isRegularFile(rows.getFirst().path())) throw new ApiException(404,audio?"Audio not found":"Cover not found");
        return rows.getFirst();
    }

    private SongDto mapSong(ResultSet rs,int row) throws SQLException {
        long id=rs.getLong("id");
        return new SongDto(id,rs.getString("title"),rs.getString("artist"),rs.getString("album_name"),rs.getString("genre"),
            rs.getInt("duration_seconds"),"/api/songs/"+id+"/stream",
            rs.getString("cover_storage_name")==null?null:"/api/songs/"+id+"/cover",
            rs.getString("feature_status"),rs.getString("genre_source"),rs.getLong("play_count"),rs.getBoolean("liked"),
            rs.getTimestamp("created_at").toInstant());
    }
    private void requireSong(long id) { if(jdbc.queryForObject("SELECT COUNT(*) FROM songs WHERE id=?",Integer.class,id)==0) throw new ApiException(404,"Song not found"); }
    private static String clean(String value){return value==null||value.isBlank()?null:value.trim();}
    private static Path resolve(Path root,String name){Path p=root.resolve(name).normalize();if(!p.startsWith(root))throw new ApiException(400,"Invalid storage path");return p;}
    private static void copy(MultipartFile file,Path target,long max) throws IOException {try(var in=file.getInputStream()){Files.copy(in,target,StandardCopyOption.REPLACE_EXISTING);}if(Files.size(target)>max){Files.deleteIfExists(target);throw new ApiException(413,"File exceeds configured size limit");}}
    private static void validate(MultipartFile file,Map<String,String> allowed,long max,boolean audio) throws IOException {
        if(file==null||file.isEmpty())throw new ApiException(400,(audio?"Audio":"Cover")+" file is required");
        if(file.getSize()>max)throw new ApiException(413,(audio?"Audio":"Cover")+" exceeds configured size limit");
        String type=file.getContentType();if(type==null||!allowed.containsKey(type))throw new ApiException(400,"Unsupported "+(audio?"audio":"cover")+" type");
        byte[] b;try(var in=file.getInputStream()){b=in.readNBytes(16);}
        boolean ok;
        if(type.equals("audio/wav")||type.equals("audio/x-wav"))ok=b.length>=12&&ascii(b,0,4).equals("RIFF")&&ascii(b,8,4).equals("WAVE");
        else if(type.equals("audio/ogg"))ok=b.length>=4&&ascii(b,0,4).equals("OggS");
        else if(type.equals("audio/mpeg"))ok=b.length>=3&&(ascii(b,0,3).equals("ID3")||((b[0]&255)==255&&(b[1]&224)==224));
        else if(type.equals("image/png"))ok=b.length>=8&&java.util.Arrays.equals(java.util.Arrays.copyOf(b,8),new byte[]{(byte)137,80,78,71,13,10,26,10});
        else if(type.equals("image/jpeg"))ok=b.length>=3&&(b[0]&255)==255&&(b[1]&255)==216&&(b[2]&255)==255;
        else ok=b.length>=12&&ascii(b,0,4).equals("RIFF")&&ascii(b,8,4).equals("WEBP");
        if(!ok)throw new ApiException(400,"Content does not match the claimed file type");
    }
    private static String ascii(byte[] bytes,int offset,int size){return new String(bytes,offset,size,StandardCharsets.US_ASCII);}
    private void requireAdmin() { if (!accounts.current().role().equals("ADMIN")) throw new ApiException(403,"Admin access required"); }
    private static void removeFile(Path path) {
        try { Files.deleteIfExists(path); }
        catch (IOException ex) { org.slf4j.LoggerFactory.getLogger(Songs.class).warn("Stored file cleanup failed", ex); }
    }
}
