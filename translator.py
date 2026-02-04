"""翻訳モジュール"""
from googletrans import Translator
from functools import lru_cache
import hashlib

translator = Translator()


@lru_cache(maxsize=500)
def translate_text(text: str, dest: str = 'ja') -> str:
    """
    テキストを日本語に翻訳（キャッシュ付き）

    Args:
        text: 翻訳するテキスト
        dest: 翻訳先言語（デフォルト: 日本語）

    Returns:
        翻訳されたテキスト
    """
    if not text or not text.strip():
        return text

    # 既に日本語の場合はそのまま返す
    try:
        detected = translator.detect(text)
        if detected.lang == 'ja':
            return text
    except:
        pass

    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def translate_news_item(title: str, summary: str) -> tuple[str, str]:
    """
    ニュース記事のタイトルと要約を翻訳

    Returns:
        (翻訳されたタイトル, 翻訳された要約)
    """
    translated_title = translate_text(title)
    translated_summary = translate_text(summary)
    return translated_title, translated_summary
