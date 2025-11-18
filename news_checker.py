import requests
import feedparser
import os
import json
from datetime import datetime

WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK')
RSS_URLS = [
    "https://store.steampowered.com/feeds/news/app/570/",
    "https://steamcommunity.com/games/570/rss/"
]

def load_last_posts():
    try:
        with open('last_post.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        print("ℹ️ Файл last_post.json не найден, создаем новый")
        return {}

def save_last_posts(posts):
    try:
        with open('last_post.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("💾 Файл last_post.json сохранен")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")
        return False

def send_to_discord(title, link, description, source):
    # Проверяем наличие вебхука
    if not WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK не настроен")
        return False
        
    # Очищаем описание от HTML тегов
    clean_description = description
    if '<' in description and '>' in description:
        import re
        clean_description = re.sub('<[^<]+?>', '', description)
    
    embed = {
        "title": title[:256],
        "url": link,
        "description": clean_description[:500] + "..." if len(clean_description) > 500 else clean_description,
        "color": 10181046,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"Dota 2 News • {source}"},
        "thumbnail": {
            "url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota2_social.jpg"
        }
    }
    
    data = {
        "embeds": [embed],
        "username": "Dota 2 Updates"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print("✅ Сообщение отправлено в Discord")
            return True
        else:
            print(f"❌ Ошибка Discord: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки в Discord: {e}")
        return False

def check_rss_feed(url, source_name, last_posts):
    try:
        print(f"🔍 Проверяем {source_name}...")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            print(f"❌ Нет записей в {source_name}")
            return False
        
        latest = feed.entries[0]
        feed_key = f"{source_name}_{latest.link}"
        
        # Проверяем, не отправляли ли уже эту новость
        if last_posts.get(feed_key) == latest.link:
            print(f"✅ Новостей нет в {source_name}")
            return False
        
        print(f"📰 Найдена новая новость: {latest.title}")
        
        # Отправляем в Discord
        if send_to_discord(latest.title, latest.link, latest.summary, source_name):
            # Сохраняем информацию о последней новости
            last_posts[feed_key] = latest.link
            print(f"✅ Отправлено в Discord: {latest.title}")
            return True
        else:
            print(f"❌ Ошибка отправки в Discord")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке {source_name}: {e}")
        return False

def create_initial_last_post():
    """Создает начальный файл last_post.json если его нет"""
    if not os.path.exists('last_post.json'):
        initial_data = {"initial": "start"}
        save_last_posts(initial_data)
        print("📄 Создан начальный файл last_post.json")

if __name__ == "__main__":
    print("🚀 Запуск проверки новостей Dota 2...")
    print(f"📝 DISCORD_WEBHOOK: {'✅ Настроен' if WEBHOOK_URL else '❌ Не настроен'}")
    
    # Создаем начальный файл если его нет
    create_initial_last_post()
    
    last_posts = load_last_posts()
    new_news_found = False
    
    # Проверяем официальные новости Steam
    if check_rss_feed(RSS_URLS[0], "Steam News", last_posts):
        new_news_found = True
    
    # Проверяем сообщество Steam
    if check_rss_feed(RSS_URLS[1], "Steam Community", last_posts):
        new_news_found = True
    
    if new_news_found:
        if save_last_posts(last_posts):
            print("💾 Данные о последних новостях сохранены")
        else:
            print("❌ Не удалось сохранить данные")
    else:
        print("ℹ️ Новых новостей не найдено")
        # Все равно сохраняем текущее состояние (на случай первой инициализации)
        save_last_posts(last_posts)
