package com.raagify;

import java.util.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Service
public class Recommendations {
    private record Candidate(long id,String genre,List<Double> vector,long plays) {}
    private record Ranked(long id,double score,long plays) {}
    private final JdbcTemplate jdbc; private final Accounts accounts; private final Songs songs;
    public Recommendations(JdbcTemplate jdbc,Accounts accounts,Songs songs){this.jdbc=jdbc;this.accounts=accounts;this.songs=songs;}

    public List<Songs.SongDto> similar(long songId){
        Songs.SongDto source=songs.get(songId);List<Double> vector=songs.vector(songId);
        return candidates("WHERE id<>?",songId).stream().map(c->{double score=!vector.isEmpty()&&!c.vector().isEmpty()?cosine(vector,c.vector()):genreScore(source.genre(),c.genre());return new Ranked(c.id(),score,c.plays());})
            .sorted(Comparator.comparingDouble(Ranked::score).reversed().thenComparing(Comparator.comparingLong(Ranked::plays).reversed())).limit(10).map(Ranked::id).map(songs::get).toList();
    }

    public List<Songs.SongDto> forCurrent(){
        var actor=accounts.current();
        var liked=jdbc.query("SELECT song_id FROM liked_songs WHERE user_id=?",(rs,row)->rs.getLong(1),actor.id());
        var recent=jdbc.query("SELECT song_id FROM play_history WHERE user_id=? GROUP BY song_id ORDER BY MAX(played_at) DESC LIMIT 20",(rs,row)->rs.getLong(1),actor.id());
        var signals=new ArrayList<Long>();signals.addAll(liked);signals.addAll(recent);
        if(signals.isEmpty()) return jdbc.query("SELECT id FROM songs ORDER BY play_count DESC,created_at DESC LIMIT 20",(rs,row)->rs.getLong(1)).stream().map(songs::get).toList();
        var vectors=signals.stream().map(songs::vector).filter(v->!v.isEmpty()).toList();List<Double> profile=average(vectors);
        var genres=new HashSet<String>();for(Long id:signals){String genre=jdbc.queryForObject("SELECT genre FROM songs WHERE id=?",String.class,id);genres.addAll(GenreTags.signals(genre));}
        Set<Long> excluded=new HashSet<>(liked);
        return candidates("").stream().filter(c->!excluded.contains(c.id())).map(c->{double similarity=!profile.isEmpty()&&!c.vector().isEmpty()?cosine(profile,c.vector()):0;double genre=GenreTags.signals(c.genre()).stream().anyMatch(genres::contains)?.2:0;return new Ranked(c.id(),similarity+genre,c.plays());})
            .sorted(Comparator.comparingDouble(Ranked::score).reversed().thenComparing(Comparator.comparingLong(Ranked::plays).reversed())).limit(20).map(Ranked::id).map(songs::get).toList();
    }

    private List<Candidate> candidates(String where,Object... args){return jdbc.query("SELECT id,genre,feature_status,play_count FROM songs "+where,(rs,row)->{long id=rs.getLong("id");return new Candidate(id,rs.getString("genre"),"READY".equals(rs.getString("feature_status"))?songs.vector(id):List.of(),rs.getLong("play_count"));},args);}
    private static double genreScore(String a,String b){return GenreTags.similarity(a,b);}
    private static List<Double> average(List<List<Double>> vectors){if(vectors.isEmpty())return List.of();int n=vectors.stream().mapToInt(List::size).min().orElse(0);var result=new ArrayList<Double>(n);for(int i=0;i<n;i++){double sum=0;for(var v:vectors)sum+=v.get(i);result.add(sum/vectors.size());}return result;}
    static double cosine(List<Double> a,List<Double> b){if(a.size()!=b.size())return 0;int n=a.size();double dot=0,aa=0,bb=0;for(int i=0;i<n;i++){double x=a.get(i),y=b.get(i);dot+=x*y;aa+=x*x;bb+=y*y;}return aa==0||bb==0?0:dot/(Math.sqrt(aa)*Math.sqrt(bb));}
}

@RestController
@RequestMapping("/api/recommendations")
class RecommendationController {
    private final Recommendations recommendations; RecommendationController(Recommendations recommendations){this.recommendations=recommendations;}
    @GetMapping java.util.List<Songs.SongDto> get(){return recommendations.forCurrent();}
}
