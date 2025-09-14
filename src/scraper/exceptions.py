"""
スクレイピング関連のカスタム例外クラス

より具体的なエラーハンドリングのためのカスタム例外を定義します。
"""


class ScrapingError(Exception):
    """スクレイピング処理中の一般的なエラー"""
    pass


class NetworkError(ScrapingError):
    """ネットワーク関連のエラー"""
    pass


class ParseError(ScrapingError):
    """HTML解析関連のエラー"""
    pass


class ValidationError(ScrapingError):
    """データ検証関連のエラー"""
    pass


class RateLimitError(NetworkError):
    """レート制限関連のエラー"""
    pass


class AuthenticationError(NetworkError):
    """認証関連のエラー"""
    pass