package com.raagify;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayOutputStream;
import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.jdbc.core.JdbcTemplate;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment=SpringBootTest.WebEnvironment.RANDOM_PORT,
    properties={"spring.datasource.url=${DB_URL}","spring.datasource.username=${DB_USER}","spring.datasource.password=${DB_PASSWORD}"})
class ApiIntegrationTest {
    @LocalServerPort int port;
    @Autowired ObjectMapper json;
    @Autowired JdbcTemplate jdbc;
    @Value("${app.bootstrap.admin-email}") String adminEmail;
    @Value("${app.bootstrap.admin-password}") String adminPassword;
    @Value("${spring.datasource.url}") String database;
    final String password="Private-test-password-123";

    class Client {
        final HttpClient http=HttpClient.newBuilder().cookieHandler(new CookieManager(null,CookiePolicy.ACCEPT_ALL)).build();
        HttpResponse<byte[]> request(String method,String path,byte[] body,String type,Map<String,String> headers) throws Exception {
            var builder=HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+"/api"+path));
            if(type!=null)builder.header("Content-Type",type);
            headers.forEach(builder::header);
            return http.send(builder.method(method,body==null?HttpRequest.BodyPublishers.noBody():HttpRequest.BodyPublishers.ofByteArray(body)).build(),HttpResponse.BodyHandlers.ofByteArray());
        }
        HttpResponse<byte[]> get(String path) throws Exception {return request("GET",path,null,null,Map.of());}
        HttpResponse<byte[]> write(String method,String path,byte[] body,String type) throws Exception {
            String token=node(get("/auth/csrf")).get("token").asText();
            return request(method,path,body,type,Map.of("X-XSRF-TOKEN",token));
        }
        HttpResponse<byte[]> write(String method,String path,Object body) throws Exception {return write(method,path,body==null?null:json.writeValueAsBytes(body),"application/json");}
        void login(String email,String pass) throws Exception {
            var response=write("POST","/auth/login",("email="+URLEncoder.encode(email,StandardCharsets.UTF_8)+"&password="+URLEncoder.encode(pass,StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8),"application/x-www-form-urlencoded");
            assertEquals(200,response.statusCode());
        }
    }
    JsonNode node(HttpResponse<byte[]> response) throws Exception {return json.readTree(response.body());}
    Client listener() throws Exception {
        assertTrue(database.contains("/raagify_test"),"Only the isolated test schema is allowed");
        var c=new Client();String email=UUID.randomUUID()+"@raagify.test";
        var response=c.write("POST","/auth/register",Map.of("displayName","Test Listener","email",email,"password",password,"role","ADMIN","userId",99999));
        assertEquals(201,response.statusCode());assertEquals("LISTENER",node(response).get("role").asText());
        assertFalse(node(response).has("passwordHash"));c.login(email,password);return c;
    }
    Client admin() throws Exception {var c=new Client();c.login(adminEmail,adminPassword);return c;}
    long playlist(Client c) throws Exception {return node(c.write("POST","/playlists",Map.of("name",UUID.randomUUID().toString(),"ownerId",99999))).get("id").asLong();}
    byte[] wave() {
        int samples=22050*3;var b=ByteBuffer.allocate(44+samples*2).order(ByteOrder.LITTLE_ENDIAN);
        b.put("RIFF".getBytes(StandardCharsets.US_ASCII)).putInt(36+samples*2).put("WAVEfmt ".getBytes(StandardCharsets.US_ASCII)).putInt(16).putShort((short)1).putShort((short)1).putInt(22050).putInt(44100).putShort((short)2).putShort((short)16).put("data".getBytes(StandardCharsets.US_ASCII)).putInt(samples*2);
        for(int i=0;i<samples;i++)b.putShort((short)(Math.sin(2*Math.PI*440*i/22050)*12000));return b.array();
    }
    HttpResponse<byte[]> upload(Client c,byte[] audio,String type,String genre) throws Exception {
        String boundary="raagify-"+UUID.randomUUID();var out=new ByteArrayOutputStream();
        for(var entry:Map.of("title","Test song "+UUID.randomUUID(),"artist","Test Artist","durationSeconds","3","genre",genre).entrySet())
            out.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+entry.getKey()+"\"\r\n\r\n"+entry.getValue()+"\r\n").getBytes(StandardCharsets.UTF_8));
        out.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"../../test.wav\"\r\nContent-Type: "+type+"\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        out.write(audio);out.write(("\r\n--"+boundary+"--\r\n").getBytes(StandardCharsets.UTF_8));
        return c.write("POST","/admin/songs",out.toByteArray(),"multipart/form-data; boundary="+boundary);
    }
    long song(Client c) throws Exception {var r=upload(c,wave(),"audio/wav","TestGenre");assertEquals(201,r.statusCode());return node(r).get("id").asLong();}

    @Test void authenticationCsrfForcedRoleAndLogout() throws Exception {
        var anonymous=new Client();assertEquals(401,anonymous.get("/songs").statusCode());
        assertEquals(403,anonymous.request("POST","/auth/register","{}".getBytes(),"application/json",Map.of()).statusCode());
        var c=listener();assertEquals("LISTENER",node(c.get("/auth/me")).get("role").asText());
        assertEquals(401,c.write("POST","/auth/login","email=wrong&password=wrong".getBytes(),"application/x-www-form-urlencoded").statusCode());
        assertEquals(200,c.write("POST","/auth/logout",null).statusCode());assertEquals(401,c.get("/auth/me").statusCode());
    }
    @Test void roleDenialAndStableValidation() throws Exception {
        var c=listener();assertEquals(403,upload(c,wave(),"audio/wav","").statusCode());
        assertEquals(403,c.write("PUT","/admin/songs/1",Map.of()).statusCode());
        var invalid=c.write("POST","/playlists",Map.of("name"," "));
        assertEquals(400,invalid.statusCode());assertTrue(node(invalid).get("fieldErrors").has("name"));
        assertEquals(400,c.get("/songs?page=-1").statusCode());assertEquals(400,c.get("/songs?page=wrong").statusCode());
        assertEquals(404,c.get("/songs/9223372036854775807").statusCode());
    }
    @Test void playlistCrudOwnershipDuplicatesAndReorder() throws Exception {
        var a=listener();var b=listener();var admin=admin();long p=playlist(a),s1=song(admin),s2=song(admin);
        assertEquals(403,b.get("/playlists/"+p).statusCode());
        assertEquals(403,b.write("DELETE","/playlists/"+p,null).statusCode());
        assertEquals(403,b.write("POST","/playlists/"+p+"/songs/"+s1,null).statusCode());
        assertEquals(201,a.write("POST","/playlists/"+p+"/songs/"+s1,null).statusCode());
        assertEquals(409,a.write("POST","/playlists/"+p+"/songs/"+s1,null).statusCode());
        assertEquals(201,a.write("POST","/playlists/"+p+"/songs/"+s2,null).statusCode());
        var reordered=a.write("PUT","/playlists/"+p+"/songs/order",Map.of("songIds",new long[]{s2,s1}));
        assertEquals(200,reordered.statusCode());assertEquals(s2,node(reordered).get("songs").get(0).get("id").asLong());
        assertEquals(400,a.write("PUT","/playlists/"+p+"/songs/order",Map.of("songIds",new long[]{s1,s1})).statusCode());
        assertEquals(200,a.write("PUT","/playlists/"+p,Map.of("name","Renamed "+UUID.randomUUID())).statusCode());
        assertEquals(200,a.write("DELETE","/playlists/"+p+"/songs/"+s2,null).statusCode());
        assertEquals(204,a.write("DELETE","/playlists/"+p,null).statusCode());assertEquals(404,a.get("/playlists/"+p).statusCode());
    }
    @Test void likesHistoryAndRecommendationsUseSessionIdentity() throws Exception {
        var a=listener();var b=listener();var admin=admin();long s=song(admin),other=song(admin);
        assertEquals(201,a.write("POST","/likes/"+s,Map.of("userId",node(b.get("/auth/me")).get("id").asLong())).statusCode());
        assertEquals(409,a.write("POST","/likes/"+s,null).statusCode());assertEquals(0,node(b.get("/likes")).size());
        assertEquals(404,b.write("DELETE","/likes/"+s,null).statusCode());
        assertEquals(204,a.write("POST","/songs/"+other+"/plays",Map.of("userId",999999)).statusCode());
        assertEquals(0,node(b.get("/history/recent")).size());assertTrue(node(a.get("/history/recent")).size()>0);
        for(var result:node(a.get("/recommendations")))assertNotEquals(s,result.get("id").asLong());
        assertEquals(204,a.write("DELETE","/likes/"+s,null).statusCode());
    }
    @Test void uploadRealFeaturesRangeAndSearch() throws Exception {
        var admin=admin();var response=upload(admin,wave(),"audio/wav","");assertEquals(201,response.statusCode());
        var metadata=node(response);long id=metadata.get("id").asLong();assertEquals("READY",metadata.get("featureStatus").asText());
        assertEquals("UNCLASSIFIED",metadata.get("genreSource").asText());assertFalse(metadata.has("genreConfidence"));assertFalse(metadata.has("audioStorageName"));
        String stored=jdbc.queryForObject("SELECT audio_storage_name FROM songs WHERE id=?",String.class,id);assertTrue(stored.matches("[a-f0-9-]{36}\\.wav"));
        var c=listener();byte[] wav=wave();
        for(String range:new String[]{"bytes=0-31","bytes=-16","bytes=32-"}){
            var r=c.request("GET","/songs/"+id+"/stream",null,null,Map.of("Range",range));assertEquals(206,r.statusCode());assertEquals("bytes",r.headers().firstValue("Accept-Ranges").orElseThrow());
            int start=range.equals("bytes=0-31")?0:range.equals("bytes=-16")?wav.length-16:32;int end=range.equals("bytes=0-31")?32:wav.length;
            assertArrayEquals(java.util.Arrays.copyOfRange(wav,start,end),r.body());
        }
        assertEquals(416,c.request("GET","/songs/"+id+"/stream",null,null,Map.of("Range","bytes=999999999-")).statusCode());
        assertEquals(416,c.request("GET","/songs/"+id+"/stream",null,null,Map.of("Range","bytes=0-1,3-4")).statusCode());
        assertEquals(200,c.request("HEAD","/songs/"+id+"/stream",null,null,Map.of()).statusCode());
        var results=node(c.get("/songs?q=Test%20Artist&size=2"));assertTrue(results.get("totalElements").asLong()>0);assertTrue(results.get("content").size()<=2);
        for(var result:node(c.get("/songs/"+id+"/similar")))assertNotEquals(id,result.get("id").asLong());
    }
    @Test void rejectFalseAudioSignatureAndDeleteCascades() throws Exception {
        var admin=admin();assertEquals(400,upload(admin,"not audio".getBytes(),"audio/wav","").statusCode());
        assertEquals(400,upload(admin,wave(),"text/plain","").statusCode());
        long s=song(admin);var c=listener();long p=playlist(c);c.write("POST","/likes/"+s,null);c.write("POST","/playlists/"+p+"/songs/"+s,null);c.write("POST","/songs/"+s+"/plays",null);
        assertEquals(200,admin.write("PUT","/admin/songs/"+s,Map.of("title","Edited","artist","Artist","album","Album","genre","Jazz","durationSeconds",3)).statusCode());
        assertEquals(204,admin.write("DELETE","/admin/songs/"+s,null).statusCode());assertEquals(404,c.get("/songs/"+s).statusCode());
        assertEquals(0,node(c.get("/likes")).size());assertEquals(0,node(c.get("/playlists/"+p)).get("songs").size());assertEquals(0,node(c.get("/history/recent")).size());
    }
    @Test void concurrentDistinctPlaylistAddsDoNotCollideOnPosition() throws Exception {
        var c=listener();var admin=admin();long p=playlist(c),s1=song(admin),s2=song(admin);
        var a=CompletableFuture.supplyAsync(()->{try{return c.write("POST","/playlists/"+p+"/songs/"+s1,null).statusCode();}catch(Exception e){throw new RuntimeException(e);}});
        var b=CompletableFuture.supplyAsync(()->{try{return c.write("POST","/playlists/"+p+"/songs/"+s2,null).statusCode();}catch(Exception e){throw new RuntimeException(e);}});
        assertEquals(201,a.get());assertEquals(201,b.get());assertEquals(2,node(c.get("/playlists/"+p)).get("songs").size());
    }
    @Test void analyticsUsesPersistedDataAndIsAdminOnly() throws Exception {
        var a=admin();var c=listener();assertEquals(403,c.get("/admin/analytics").statusCode());assertEquals(400,a.get("/admin/analytics?days=2").statusCode());
        var before=node(a.get("/admin/analytics?days=7"));long s=song(a);long p=playlist(c);c.write("POST","/likes/"+s,null);c.write("POST","/songs/"+s+"/plays",null);c.write("POST","/songs/"+s+"/plays",null);
        var after=node(a.get("/admin/analytics?days=7"));assertTrue(after.get("totals").get("songs").asLong()>=before.get("totals").get("songs").asLong()+1);assertTrue(after.get("period").get("plays").asLong()>=before.get("period").get("plays").asLong()+2);
        assertEquals(7,after.get("dailyPlays").size());long sum=0;for(var day:after.get("dailyPlays"))sum+=day.get("plays").asLong();assertEquals(after.get("period").get("plays").asLong(),sum);
        assertEquals("UTC",after.get("timezone").asText());assertEquals("UP",after.get("processor").get("status").asText());assertFalse(after.toString().contains("password"));
    }
}
