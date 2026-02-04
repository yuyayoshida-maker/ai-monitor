"""arXiv API クライアント"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Paper:
    """論文データクラス"""
    id: str
    title: str
    summary: str
    authors: list[str]
    published: datetime
    updated: datetime
    categories: list[str]
    pdf_url: str
    arxiv_url: str


class ArxivClient:
    """arXiv API クライアント"""

    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACES = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }

    # AI/ML関連のカテゴリ
    AI_CATEGORIES = [
        'cs.AI',   # Artificial Intelligence
        'cs.CL',   # Computation and Language (NLP)
        'cs.LG',   # Machine Learning
        'cs.CV',   # Computer Vision
        'cs.NE',   # Neural and Evolutionary Computing
        'stat.ML', # Machine Learning (Statistics)
    ]

    def search(
        self,
        query: Optional[str] = None,
        categories: Optional[list[str]] = None,
        max_results: int = 50,
        sort_by: str = 'submittedDate',
        sort_order: str = 'descending'
    ) -> list[Paper]:
        """
        arXiv APIで論文を検索

        Args:
            query: 検索キーワード
            categories: カテゴリリスト（例: ['cs.AI', 'cs.CL']）
            max_results: 最大取得件数
            sort_by: ソート基準（submittedDate, lastUpdatedDate, relevance）
            sort_order: ソート順（ascending, descending）

        Returns:
            論文のリスト
        """
        # 検索クエリを構築
        search_parts = []

        if categories:
            cat_query = ' OR '.join(f'cat:{cat}' for cat in categories)
            search_parts.append(f'({cat_query})')
        else:
            # デフォルトでAI関連カテゴリを検索
            cat_query = ' OR '.join(f'cat:{cat}' for cat in self.AI_CATEGORIES)
            search_parts.append(f'({cat_query})')

        if query:
            # タイトルと要約で検索
            search_parts.append(f'(ti:"{query}" OR abs:"{query}")')

        search_query = ' AND '.join(search_parts)

        # APIパラメータ
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': sort_by,
            'sortOrder': sort_order,
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        # APIリクエスト
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_data = response.read().decode('utf-8')

        return self._parse_response(xml_data)

    def _parse_response(self, xml_data: str) -> list[Paper]:
        """XMLレスポンスをパース"""
        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall('atom:entry', self.NAMESPACES):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)

        return papers

    def _parse_entry(self, entry: ET.Element) -> Optional[Paper]:
        """エントリをPaperオブジェクトに変換"""
        try:
            # ID
            id_elem = entry.find('atom:id', self.NAMESPACES)
            arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None else ''

            # タイトル
            title_elem = entry.find('atom:title', self.NAMESPACES)
            title = ' '.join(title_elem.text.split()) if title_elem is not None else ''

            # 要約
            summary_elem = entry.find('atom:summary', self.NAMESPACES)
            summary = ' '.join(summary_elem.text.split()) if summary_elem is not None else ''

            # 著者
            authors = []
            for author in entry.findall('atom:author', self.NAMESPACES):
                name_elem = author.find('atom:name', self.NAMESPACES)
                if name_elem is not None:
                    authors.append(name_elem.text)

            # 日付
            published_elem = entry.find('atom:published', self.NAMESPACES)
            published = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00')) if published_elem is not None else datetime.now()

            updated_elem = entry.find('atom:updated', self.NAMESPACES)
            updated = datetime.fromisoformat(updated_elem.text.replace('Z', '+00:00')) if updated_elem is not None else datetime.now()

            # カテゴリ
            categories = []
            for category in entry.findall('atom:category', self.NAMESPACES):
                term = category.get('term')
                if term:
                    categories.append(term)

            # URL
            pdf_url = ''
            arxiv_url = ''
            for link in entry.findall('atom:link', self.NAMESPACES):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href', '')
                elif link.get('rel') == 'alternate':
                    arxiv_url = link.get('href', '')

            return Paper(
                id=arxiv_id,
                title=title,
                summary=summary,
                authors=authors,
                published=published,
                updated=updated,
                categories=categories,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url,
            )
        except Exception:
            return None


# キーワードプリセット
TRENDING_KEYWORDS = [
    'LLM',
    'Large Language Model',
    'GPT',
    'Transformer',
    'RLHF',
    'Chain of Thought',
    'RAG',
    'Retrieval Augmented',
    'Multimodal',
    'Vision Language',
    'Diffusion',
    'Agent',
    'Reasoning',
    'Fine-tuning',
    'Prompt',
]
