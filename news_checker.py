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

# Вместо файла используем память (для одного запуска)
sent_links_this_run = set()

def load_last_posts():
    """Загружаем историю из файла, но не полагаемся на нее полностью"""
    try:
        with open('last_post.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📖 Загружено {len(data)} записей из last_post.json")
            return data
    except:
        print("ℹ️ Файл last_post.json не найден или пуст")
        return {}

def save_last_posts(posts):
    """Сохраняем в файл (но не коммитим)"""
    try:
        with open('last_post.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено {len(posts)} записей в last_post.json")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

def send_to_discord(title, link, description, source):
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
        
        # Проверяем в памяти этого запуска
        if latest.link in sent_links_this_run:
            print(f"✅ Новость уже отправлена в этом запуске: {latest.title}")
            return False
            
        # Проверяем в сохраненной истории
        if last_posts.get(feed_key) == latest.link:
            print(f"✅ Новостей нет в {source_name}")
            return False
        
        print(f"📰 Найдена новая новость: {latest.title}")
        
        # Отправляем в Discord
        if send_to_discord(latest.title, latest.link, latest.summary, source_name):
            # Сохраняем в память этого запуска
            sent_links_this_run.add(latest.link)
            # Обновляем историю
            last_posts[feed_key] = latest.link
            print(f"✅ Отправлено в Discord: {latest.title}")
            return True
        else:
            print(f"❌ Ошибка отправки в Discord")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке {source_name}: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск проверки новостей Dota 2...")
    print(f"📝 DISCORD_WEBHOOK: {'✅ Настроен' if WEBHOOK_URL else '❌ Не настроен'}")
    
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
            print("💾 Данные о последних новостях сохранены (локально)")
        else:
            print("❌ Не удалось сохранить данные")
    else:
        print("ℹ️ Новых новостей не найдено")
    
    print(f"📊 Итог: найдено {len(sent_links_this_run)} новых новостей")
