package com.raagify;

final class MetadataText {
    private static final String BRAND="(?:spotidost|spotidown|spotimate|spotiflyer|spotdown)";
    static String clean(String value,boolean title){
        if(value==null)return null;
        String text=value.replaceAll("(?i)https?://(?:www\\.)?"+BRAND+"\\.[a-z]+\\S*","").replaceAll("(?i)\\b(?:www\\.)?"+BRAND+"(?:\\.[a-z]+)?\\b","");
        if(title)text=text.replaceFirst("^\\s*\\d{1,3}_+\\s*","");
        text=text.replaceAll("[\\[({]\\s*[\\])}]","").replaceAll("\\s+"," ").replaceAll("^[ \\t\\r\\n_|-]+|[ \\t\\r\\n_|-]+$","");
        return text.isBlank()?null:text;
    }
}
