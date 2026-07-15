import json
import requests
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

# ==========================================
# 1. 設定監控藝人名單 (改為使用藝人 ID 追蹤)
# 格式: "藝人ID": "自訂顯示名稱 (給側邊欄用的)"
# ==========================================
TRACKED_ARTISTS = {
    "KR": {
        "80957377": "aespa",
        "80197389": "AKMU",
        "80131399": "Apink",
        "82934007": "Baby DONT Cry",
        "82262194": "BABYMONSTER",
        "82507911": "BADVILLAIN",
        "80158972": "Baek A Yeon",
        "82072751": "BBGIRLS",
        "80667991": "BIBI",
        "81254551": "Billlie",
        "80539764": "BLACKPINK",
        "80316854": "BOL4",
        "80519791": "Choi Yoo jung",
        "80519790": "Chung Ha",
        "81394103": "CLASSy",
        "80347927": "CLC",
        "81491030": "CSR",
        "80560326": "Dreamcatcher",
        "82164268": "EL7Z UP",
        "81223544": "Ellui",
        "80441312": "Eunha",
        "80682661": "EVERGLOW",
        "81630823": "FIFTY FIFTY",
        "80606382": "fromis_9",
        "80327727": "GFRIEND",
        "82162588": "Gyubin",
        "81289352": "H1-KEY",
        "80923087": "Hayeon",
        "82779545": "Hearts2Hearts",
        "82833348": "Hebi",
        "81399607": "HUH YUNJIN",
        "80441390": "HwaSa",
        "80632010": "i-dle",
        "82387391": "ILLIT",
        "81354329": "ILY:1",
        "80679336": "ITZY",
        "67872918": "IU",
        "81271496": "IVE",
        "80660177": "IZ*ONE",
        "82704290": "izna",
        "80539780": "Jennie",
        "80468937": "JIHYO",
        "80539782": "JISOO",
        "80661354": "JO YURI",
        "80441325": "Joy",
        "80661359": "Kang Hye Won",
        "81286392": "Kep1er",
        "82792175": "KiiiKiii",
        "80519786": "Kim Sejeong",
        "80668350": "KIMDOAH",
        "82007551": "KISS OF LIFE",
        "80661358": "Kwon Eun Bi",
        "80704912": "KyoungSeo",
        "83176183": "LATENCY",
        "81397289": "LE SSERAFIM",
        "80661363": "LEE CHAE YEON",
        "80158970": "LEE HI",
        "81131367": "LIGHTSUM",
        "80539781": "Lisa",
        "80279134": "Mamamoo",
        "80632475": "Minnie",
        "80632474": "Miyeon",
        "80441388": "Moonbyul",
        "80740728": "MRCH",
        "80468933": "NAYEON",
        "81490206": "NewJeans",
        "81326040": "NMIXX",
        "80357324": "OH MY GIRL",
        "82209678": "QWER",
        "80284018": "Red Velvet",
        "82379125": "RESCENE",
        "80539779": "Rosé",
        "80602557": "Rothy",
        "81165501": "Saebit",
        "81655094": "Seo Dahyun",
        "80441324": "SEULGI",
        "80441314": "SINB",
        "80794774": "siso",
        "80441387": "Solar",
        "80519789": "Somi",
        "80632471": "SOOJIN",
        "79948613": "Soyeon",  
        "80953355": "STAYC",
        "80119174": "Suzy",
        "56069675": "Taeyeon",
        "79930356": "T-ara",
        "81599561": "tripleS",
        "80463902": "TWICE",
        "80468941": "TZUYU",
        "80441315": "Umji",
        "81333511": "VIVIZ",
        "80258051": "Wendy",
        "80441389": "Wheein",
        "80957384": "WINTER",
        "80505860": "WJSN",
        "80840761": "WOOAH",
        "80661355": "YENA",
        "80441311": "Yerin",
        "42307533": "Younha",
        "80441313": "Yuju",
        "42114005": "Yunsae",
        "80632473": "Yuqi"
        # ⚠️ 請在此處繼續加入
    },
    "JP": {
        "80163641": "Ado",
        "82204740": "Ai Tomioka",
        "80430477": "Aimer",
        "80566612": "aimyon",
        "82623175": "Aooo",
        "81084320": "ATARAYO",
        "81016237": "BAND-MAID",
        "80923631": "chilldspot",
        "81189253": "Chilli Beans",
        "82802328": "Faulieu",
        "82779519": "HANA",
        "80163390": "LiSA",
        "80622875": "Majiko",
        "82570285": "NEK!",
        "80649539": "ReoNa",
        "81408764": "TRiDENT",
        "82389809": "tuki.",
        "81021172": "yama",
        "80847403": "YOASOBI",
        "80729088": "Yorushika",
        "81145659": "Yuika",
        "80661613": "ZUTOMAYO",
        "82783169": "ねぎ塩豚丼"
        # ⚠️ 請在此處繼續加入
    }
}

DATA_FILE = "songs_data.json"

# ==========================================
# 工具函式
# ==========================================
def get_taiwan_timezone():
    return timezone(timedelta(hours=8))

def get_taiwan_time():
    return datetime.now(get_taiwan_timezone())

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "songs" in data: return data["songs"]
                return []
        except: return []
    return []

# ==========================================
# 主邏輯
# ==========================================
def scrape_job():
    print(f"[{get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')}] 雲端爬蟲啟動 (Taiwan Time)...")
    
    existing_songs = load_existing_data()
    existing_links = {song['link'] for song in existing_songs}
    new_songs = []

    # 將分類的藝人 ID 扁平化，方便快速比對
    flat_tracked_ids = {}
    for category, artists in TRACKED_ARTISTS.items():
        for artist_id, artist_name in artists.items():
            flat_tracked_ids[str(artist_id)] = artist_name
    
    try:
        url = "https://www.genie.co.kr/newest/song"
        headers = { 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" 
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        song_list = soup.select("table.list-wrap > tbody > tr")

        for song in song_list:
            try:
                artist_elem = song.select_one("a.artist")
                original_artist_name = artist_elem.text.strip() if artist_elem else "未知藝人"

                # === 抓取 onclick 裡的藝人 ID ===
                artist_id = ""
                if artist_elem and 'onclick' in artist_elem.attrs:
                    match_artist = re.search(r'fnViewArtist\((\d+)\)', artist_elem['onclick'])
                    if match_artist:
                        artist_id = match_artist.group(1)

                # === 判斷是否為追蹤藝人 ===
                is_tracked = False
                # 💡 這裡直接保持原始名稱，不再用我們字典裡的名稱覆蓋它
                display_artist_name = original_artist_name 

                if artist_id and artist_id in flat_tracked_ids:
                    is_tracked = True
                
                link_id = song['songid']
                song_link = f"https://www.genie.co.kr/detail/songInfo?xgnm={link_id}"

                album_elem = song.select_one("a.albumtitle")
                title = album_elem.text.strip() if album_elem else "未知專輯"
                if "TITLE" in title: title = title.replace("TITLE", "").strip()
                if "19금" in title: title = title.replace("19금", "").strip()

                # === 抓取 onclick 裡的專輯 ID ===
                album_id = ""
                if album_elem and 'onclick' in album_elem.attrs:
                    match_album = re.search(r'fnViewAlbumLayer\((\d+)\)', album_elem['onclick'])
                    if match_album:
                        album_id = match_album.group(1)

                # === 組成專輯連結 ===
                final_link = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}" if album_id else song_link

                # 檢查是否已經抓過
                if song_link in existing_links or final_link in existing_links: 
                    continue

                img_elem = song.select_one("a.cover img")
                img_src = "https:" + img_elem['src'] if img_elem else ""

                new_song = {
                    "artist": display_artist_name,
                    "title": title,
                    "image": img_src,
                    "link": final_link,
                    "found_at": get_taiwan_time().strftime("%Y-%m-%d %H:%M"),
                    "is_tracked": is_tracked
                }
                new_songs.append(new_song)
                
                log_prefix = "⭐ 關注" if is_tracked else "   其他"
                print(f"   -> {log_prefix}：{display_artist_name} - {title}")

            except Exception as e: continue

    except Exception as e:
        print(f"⚠️ 爬蟲錯誤: {e}")

    full_song_list = new_songs + existing_songs
    now_tw = get_taiwan_time()
    today_date = now_tw.date()
    cutoff_180 = now_tw - timedelta(days=180)
    final_list = []
    tz_tw = get_taiwan_timezone()

    for song in full_song_list:
        try:
            song_datetime_naive = datetime.strptime(song['found_at'], "%Y-%m-%d %H:%M")
            song_datetime = song_datetime_naive.replace(tzinfo=tz_tw)
            song_date = song_datetime.date()
            is_my_artist = song.get('is_tracked', False)
            
            if is_my_artist:
                if song_datetime > cutoff_180:
                    final_list.append(song)
            else:
                if song_date == today_date:
                    final_list.append(song)
        except ValueError:
            final_list.append(song)

        # 這裡會從 TRACKED_ARTISTS 裡抓取「你自訂的名字」送到前端側邊欄
        sorted_tracked_artists = {
            category: sorted(list(artists.values()), key=lambda x: x.lower()) 
            for category, artists in TRACKED_ARTISTS.items() if artists
        }

    # 3. 存檔
    data_to_save = {
        "updated_at": get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
        "tracked_artists": sorted_tracked_artists, 
        "songs": final_list
    }
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 資料已更新。目前資料庫總數: {len(final_list)}")

if __name__ == "__main__":
    scrape_job()
