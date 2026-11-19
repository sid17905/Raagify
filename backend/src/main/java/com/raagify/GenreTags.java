package com.raagify;

import java.text.Normalizer;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

final class GenreTags {
    static Map<String,String> tags(String genre){
        var result=new LinkedHashMap<String,String>();
        if(genre==null)return result;
        for(String tag:genre.split("/")){
            String display=tag.trim();if(display.isEmpty())continue;
            String key=Normalizer.normalize(display,Normalizer.Form.NFKC).toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]","");
            if(!key.isEmpty())result.putIfAbsent(key,display);
        }
        return result;
    }
    static Set<String> signals(String genre){var tags=tags(genre);tags.remove("unclassified");tags.remove("unknown");return tags.keySet();}
    static double similarity(String left,String right){var a=signals(left);var b=signals(right);if(a.isEmpty()||b.isEmpty())return 0;long common=a.stream().filter(b::contains).count();return common/(double)(a.size()+b.size()-common);}
}
