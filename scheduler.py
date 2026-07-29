import json
import requests
import os
import re
import time
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
        "80632473": "Yuqi",
        "83405256": "OURBIRTHDAY"
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
# 爬取「單一藝人自己的頁面」，抓他最新發行的專輯
# 💡 這是解決 J-POP（或其他分類）漏爬問題的核心：
#    不管 Genie 把這張專輯歸類成什麼分類，
#    只要它出現在該藝人自己的「발매 앨범」列表裡，就一定抓得到。
#    頁面預設就會顯示該藝人最新的幾張專輯，且已經是新到舊排序。
# ==========================================
# ==========================================
# 抓取「單一專輯頁面」的 장르/스타일 欄位，轉換成前端要顯示的曲風標籤
#    가요 -> K-POP；OST、J-POP 等其他分類則照字面顯示
# ==========================================
def map_style_to_genre_label(style_text):
    style_text = style_text.strip()
    if not style_text:
        return None
    if style_text == "가요":
        return "K-POP"
    return style_text


def fetch_album_genre(album_link, headers):
    try:
        response = requests.get(album_link, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        style_text = ""

        # 先嘗試常見的資訊清單結構（依 Genie 專輯頁面版型可能為 dl/dt/dd 或 li 結構）
        for row in soup.select("li"):
            label = row.select_one(".info, dt, .title, span")
            row_text = row.get_text(" ", strip=True)
            if row_text.startswith("장르") or "장르/스타일" in row_text or "장르 / 스타일" in row_text:
                style_text = row_text
                break

        if not style_text:
            # 後備方案：直接在整頁純文字中定位「장르/스타일」欄位內容
            page_text = soup.get_text(" ", strip=True)
            match = re.search(r'장르\s*/?\s*스타일\s*([^\s].*?)(?:발매사|기획사|발매일|$)', page_text)
            if match:
                style_text = "장르/스타일 " + match.group(1).strip()

        if not style_text:
            return None

        # 欄位格式通常是「장르/스타일  댄스 / 가요」或「장르/스타일  팝 / J-POP」
        # 去掉欄位標籤本身，取「/」分隔後的最後一段（스타일）
        cleaned = style_text.replace("장르/스타일", "").replace("장르 / 스타일", "").strip()
        parts = [p.strip() for p in cleaned.split("/") if p.strip()]
        if not parts:
            return None

        return map_style_to_genre_label(parts[-1])

    except Exception:
        return None



    new_songs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://www.genie.co.kr/detail/artistInfo?xxnm={artist_id}"

    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')

        album_section = soup.select_one("#artist-album")
        if not album_section:
            return new_songs

        album_items = album_section.select("ul > li")

        for item in album_items:
            try:
                thumb_elem = item.select_one("a.album-thumb")
                title_elem = item.select_one("a.artist")  # 💡 這裡的 class="artist" 其實是專輯標題連結
                date_elem = item.select_one("span.date")

                onclick_src = ""
                if thumb_elem and 'onclick' in thumb_elem.attrs:
                    onclick_src = thumb_elem['onclick']
                elif title_elem and 'onclick' in title_elem.attrs:
                    onclick_src = title_elem['onclick']

                match_album = re.search(r'fnViewAlbumLayer\((\d+)\)', onclick_src)
                if not match_album:
                    continue
                album_id = match_album.group(1)

                final_link = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"

                # 檢查是否已經抓過
                if final_link in existing_links or final_link in seen_links:
                    continue
                seen_links.add(final_link)

                title = title_elem.text.strip() if title_elem else "未知專輯"

                # === 用頁面上真實的發行日期，而不是「現在爬蟲執行的時間」 ===
                # 💡 這裡的日期格式是 "2026.07.29"，沒有時分資訊，統一補 00:00
                #    避免把明明是很久以前發行的專輯，誤標成「今天發現」
                date_text = date_elem.text.strip() if date_elem else ""
                release_date = None
                if date_text:
                    try:
                        release_date = datetime.strptime(date_text, "%Y.%m.%d")
                    except ValueError:
                        release_date = None

                if release_date:
                    found_at = release_date.strftime("%Y-%m-%d") + " 00:00"
                else:
                    # 抓不到日期的極端情況才退回用現在時間，避免整筆資料被跳過
                    found_at = get_taiwan_time().strftime("%Y-%m-%d %H:%M")

                img_elem = item.select_one("span.cover img")
                img_src = ""
                if img_elem and img_elem.get('src'):
                    src = img_elem['src']
                    img_src = "https:" + src if src.startswith("//") else src

                genre_label = fetch_album_genre(final_link, headers)

                new_song = {
                    "artist": artist_display_name,
                    "title": title,
                    "image": img_src,
                    "link": final_link,
                    "found_at": found_at,
                    "is_tracked": True,
                    "genre": genre_label
                }
                new_songs.append(new_song)
                print(f"   -> ⭐ 關注（藝人頁）：{artist_display_name} - {title}" + (f" [{genre_label}]" if genre_label else ""))

            except Exception:
                continue

    except Exception as e:
        print(f"⚠️ 藝人頁面爬蟲錯誤 ({artist_display_name} / {artist_id}): {e}")

    return new_songs


# ==========================================
# 主邏輯
# ==========================================
def scrape_job():
    print(f"[{get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')}] 雲端爬蟲啟動 (Taiwan Time)...")

    existing_songs = load_existing_data()
    existing_links = {song['link'] for song in existing_songs}
    new_songs = []
    seen_links = set()  # 這次執行中，避免不同來源重複收到同一首歌

    # 將分類的藝人 ID 扁平化，方便快速比對
    flat_tracked_ids = {}
    for category, artists in TRACKED_ARTISTS.items():
        for artist_id, artist_name in artists.items():
            flat_tracked_ids[str(artist_id)] = artist_name

    # 依序爬取每個追蹤藝人「自己的頁面」
    # 這一步不受 Genie 的分類（國內/J-POP/其他海外分類...）影響，
    # 只要是該藝人自己頁面上列出的新專輯，一定抓得到。
    print(f"[{get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')}] 開始逐一檢查 {len(flat_tracked_ids)} 位追蹤藝人的個人頁面...")
    for artist_id, artist_display_name in flat_tracked_ids.items():
        new_songs.extend(scrape_artist_page(artist_id, artist_display_name, existing_links, seen_links))
        time.sleep(0.5)  # 禮貌性延遲，避免短時間內對同一網站發出過多請求

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
