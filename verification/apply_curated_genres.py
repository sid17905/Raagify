"""Apply the user's supplied labels as protected admin edits, not model predictions."""
import json
import re
import httpx
from runtime import ROOT, RUNTIME, credentials

TAGS = {
"505":"Indie Rock / Alternative Rock",
"Sapphire":"Punjabi Pop",
"Lose My Mind":"Pop Rap / Electropop / Synthpop / Dance-Pop",
"Dard - E - Disco":"Bollywood Disco / Dance-Pop / Filmi",
"Actor":"Indie Pop / Pop Rock / Bedroom Pop",
"Yeh Fitoor Mera":"Bollywood Romantic Ballad / Filmi / Sufi Pop",
"No. 1 Party Anthem":"Indie Rock / Alternative Rock / Lounge Pop",
"Mausam":"Bollywood Pop / Filmi / Soft Rock",
"Lover Girl":"Indie Pop / Bedroom Pop / Jazz Pop",
"Labb Par Aaye":"Hindustani Classical Fusion / Ghazal / Filmi",
"Do Me a Favour":"Indie Rock / Post-Punk Revival / Alternative Rock",
"Dracula":"Psychedelic Pop / Psychedelic Rock / Synthpop",
"Behe Chala":"Bollywood Pop / Ambient Pop / Filmi",
"Aakhri Ishq":"Bollywood Romantic Ballad / Indipop / Filmi",
"Khat":"Indie Pop / Acoustic Pop / Singer-Songwriter",
"Destiny - Mann Atkeya":"Desi Hip-Hop / Pop Rap / Sufi Fusion",
"Ishq Jalakar - Karvaan":"Sufi Rock / Qawwali Fusion / Filmi",
"Dhurandhar The Revenge - Aari Aari":"Punjabi Pop / Bhangra Hip-Hop / Dance-Pop",
"Main Aur Tu":"Punjabi Pop / Desi Hip-Hop / Urban Punjabi",
"Wild Ride":"Desi Hip-Hop / Trap / Punjabi Rap",
"Banda Kaam Ka":"Experimental Hip-Hop / Alternative R&B / Indipop",
"A Certain Romance":"Indie Rock / Garage Rock Revival / Post-Punk Revival",
"Move - Yeh Ishq Ishq":"Bollywood Hip-Hop / Qawwali Fusion / Dance-Pop",
"Kya Mujhe Pyar Hai":"Bollywood Pop Rock / Filmi / Romantic Ballad",
"Smooth Criminal - 2012 Remaster":"Pop / Funk / Dance-Pop / New Jack Swing",
"Dirty Diana":"Hard Rock / Pop Rock / Arena Rock",
"Billie Jean":"Post-Disco / Pop / Funk / Dance-Pop",
"Smooth Operator":"Sophisti-Pop / Smooth Jazz / Quiet Storm / Soul",
"Borderline":"Psychedelic Pop / Nu-Disco / Synthpop",
"The Less I Know The Better":"Psychedelic Pop / Nu-Disco / Funk Rock",
"Tu Meri":"Bollywood Dance-Pop / Electro-Pop / Filmi",
"Aadat Se Majboor":"Bollywood Hip-Hop / Dance-Pop / Filmi",
"Can't Take My Eyes Off You":"Blue-Eyed Soul / Traditional Pop / Baroque Pop",
"Bakamitai - Taxi Driver Edition":"Kayōkyoku / J-Pop Ballad / Enka-Pop",
"Kalank - Title Track":"Bollywood Romantic Ballad / Orchestral Pop / Filmi",
"Die With A Smile":"Soft Rock / Pop Soul / Ballad",
"I Ain't Worried":"Pop Rock / Sunshine Pop / Dance-Pop",
"Zara Sa":"Bollywood Pop Rock / Filmi / Romantic Ballad",
"Tere Liye":"Bollywood Romantic Ballad / Filmi / Pop",
"Dhurandhar - Title Track":"Desi Hip-Hop / Punjabi Trap / Hardcore Hip-Hop",
"Rasputin":"Euro-Disco / Disco / Europop",
"Naal Nachna":"Punjabi Pop / Bhangra / Dance-Pop",
"Thriller":"Disco / Post-Disco / Funk / Pop",
"Last Christmas":"Synthpop / Holiday Pop / Sophisti-Pop",
"Shinunoga E-Wa":"J-Pop / R&B / Kayōkyoku",
"Pungi":"Bollywood Dance-Pop / Bhangra Pop / Filmi",
"Yaad Aa Raha Hai":"Bollywood Disco / Synth-Disco / Filmi",
"Maston Ka Jhund":"Bollywood Folk Rock / Bhangra Rock / Filmi",
"Get Lucky Radio Edit":"Nu-Disco / Funk / French House / Dance-Pop",
"I Was Made For Lovin' You":"Disco Rock / Hard Rock / Glam Rock",
"Bye Bye Bye":"Teen Pop / Dance-Pop / Electropop",
"You Give Love A Bad Name":"Glam Metal / Arena Rock / Hard Rock",
"I Wanna Be Yours":"Indie Rock / Psychedelic Rock / Alternative Rock",
"Chura Ke Dil Mera":"90s Bollywood Pop / Filmi / Romantic Dance-Pop",
"Feel It":"Indie Pop / Alternative R&B / Bedroom Pop",
"Aari Aari":"Punjabi Pop / Bhangra Hip-Hop / Dance-Pop",
"Jaan Se Guzarte Hain":"Sufi / Punjabi Soul / Ghazal Fusion",
"Vaari Jaavan":"Punjabi Pop / Bhangra / Urban Punjabi",
"Careless Whisper":"Sophisti-Pop / Smooth Jazz / Blue-Eyed Soul / Pop Ballad",
"Gehra Hua-Dhurandhar":"Bollywood Romantic Ballad / Filmi / Sufi Pop",
}

def normalized(value): return re.sub(r"[^\w]","",value.casefold())

def main():
    with httpx.Client(base_url="http://127.0.0.1:18080/api",timeout=20) as client:
        def csrf():return {"X-XSRF-TOKEN":client.get("/auth/csrf").json()["token"]}
        assert client.post("/auth/login",headers=csrf(),data={"email":"private-admin@raagify.test","password":credentials()["adminPassword"]}).status_code==200
        first=client.get("/songs?size=50").json();songs=list(first["content"])
        for page in range(1,first["totalPages"]):songs+=client.get(f"/songs?size=50&page={page}").json()["content"]
        (RUNTIME/"curated-genre-backup.json").write_text(json.dumps(songs))
        applied=[];unmatched=[]
        for song in songs:
            name=normalized(song["title"])
            candidates=[(key,genre) for key,genre in TAGS.items() if name.startswith(normalized(key))]
            if not candidates:unmatched.append({"id":song["id"],"title":song["title"]});continue
            key,genre=max(candidates,key=lambda item:len(normalized(item[0])))
            assert len(genre)<=80
            body={key:song[key] for key in ["title","artist","album","durationSeconds"]};body["genre"]=genre
            response=client.put(f"/admin/songs/{song['id']}",headers=csrf(),json=body);assert response.status_code==200
            assert response.json()["genreSource"]=="ADMIN_OVERRIDE"
            applied.append({"id":song["id"],"title":song["title"],"genre":genre})
        result={"classification":"Observed","source":"User-supplied curated genres; not inferred by the model","applied":applied,"unmatched":unmatched}
        (ROOT/"verification/curated-genres-results.json").write_text(json.dumps(result,indent=2));print(f"Observed: applied {len(applied)} curated genre sets; unmatched: {unmatched}")

if __name__=="__main__":main()
