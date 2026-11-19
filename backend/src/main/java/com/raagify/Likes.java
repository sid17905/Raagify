package com.raagify;

import java.util.List;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Service
public class Likes {
    private final JdbcTemplate jdbc; private final Accounts accounts; private final Songs songs;
    public Likes(JdbcTemplate jdbc,Accounts accounts,Songs songs){this.jdbc=jdbc;this.accounts=accounts;this.songs=songs;}
    public List<Songs.SongDto> list(){var actor=accounts.current();return jdbc.query("SELECT song_id FROM liked_songs WHERE user_id=? ORDER BY liked_at DESC",(rs,row)->rs.getLong(1),actor.id()).stream().map(songs::get).toList();}
    @Transactional public Songs.SongDto like(long songId){var actor=accounts.current();songs.get(songId);try{jdbc.update("INSERT INTO liked_songs(user_id,song_id) VALUES(?,?)",actor.id(),songId);}catch(DuplicateKeyException error){throw new ApiException(409,"Song is already liked");}return songs.get(songId);}
    @Transactional public void unlike(long songId){var actor=accounts.current();if(jdbc.update("DELETE FROM liked_songs WHERE user_id=? AND song_id=?",actor.id(),songId)==0)throw new ApiException(404,"Liked song not found");}
}

@RestController
@RequestMapping("/api/likes")
class LikeController {
    private final Likes likes; LikeController(Likes likes){this.likes=likes;}
    @GetMapping List<Songs.SongDto> list(){return likes.list();}
    @PostMapping("/{songId}") ResponseEntity<Songs.SongDto> like(@PathVariable long songId){return ResponseEntity.status(201).body(likes.like(songId));}
    @DeleteMapping("/{songId}") ResponseEntity<Void> unlike(@PathVariable long songId){likes.unlike(songId);return ResponseEntity.noContent().build();}
}
