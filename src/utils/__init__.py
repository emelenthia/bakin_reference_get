"""
ユーティリティモジュール

HTML解析、URL変換、その他の共通ユーティリティ機能を提供します。
"""

from .html_parser import (
    HTMLParser,
    parse_html,
    to_absolute_url,
    extract_links_from_html,
    clean_text
)

__all__ = [
    'HTMLParser',
    'parse_html',
    'to_absolute_url',
    'extract_links_from_html',
    'clean_text'
]