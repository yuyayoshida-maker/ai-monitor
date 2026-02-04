"""AI/LLMニュースRSSクライアント"""
import feedparser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import re
import html


@dataclass
class NewsItem:
    """ニュース記事データ"""
    title: str
    summary: str
    url: str
    source: str
    published: Optional[datetime]
    image_url: Optional[str]


# AI関連のRSSフィード
NEWS_FEEDS = {
    'TechCrunch AI': 'https://techcrunch.com/category/artificial-intelligence/feed/',
    'The Verge AI': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
    'Wired AI': 'https://www.wired.com/feed/tag/ai/latest/rss',
    'Ars Technica AI': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
    'VentureBeat AI': 'https://venturebeat.com/category/ai/feed/',
    'MIT Tech Review AI': 'https://www.technologyreview.com/feed/',
}

# AIキーワード（フィルタリング用）
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'ml',
    'llm', 'large language model', 'gpt', 'chatgpt', 'claude',
    'gemini', 'openai', 'anthropic', 'deepmind', 'google ai',
    'neural', 'deep learning', 'transformer', 'diffusion',
    'generative', 'copilot', 'midjourney', 'stable diffusion',
    'agent', 'rag', 'embedding', 'fine-tuning', 'prompt',
]


def clean_html(text: str) -> str:
    """HTMLタグを除去"""
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_image(entry) -> Optional[str]:
    """記事から画像URLを抽出"""
    # media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('url', '').endswith(('.jpg', '.png', '.webp')):
                return media.get('url')

    # media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')

    # enclosure
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                return enc.get('href')

    # content内の画像
    content = ''
    if hasattr(entry, 'content') and entry.content:
        content = entry.content[0].get('value', '')
    elif hasattr(entry, 'summary'):
        content = entry.summary or ''

    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if img_match:
        return img_match.group(1)

    return None


def parse_date(entry) -> Optional[datetime]:
    """日付をパース"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except:
            pass
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except:
            pass
    return None


def is_ai_related(title: str, summary: str) -> bool:
    """AI関連の記事かどうか判定"""
    text = (title + ' ' + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def fetch_feed(name: str, url: str) -> list[NewsItem]:
    """単一フィードを取得"""
    try:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries[:20]:
            title = clean_html(entry.get('title', ''))
            summary = clean_html(entry.get('summary', entry.get('description', '')))

            # AI関連でない記事はスキップ（一部のフィードはAI専用でないため）
            if 'AI' not in name and not is_ai_related(title, summary):
                continue

            items.append(NewsItem(
                title=title,
                summary=summary[:300] + '...' if len(summary) > 300 else summary,
                url=entry.get('link', ''),
                source=name,
                published=parse_date(entry),
                image_url=extract_image(entry),
            ))

        return items
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []


def fetch_all_news(sources: Optional[list[str]] = None) -> list[NewsItem]:
    """全フィードからニュースを取得"""
    feeds_to_fetch = {k: v for k, v in NEWS_FEEDS.items() if not sources or k in sources}

    all_items = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_feed, name, url) for name, url in feeds_to_fetch.items()]
        for future in futures:
            all_items.extend(future.result())

    # 日付でソート（新しい順）
    all_items.sort(key=lambda x: x.published or datetime.min, reverse=True)

    return all_items
