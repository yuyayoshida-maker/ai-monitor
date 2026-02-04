"""AI/LLMニュースモニタリングWebアプリ"""
from flask import Flask, render_template, request, jsonify
from news_client import fetch_all_news, NEWS_FEEDS
from translator import translate_text

app = Flask(__name__)


@app.route('/')
def index():
    """メインダッシュボード"""
    return render_template(
        'index.html',
        sources=list(NEWS_FEEDS.keys()),
    )


@app.route('/api/news')
def get_news():
    """ニュースAPIエンドポイント"""
    sources = request.args.getlist('sources')
    query = request.args.get('query', '').strip().lower()

    news = fetch_all_news(sources if sources else None)

    # キーワードフィルタ
    if query:
        news = [n for n in news if query in n.title.lower() or query in n.summary.lower()]

    result = []
    for n in news[:50]:
        # タイトルと要約を日本語に翻訳
        title_ja = translate_text(n.title)
        summary_ja = translate_text(n.summary)

        result.append({
            'title': title_ja,
            'title_original': n.title,
            'summary': summary_ja,
            'summary_original': n.summary,
            'url': n.url,
            'source': n.source,
            'published': n.published.strftime('%Y-%m-%d %H:%M') if n.published else None,
            'image_url': n.image_url,
        })

    return jsonify(result)


if __name__ == '__main__':
    print("🚀 AI Monitor starting at http://localhost:8080")
    app.run(debug=True, port=8080)
