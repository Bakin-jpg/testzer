import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# URL HALAMAN UTAMA (BUKAN JADWAL)
URL = "https://kilatlive.live/"
NAMA_FILE_PLAYLIST = "kilatlive_playlist.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

def setup_driver():
    """Mengatur dan mengembalikan instance WebDriver."""
    print("Menyiapkan WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    
    # Menambahkan kapabilitas untuk logging network
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Mengatur timeout agar tidak menunggu selamanya
        driver.set_page_load_timeout(30)
        return driver
    except WebDriverException as e:
        print(f"Error fatal saat setup driver: {e}")
        return None

def find_stream_url_from_logs(driver):
    """Menganalisis log jaringan untuk menemukan URL streaming .m3u8."""
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if 'Network.responseReceived' in log['method']:
                params = log.get('params', {})
                response = params.get('response', {})
                url = response.get('url', '')
                if '.m3u8' in url:
                    print(f"  -> Ditemukan URL stream: {url}")
                    return url
    except Exception as e:
        print(f"  -> Gagal saat membaca log jaringan: {e}")
    return None

def create_playlist():
    """Fungsi utama untuk membuat playlist."""
    driver = setup_driver()
    if not driver:
        return

    playlist_content = "#EXTM3U\n"
    found_any_streams = False

    try:
        print(f"Mengakses halaman utama: {URL}")
        driver.get(URL)
        time.sleep(10) # Tunggu halaman utama memuat semua elemen

        # Cari SEMUA link yang valid di halaman utama
        # Kita targetkan link yang ada di dalam elemen dengan atribut data-id
        match_links_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-id]")
        
        if not match_links_elements:
            print("Tidak ditemukan elemen pertandingan di halaman utama. Selector mungkin perlu diubah.")
            return

        # Kumpulkan semua URL unik untuk menghindari duplikasi
        unique_urls = list(dict.fromkeys([elem.get_attribute('href') for elem in match_links_elements if elem.get_attribute('href')]))
        
        print(f"Ditemukan {len(unique_urls)} link pertandingan unik. Memproses satu per satu...")

        for i, match_url in enumerate(unique_urls, 1):
            print(f"\n[{i}/{len(unique_urls)}] Memproses: {match_url}")
            try:
                # Buka halaman pertandingan di tab baru
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(match_url)
                
                # Tunggu beberapa detik agar player sempat melakukan request
                time.sleep(8)
                
                stream_url = find_stream_url_from_logs(driver)
                
                if stream_url:
                    # Ambil judul dari halaman pertandingan
                    title = driver.title.replace("Nonton ", "").replace(" Gratis - Kilatlive", "")
                    print(f"  -> Judul Acara: {title}")

                    # Tambahkan ke playlist dengan format yang BENAR
                    playlist_content += f'#EXTINF:-1, {title}\n'
                    playlist_content += f'#EXTVLCOPT:http-referrer={match_url}\n'
                    playlist_content += f'#EXTVLCOPT:http-origin=https://kilatlive.live\n'
                    playlist_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
                    playlist_content += f'{stream_url}\n'
                    found_any_streams = True
                else:
                    print("  -> Gagal menemukan .m3u8 stream URL untuk pertandingan ini.")

            except TimeoutException:
                print("  -> Halaman terlalu lama dimuat, melewati pertandingan ini.")
            except Exception as e:
                print(f"  -> Terjadi error saat memproses pertandingan: {e}")
            finally:
                # Tutup tab pertandingan dan kembali ke tab utama
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print(f"Terjadi kesalahan besar pada proses utama: {e}")
    finally:
        driver.quit()
        print("\nProses scraper selesai.")

    if found_any_streams:
        with open(NAMA_FILE_PLAYLIST, "w", encoding="utf-8") as f:
            f.write(playlist_content)
        print(f"Playlist '{NAMA_FILE_PLAYLIST}' berhasil dibuat/diperbarui!")
    else:
        print("Sayang sekali, tidak ada satupun stream yang berhasil diekstrak hari ini.")

if __name__ == "__main__":
    create_playlist()
