from flask import Flask, request, jsonify, render_template
import re
import time
import requests
from requests_html import HTMLSession

app = Flask(__name__, static_folder='static', template_folder='templates')
app.debug = False

# --- ÖNBELLEK MEKANİZMASI ---
CACHE_DURATION = 6 * 60 * 60  # 6 saat (saniye cinsinden)
last_fetched = 0
cached_words = set()
cached_names = set()
cached_common_passwords = set()

def fetch_online_data(url):
    try:
        response = requests.get(url, timeout=5)
        return response.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return []

def fetch_wiki_names(url):
    names = set()
    try:
        session = HTMLSession()
        wiki_page = session.get(url, timeout=10)
        tables = wiki_page.html.find('table.wikitable')
        for table in tables:
            for row in table.find('tr')[1:]:
                cells = row.find('td')
                if cells:
                    name = cells[0].text.strip().split()[0].lower()
                    names.add(name)
    except Exception as e:
        print(f"Error scraping names from {url}: {str(e)}")
    return names

def get_words():
    word_sources = [
        "https://raw.githubusercontent.com/maidis/mythes-tr/master/veriler/kelime-listesi.txt",
        "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
    ]
    words = set()
    for url in word_sources:
        words.update(fetch_online_data(url))
    return words

def get_names():
    name_sources = [
        "https://tr.wikipedia.org/wiki/T%C3%BCrkiye%27de_en_yayg%C4%B1n_isimler_listesi",
        "https://en.wikipedia.org/wiki/List_of_most_popular_given_names"
    ]
    names = set()
    for url in name_sources:
        names.update(fetch_wiki_names(url))
    return names

def get_common_passwords():
    return fetch_online_data("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt")

def refresh_data_if_needed():
    global last_fetched, cached_words, cached_names, cached_common_passwords
    now = time.time()
    if now - last_fetched > CACHE_DURATION or not cached_words:
        print("🔄 Veriler güncelleniyor...")
        cached_words = get_words()
        cached_names = get_names()
        cached_common_passwords = set(p.lower() for p in get_common_passwords())
        last_fetched = now
    else:
        print("✅ Önbellekten veri kullanılıyor.")

def calculate_time_to_crack(password):
    if password.lower() in cached_common_passwords:
        return "1 saniyeden az"
    
    if contains_word(password, cached_words) or contains_word(password, cached_names):
        return "birkaç dakika"
    
    charsets = {
        'lower': 26, 'upper': 26, 'digit': 10, 'special': 32
    }
    
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    charset_size = sum(size for use, size in zip(
        [has_lower, has_upper, has_digit, has_special],
        charsets.values()
    ) if use)

    if charset_size == 0:
        return "1 saniyeden az"

    combinations = charset_size ** len(password)
    cracking_speed = 1e9  # 1 milyar/s
    
    seconds = combinations / cracking_speed

    intervals = [
        (1, "saniyeden az"),
        (60, f"{int(seconds)} saniye"),
        (3600, f"{int(seconds/60)} dakika"),
        (86400, f"{int(seconds/3600)} saat"),
        (2592000, f"{int(seconds/86400)} gün"),
        (31536000, f"{int(seconds/2592000)} ay"),
        (float('inf'), f"{int(seconds/31536000)} yıl")
    ]
    
    for threshold, text in intervals:
        if seconds < threshold:
            return text

    return "yüzlerce yıl"

def contains_word(password, data, min_length=3):
    password_lower = password.lower()
    for word in data:
        if len(word) >= min_length and word.lower() in password_lower:
            return True
    return False

def check_password_strength(password):
    refresh_data_if_needed()

    issues = []
    length = len(password)
    checks = {
        'has_upper': any(c.isupper() for c in password),
        'has_lower': any(c.islower() for c in password),
        'has_number': any(c.isdigit() for c in password),
        'has_special': any(not c.isalnum() for c in password)
    }

    # Temel kontroller
    if length < 8:
        issues.append(f"Çok kısa ({length} karakter)")
    elif length < 12:
        issues.append("Daha uzun şifre kullanın")

    if not checks['has_upper']:
        issues.append("Büyük harf yok")
    if not checks['has_lower']:
        issues.append("Küçük harf yok")
    if not checks['has_number']:
        issues.append("Rakam yok")
    if not checks['has_special']:
        issues.append("Özel karakter yok")

    # Önemli güvenlik sorunları
    if password.lower() in cached_common_passwords:
        issues.append("Yaygın şifre (anında kırılır)")
    if contains_word(password, cached_words):
        issues.append("Sözlük kelimesi içeriyor")
    if contains_word(password, cached_names):
        issues.append("Yaygın isim içeriyor")

    # Desen kontrolleri
    if re.search(r'(.)\1{2,}', password):
        issues.append("Tekrar eden karakterler")
    if re.search(r'(abc|123|qwe|asd|zxc|987|321)', password.lower()):
        issues.append("Ardışık karakterler")

    # Puan hesaplama (0-100 arası)
    score = 0
    
    # Uzunluk puanı (0-30)
    score += min(length, 20) * 1.5
    
    # Karakter çeşitliliği puanı (0-40)
    score += sum(10 for check in checks.values() if check)
    
    # Özel karakter bonusu
    if checks['has_special']:
        score += 10
    
    # Ciddi sorunlar için büyük kesintiler
    if "Yaygın şifre" in issues:
        score = max(10, score * 0.3)
    elif "Sözlük kelimesi" in issues:
        score = max(20, score * 0.5)
    elif "Yaygın isim" in issues:
        score = max(30, score * 0.7)
    
    # Diğer sorunlar için küçük kesintiler
    if "Tekrar eden karakterler" in issues:
        score = max(0, score - 15)
    if "Ardışık karakterler" in issues:
        score = max(0, score - 10)

    # Güç seviyesi belirleme
    strength_levels = [
        (30, "ÇOK ZAYIF", "red"),
        (45, "ZAYIF", "orange"),
        (65, "ORTA", "yellow"),
        (80, "GÜÇLÜ", "lightgreen"),
        (float('inf'), "ÇOK GÜÇLÜ", "darkgreen")
    ]

    strength, color = next(((level, color) for threshold, level, color in strength_levels if score <= threshold))

    return {
        'score': min(100, int(score)),
        'strength': strength,
        'color': color,
        'length': length,
        **checks,
        'issues': issues,
        'time_to_crack': calculate_time_to_crack(password)
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return jsonify(check_password_strength(request.form.get('password', '')))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)