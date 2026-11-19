package com.raagify;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.StandardOpenOption;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/songs")
public class SongController {
    private final Songs songs;
    private final Listening listening;
    private final Recommendations recommendations;
    public SongController(Songs songs, Listening listening, Recommendations recommendations) {
        this.songs=songs; this.listening=listening; this.recommendations=recommendations;
    }
    @GetMapping Songs.PageDto browse(@RequestParam(defaultValue="") String q,
                                     @RequestParam(defaultValue="0") int page,
                                     @RequestParam(defaultValue="20") int size) { return songs.search(q,page,size); }
    @GetMapping("/{id}") Songs.SongDto one(@PathVariable long id) { return songs.get(id); }
    @GetMapping("/{id}/similar") java.util.List<Songs.SongDto> similar(@PathVariable long id) { return recommendations.similar(id); }
    @PostMapping("/{id}/plays") ResponseEntity<Void> played(@PathVariable long id) { listening.record(id); return ResponseEntity.noContent().build(); }
    @RequestMapping(value="/{id}/stream", method={RequestMethod.GET,RequestMethod.HEAD})
    void stream(@PathVariable long id, HttpServletRequest request, HttpServletResponse response) throws IOException {
        Songs.Stored stored=songs.audio(id); long total=stored.size();
        response.setHeader("Accept-Ranges","bytes"); response.setContentType(stored.contentType());
        response.setHeader("Cache-Control","private, no-cache"); response.setHeader("X-Content-Type-Options","nosniff");
        Range range;
        try { range=Range.parse(request.getHeader("Range"),total); }
        catch(IllegalArgumentException error){response.setStatus(416);response.setHeader("Content-Range","bytes */"+total);return;}
        if(request.getHeader("Range")!=null){response.setStatus(206);response.setHeader("Content-Range","bytes "+range.start()+"-"+range.end()+"/"+total);}
        response.setContentLengthLong(range.length()); if(request.getMethod().equals("HEAD")) return;
        try(var channel=FileChannel.open(stored.path(),StandardOpenOption.READ)){
            channel.position(range.start()); long remaining=range.length(); var buffer=ByteBuffer.allocate(16*1024); var out=response.getOutputStream();
            while(remaining>0){buffer.clear();buffer.limit((int)Math.min(buffer.capacity(),remaining));int read=channel.read(buffer);if(read<0)break;out.write(buffer.array(),0,read);remaining-=read;}
        }
    }
    @GetMapping("/{id}/cover") void cover(@PathVariable long id,HttpServletResponse response) throws IOException {
        Songs.Stored stored=songs.cover(id); response.setContentType(stored.contentType());response.setContentLengthLong(stored.size());
        response.setHeader("Cache-Control","private, max-age=3600");response.setHeader("X-Content-Type-Options","nosniff");
        java.nio.file.Files.copy(stored.path(),response.getOutputStream());
    }
    record Range(long start,long end){
        long length(){return end-start+1;}
        static Range parse(String header,long total){
            if(total<=0)throw new IllegalArgumentException(); if(header==null)return new Range(0,total-1);
            if(!header.matches("bytes=\\d*-\\d*"))throw new IllegalArgumentException();String[] p=header.substring(6).split("-",-1);
            try{if(p[0].isEmpty()){if(p[1].isEmpty())throw new IllegalArgumentException();long suffix=Long.parseLong(p[1]);if(suffix<=0)throw new IllegalArgumentException();return new Range(Math.max(0,total-suffix),total-1);}
                long start=Long.parseLong(p[0]),end=p[1].isEmpty()?total-1:Long.parseLong(p[1]);if(start>=total||end<start)throw new IllegalArgumentException();return new Range(start,Math.min(end,total-1));
            }catch(NumberFormatException error){throw new IllegalArgumentException(error);}
        }
    }
}

@RestController
@RequestMapping("/api/admin/songs")
class AdminSongController {
    private final Songs songs;
    AdminSongController(Songs songs){this.songs=songs;}
    @PostMapping(consumes="multipart/form-data") ResponseEntity<Songs.SongDto> upload(@Valid @ModelAttribute Songs.Upload request) throws IOException {
        return ResponseEntity.status(201).body(songs.upload(request));
    }
    @PutMapping("/{id}") Songs.SongDto update(@PathVariable long id,@Valid @RequestBody Songs.Update request){return songs.update(id,request);}
    @DeleteMapping("/{id}") ResponseEntity<Void> delete(@PathVariable long id) throws IOException {songs.delete(id);return ResponseEntity.noContent().build();}
    @PostMapping("/{id}/features/retry") Songs.SongDto retry(@PathVariable long id) { return songs.retryFeatures(id); }
    @PostMapping("/{id}/artwork/restore") Songs.SongDto restoreArtwork(@PathVariable long id){return songs.restoreArtwork(id);}
    @PostMapping("/artwork/restore") Songs.ArtworkSummary restoreAll(){return songs.restoreAllArtwork();}
    @PostMapping(value="/metadata",consumes="multipart/form-data") MediaClient.Metadata metadata(@RequestParam("file") MultipartFile file) throws IOException{return songs.previewMetadata(file);}
    @PostMapping("/{id}/metadata/refresh") Songs.SongDto refreshMetadata(@PathVariable long id){return songs.refreshMetadata(id);}
}
