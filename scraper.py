import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os

# URL Halaman Jadwal
URL = "https://kilatlive.live/schedules"
NAMA_FILE_PLAYLIST = "jadwal_kilatlive.m3u"

def scrap_jadwal_dan_buat_playlist():
    print("Memulai proses scraping di server...")

    # Pengaturan Selenium untuk berjalan di server Linux (seperti di GitHub Actions)
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Wajib, karena tidak ada layar
    chrome_options.add_argument("--no-sandbox") # Wajib untuk lingkungan Linux
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Inisialisasi driver
    try:
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error saat inisialisasi WebDriver: {e}")
        # Mencoba tanpa path eksplisit jika chromedriver ada di PATH
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            print(f"Error kedua saat inisialisasi WebDriver: {e2}")
            return

    try:
        driver.get(URL)
        print("Halaman diakses. Menunggu konten dimuat...")
        # Waktu tunggu yang lebih lama mungkin diperlukan di server
        time.sleep(15) 

        page_source = driver.page_source
        
        # Di sini kita tidak menggunakan BeautifulSoup untuk menjaga dependensi tetap minimal
        # Kita gunakan Selenium langsung untuk mencari elemen
        
        # Selector CSS yang sudah dikoreksi berdasarkan inspeksi terbaru
        # Mencari tag <a> yang merupakan anak langsung dari div di dalam div#match-schedule-wrapper
        matches = driver.find_elements(By.CSS_SELECTOR, "div#match-schedule-wrapper > div > a")

        if not matches:
            print("Tidak ada jadwal ditemukan. Selector CSS mungkin perlu diperbarui atau halaman gagal dimuat.")
            return

        print(f"Ditemukan {len(matches)} jadwal pertandingan.")
        
        playlist_content = "#EXTM3U\n"
        for match in matches:
            try:
                link_stream = match.get_attribute('href')
                # Mencari teks dari semua span di dalam link
                spans = match.find_elements(By.TAG_NAME, 'span')
                if len(spans) > 2:
                    waktu = spans[0].text.strip()
                    tim_a = spans[1].text.strip()
                    tim_b = spans[2].text.strip()
                    nama_channel = f"{waktu} - {tim_a} vs {tim_b}"
                else:
                    nama_channel = match.text.strip().replace('\n', ' ')

                if link_stream and nama_channel:
                    playlist_content += f"#EXTINF:-1, {nama_channel}\n"
                    playlist_content += f"{link_stream}\n"
            except Exception as e:
                print(f"Gagal memproses satu jadwal: {e}")
                continue

        with open(NAMA_FILE_PLAYLIST, "w", encoding="utf-8") as f:
            f.write(playlist_content)

        print(f"\nPlaylist '{NAMA_FILE_PLAYLIST}' berhasil dibuat/diperbarui!")

    except Exception as e:
        print(f"Terjadi kesalahan saat proses scraping: {e}")
    finally:
        driver.quit()
        print("Proses selesai.")

if __name__ == "__main__":
    scrap_jadwal_dan_buat_playlist()
