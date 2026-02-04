"""翻訳モジュール"""
from functools import lru_cache

try:
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source='auto', target='ja')
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
    translator = None


@lru_cache(maxsize=500)
def translate_text(text: str) -> str:
    """テキストを日本語に翻訳（キャッシュ付き）"""
    if not text or not text.strip() or not AVAILABLE:
        return text

    try:
        # 長すぎるテキストは分割
        if len(text) > 4500:
            text = text[:4500]
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text
