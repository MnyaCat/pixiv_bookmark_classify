"""例外のモジュール"""


class BookmarkClassifyException(Exception):
    """基本例外クラス。"""
    pass


class RateLimited(BookmarkClassifyException):
    """pixivのAPIでレート制限が発生した場合に発生する例外。"""

    def __init__(self, illust_id: int) -> None:
        self.illust_id = illust_id

    def __str__(self) -> str:
        return f"レート制限が発生しました。 illust_id: {self.illust_id}"


class BookmarkDetailRateLimited(RateLimited):
    """ブックマークの詳細を取得するAPIで、レート制限が発生した場合に発生する例外。"""

    def __str__(self) -> str:
        return f"レート制限が発生したため、ブックマークを取得に失敗しました。 illust_id: {self.illust_id}"


class BookmarkAddRateLimited(RateLimited):
    """ブックマークを追加するAPIで、レート制限が発生した場合に発生する例外。"""

    def __str__(self) -> str:
        return f"レート制限が発生したため、ブックマークの追加に失敗しました。 illust_id: {self.illust_id}"


class BookmarkDeleteRateLimited(RateLimited):
    """ブックマークを削除するAPIで、レート制限が発生した場合に発生する例外。"""

    def __str__(self) -> str:
        return f"レート制限が発生したため、ブックマークの削除に失敗しました。 illust_id: {self.illust_id}"
