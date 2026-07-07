import json
import requests
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

# ==========================================
# 1. 設定監控藝人名單 (改為使用藝人 ID 追蹤)
# 格式: "藝人ID": "自訂顯示名稱"
# ==========================================
TRACKED_ARTISTS = {
    "KR": {
        "82779545": "Hearts2Hearts",
        "80632010": "i-dle"
        # ⚠️ 請在此處繼續加入其他 KR 藝人的 ID
    },
    "JP": {
        # ⚠️ 請在此處繼續加入其他 JP 藝人的 ID
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
                display_artist_name = original_artist_name

                if artist_id and artist_id in flat_tracked_ids:
                    is_tracked = True
                    display_artist_name = flat_tracked_ids[artist_id] 
                
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
    # === 將保留時間改為 180 天 ===
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
                # === 判定是否超過 180 天 ===
                if song_datetime > cutoff_180:
                    final_list.append(song)
            else:
                if song_date == today_date:
                    final_list.append(song)
        except ValueError:
            final_list.append(song)

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
