package com.raagify;

import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Service
public class Listening {
    private final JdbcTemplate jdbc; private final Accounts accounts; private final Songs songs;
    public Listening(JdbcTemplate jdbc,Accounts accounts,Songs songs){this.jdbc=jdbc;this.accounts=accounts;this.songs=songs;}
    @Transactional public void record(long songId){var actor=accounts.current();songs.get(songId);jdbc.update("INSERT INTO play_history(user_id,song_id) VALUES(?,?)",actor.id(),songId);jdbc.update("UPDATE songs SET play_count=play_count+1 WHERE id=?",songId);}
    public List<Songs.SongDto> recent(){var actor=accounts.current();return jdbc.query("SELECT song_id FROM play_history WHERE user_id=? GROUP BY song_id ORDER BY MAX(played_at) DESC LIMIT 30",(rs,row)->rs.getLong(1),actor.id()).stream().map(songs::get).toList();}
}

@RestController
@RequestMapping("/api/history")
class HistoryController {
    private final Listening listening; HistoryController(Listening listening){this.listening=listening;}
    @GetMapping("/recent") List<Songs.SongDto> recent(){return listening.recent();}
}
