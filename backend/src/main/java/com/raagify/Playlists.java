package com.raagify;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.util.HashSet;
import java.util.List;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Service
public class Playlists {
    public record Name(@NotBlank @Size(max=120) String name) {}
    public record Reorder(@NotNull @Size(max=500) List<@NotNull @Positive Long> songIds) {}
    public record PlaylistDto(long id,String name,List<Songs.SongDto> songs) {}
    private final JdbcTemplate jdbc; private final Accounts accounts; private final Songs songs;
    public Playlists(JdbcTemplate jdbc,Accounts accounts,Songs songs){this.jdbc=jdbc;this.accounts=accounts;this.songs=songs;}
    public List<PlaylistDto> list(){var actor=accounts.current();return jdbc.query("SELECT id FROM playlists WHERE owner_id=? ORDER BY updated_at DESC,id DESC",(rs,row)->rs.getLong(1),actor.id()).stream().map(this::get).toList();}
    public PlaylistDto get(long id){owned(id);String name=jdbc.queryForObject("SELECT name FROM playlists WHERE id=?",String.class,id);var tracks=jdbc.query("SELECT song_id FROM playlist_songs WHERE playlist_id=? ORDER BY position_no",(rs,row)->rs.getLong(1),id).stream().map(songs::get).toList();return new PlaylistDto(id,name,tracks);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public PlaylistDto create(Name request){var actor=accounts.current();try{jdbc.update("INSERT INTO playlists(owner_id,name) VALUES(?,?)",actor.id(),request.name().trim());}catch(DuplicateKeyException e){throw new ApiException(409,"A playlist with that name already exists");}Long id=jdbc.queryForObject("SELECT LAST_INSERT_ID()",Long.class);return get(id);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public PlaylistDto rename(long id,Name request){owned(id);try{jdbc.update("UPDATE playlists SET name=? WHERE id=?",request.name().trim(),id);}catch(DuplicateKeyException e){throw new ApiException(409,"A playlist with that name already exists");}return get(id);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public void delete(long id){owned(id);jdbc.update("DELETE FROM playlists WHERE id=?",id);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public PlaylistDto add(long id,long songId){owned(id);songs.get(songId);Integer count=jdbc.queryForObject("SELECT COUNT(*) FROM playlist_songs WHERE playlist_id=?",Integer.class,id);if(count>=500)throw new ApiException(400,"A playlist can contain at most 500 songs");Integer pos=jdbc.queryForObject("SELECT COALESCE(MAX(position_no),-1)+1 FROM playlist_songs WHERE playlist_id=?",Integer.class,id);try{jdbc.update("INSERT INTO playlist_songs(playlist_id,song_id,position_no) VALUES(?,?,?)",id,songId,pos);}catch(DuplicateKeyException e){throw new ApiException(409,"Song is already in this playlist");}return get(id);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public PlaylistDto remove(long id,long songId){owned(id);if(jdbc.update("DELETE FROM playlist_songs WHERE playlist_id=? AND song_id=?",id,songId)==0)throw new ApiException(404,"Playlist entry not found");compact(id);return get(id);}
    @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) public PlaylistDto reorder(long id,Reorder request){owned(id);if(new HashSet<>(request.songIds()).size()!=request.songIds().size())throw new ApiException(400,"Reorder list contains duplicate song IDs");var existing=jdbc.query("SELECT song_id FROM playlist_songs WHERE playlist_id=?",(rs,row)->rs.getLong(1),id);if(existing.size()!=request.songIds().size()||!new HashSet<>(existing).equals(new HashSet<>(request.songIds())))throw new ApiException(400,"Reorder must contain every playlist song exactly once");jdbc.update("DELETE FROM playlist_songs WHERE playlist_id=?",id);for(int i=0;i<request.songIds().size();i++)jdbc.update("INSERT INTO playlist_songs(playlist_id,song_id,position_no) VALUES(?,?,?)",id,request.songIds().get(i),i);return get(id);}
    private void compact(long id){var ids=jdbc.query("SELECT song_id FROM playlist_songs WHERE playlist_id=? ORDER BY position_no",(rs,row)->rs.getLong(1),id);jdbc.update("DELETE FROM playlist_songs WHERE playlist_id=?",id);for(int i=0;i<ids.size();i++)jdbc.update("INSERT INTO playlist_songs(playlist_id,song_id,position_no) VALUES(?,?,?)",id,ids.get(i),i);}
    private void owned(long id){var actor=accounts.current();var owners=jdbc.query("SELECT owner_id FROM playlists WHERE id=?"+(org.springframework.transaction.support.TransactionSynchronizationManager.isActualTransactionActive()?" FOR UPDATE":""),(rs,row)->rs.getLong(1),id);if(owners.isEmpty())throw new ApiException(404,"Playlist not found");if(owners.getFirst()!=actor.id())throw new ApiException(403,"Playlist belongs to another user");}
}

@RestController
@RequestMapping("/api/playlists")
class PlaylistController {
    private final Playlists playlists; PlaylistController(Playlists playlists){this.playlists=playlists;}
    @GetMapping List<Playlists.PlaylistDto> list(){return playlists.list();}
    @GetMapping("/{id}") Playlists.PlaylistDto get(@PathVariable long id){return playlists.get(id);}
    @PostMapping ResponseEntity<Playlists.PlaylistDto> create(@jakarta.validation.Valid @RequestBody Playlists.Name request){return ResponseEntity.status(201).body(playlists.create(request));}
    @PutMapping("/{id}") Playlists.PlaylistDto rename(@PathVariable long id,@jakarta.validation.Valid @RequestBody Playlists.Name request){return playlists.rename(id,request);}
    @DeleteMapping("/{id}") ResponseEntity<Void> delete(@PathVariable long id){playlists.delete(id);return ResponseEntity.noContent().build();}
    @PostMapping("/{id}/songs/{songId}") ResponseEntity<Playlists.PlaylistDto> add(@PathVariable long id,@PathVariable long songId){return ResponseEntity.status(201).body(playlists.add(id,songId));}
    @DeleteMapping("/{id}/songs/{songId}") Playlists.PlaylistDto remove(@PathVariable long id,@PathVariable long songId){return playlists.remove(id,songId);}
    @PutMapping("/{id}/songs/order") Playlists.PlaylistDto reorder(@PathVariable long id,@jakarta.validation.Valid @RequestBody Playlists.Reorder request){return playlists.reorder(id,request);}
}
