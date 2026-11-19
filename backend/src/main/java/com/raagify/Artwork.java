package com.raagify;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

@Service
public class Artwork {
    private final JdbcTemplate jdbc;
    private final MediaClient media;
    private final Accounts accounts;
    private final Path root;
    private final long maxBytes;
    public Artwork(JdbcTemplate jdbc, MediaClient media, Accounts accounts,
        @Value("${app.storage.cover-path}") String directory, @Value("${app.storage.cover-max-bytes}") long maxBytes) throws IOException {
        this.jdbc=jdbc;this.media=media;this.accounts=accounts;this.root=Path.of(directory).toAbsolutePath().normalize();this.maxBytes=maxBytes;Files.createDirectories(root);
    }
    @Transactional
    public boolean restore(long id, Path audio) {
        if (!accounts.current().role().equals("ADMIN")) throw new ApiException(403,"Admin access required");
        if (jdbc.queryForObject("SELECT COUNT(*) FROM songs WHERE id=? AND cover_storage_name IS NULL",Integer.class,id)==0) return false;
        var result=media.artwork(audio);
        if(result==null || result.coverBase64()==null || result.coverContentType()==null || result.coverBase64().length()>(maxBytes+2)*4/3+4)return false;
        byte[] bytes;
        try {bytes=Base64.getDecoder().decode(result.coverBase64());}catch(IllegalArgumentException ex){return false;}
        if(bytes.length==0 || bytes.length>maxBytes)return false;
        String extension=switch(result.coverContentType()){case "image/png" -> "png";case "image/jpeg" -> "jpg";case "image/webp" -> "webp";default -> null;};
        if(extension==null || !signature(result.coverContentType(),bytes))return false;
        String name=UUID.randomUUID()+"."+extension;
        Path path=root.resolve(name).normalize();
        try {
            Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
            if(jdbc.update("UPDATE songs SET cover_storage_name=?,cover_content_type=? WHERE id=? AND cover_storage_name IS NULL",name,result.coverContentType(),id)==0){Files.deleteIfExists(path);return false;}
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization(){
                @Override public void afterCompletion(int status){if(status!=STATUS_COMMITTED)remove(path);}
            });
            return true;
        }catch(IOException|RuntimeException ex){remove(path);throw new ApiException(500,"Artwork could not be stored");}
    }
    private static boolean signature(String type,byte[] bytes){
        if(type.equals("image/png"))return bytes.length>=8&&java.util.Arrays.equals(java.util.Arrays.copyOf(bytes,8),new byte[]{(byte)137,80,78,71,13,10,26,10});
        if(type.equals("image/jpeg"))return bytes.length>=3&&(bytes[0]&255)==255&&(bytes[1]&255)==216&&(bytes[2]&255)==255;
        return bytes.length>=12&&new String(bytes,0,4,java.nio.charset.StandardCharsets.US_ASCII).equals("RIFF")&&new String(bytes,8,4,java.nio.charset.StandardCharsets.US_ASCII).equals("WEBP");
    }
    private static void remove(Path path){try{Files.deleteIfExists(path);}catch(IOException ex){org.slf4j.LoggerFactory.getLogger(Artwork.class).warn("Artwork cleanup failed",ex);}}
}
