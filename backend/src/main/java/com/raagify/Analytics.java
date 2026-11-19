package com.raagify;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Service
public class Analytics {
    public record Totals(long songs,long listeners,long playlists,long likes,long plays,long readyFeatures,long pendingFeatures,long curatedGenres,long unclassifiedSongs,long covers) {}
    public record Period(long plays,long activeListeners,long newListeners) {}
    public record Day(String date,long plays) {}
    public record Genre(String name,long songs,long plays) {}
    public record Popular(long id,String title,String artist,String coverUrl,long plays,long likes) {}
    public record Dashboard(Totals totals,Period period,int days,String timezone,List<Day> dailyPlays,List<Genre> genres,List<Popular> popularSongs,MediaClient.Health processor) {}
    private final JdbcTemplate jdbc;
    private final Accounts accounts;
    private final MediaClient media;
    public Analytics(JdbcTemplate jdbc,Accounts accounts,MediaClient media){this.jdbc=jdbc;this.accounts=accounts;this.media=media;}

    @Transactional(readOnly=true,isolation=Isolation.REPEATABLE_READ)
    public Dashboard dashboard(int days){
        if(!accounts.current().role().equals("ADMIN"))throw new ApiException(403,"Admin access required");
        if(days<7||days>90)throw new ApiException(400,"Days must be between 7 and 90");
        LocalDate end=LocalDate.now(ZoneOffset.UTC),start=end.minusDays(days-1);
        Timestamp from=Timestamp.from(start.atStartOfDay().toInstant(ZoneOffset.UTC)),until=Timestamp.from(end.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC));
        var totals=new Totals(count("SELECT COUNT(*) FROM songs"),count("SELECT COUNT(*) FROM users WHERE role='LISTENER'"),count("SELECT COUNT(*) FROM playlists"),count("SELECT COUNT(*) FROM liked_songs"),count("SELECT COUNT(*) FROM play_history"),count("SELECT COUNT(*) FROM songs WHERE feature_status='READY'"),count("SELECT COUNT(*) FROM songs WHERE feature_status='PENDING'"),count("SELECT COUNT(*) FROM songs WHERE genre_source='ADMIN_OVERRIDE'"),count("SELECT COUNT(*) FROM songs WHERE genre IS NULL OR genre='' OR genre='Unclassified'"),count("SELECT COUNT(*) FROM songs WHERE cover_storage_name IS NOT NULL"));
        var period=new Period(count("SELECT COUNT(*) FROM play_history WHERE played_at>=? AND played_at<?",from,until),count("SELECT COUNT(DISTINCT p.user_id) FROM play_history p JOIN users u ON u.id=p.user_id WHERE u.role='LISTENER' AND p.played_at>=? AND p.played_at<?",from,until),count("SELECT COUNT(*) FROM users WHERE role='LISTENER' AND created_at>=? AND created_at<?",from,until));
        var daily=new HashMap<String,Long>();jdbc.query("SELECT DATE(played_at) day,COUNT(*) plays FROM play_history WHERE played_at>=? AND played_at<? GROUP BY DATE(played_at)",rs->{daily.put(rs.getDate("day").toLocalDate().toString(),rs.getLong("plays"));},from,until);
        var daysList=new ArrayList<Day>();for(LocalDate date=start;!date.isAfter(end);date=date.plusDays(1))daysList.add(new Day(date.toString(),daily.getOrDefault(date.toString(),0L)));
        var genreTotals=new java.util.HashMap<String,long[]>();var genreNames=new java.util.HashMap<String,String>();
        jdbc.query("SELECT genre,play_count FROM songs",rs->{var tags=GenreTags.tags(rs.getString("genre"));if(tags.isEmpty())tags=GenreTags.tags("Unclassified");for(var tag:tags.entrySet()){genreNames.putIfAbsent(tag.getKey(),tag.getValue());var counts=genreTotals.computeIfAbsent(tag.getKey(),key->new long[2]);counts[0]++;counts[1]+=rs.getLong("play_count");}});
        var genres=genreTotals.entrySet().stream().map(entry->new Genre(genreNames.get(entry.getKey()),entry.getValue()[0],entry.getValue()[1])).sorted(java.util.Comparator.comparingLong(Genre::songs).reversed().thenComparing(Genre::name)).toList();
        var popular=jdbc.query("SELECT s.id,s.title,s.artist,s.cover_storage_name,s.play_count,(SELECT COUNT(*) FROM liked_songs l WHERE l.song_id=s.id) likes FROM songs s ORDER BY s.play_count DESC,likes DESC,s.id DESC LIMIT 10",(rs,row)->new Popular(rs.getLong("id"),rs.getString("title"),rs.getString("artist"),rs.getString("cover_storage_name")==null?null:"/api/songs/"+rs.getLong("id")+"/cover",rs.getLong("play_count"),rs.getLong("likes")));
        return new Dashboard(totals,period,days,"UTC",daysList,genres,popular,media.health());
    }
    private long count(String sql,Object...args){Long result=jdbc.queryForObject(sql,Long.class,args);return result==null?0:result;}
}

@RestController
@RequestMapping("/api/admin/analytics")
class AnalyticsController {
    private final Analytics analytics;
    AnalyticsController(Analytics analytics){this.analytics=analytics;}
    @GetMapping Analytics.Dashboard get(@RequestParam(defaultValue="30") int days){return analytics.dashboard(days);}
}
