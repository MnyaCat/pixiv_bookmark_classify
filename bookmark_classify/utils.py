"""
Example
    型エイリアスの説明兼サンプルです。

    ::

        api = AppPixivAPI()

        illust_id = 0000

        json_result = await api.illust_detail(illust_id)
        illust: Illust = json_result.illust

        illust_tag = illust.tags[0]

        json_result = await api.illust_bookmark_detail(illust_id)
        bookmark_detail = json_result.bookmark_detail

        bookmark_tag: BookmarkTag = bookmark_detail.tags[0]

        restrict_public: Restrict = "public"
        restrict_private: Restrict = "private"
"""

from typing import Any, Literal

Illust = Any
IllustTag = Any
BookmarkTag = Any
BookmarkDetail = Any
Restrict = Literal["public", "private"]
PreferredTag = Literal["illust", "bookmark"]


def print_override(string: str) -> None:
    """カーソルを行の先頭に戻し、それより後ろを消去した後、`strings`を出力します。

    Args:
        string (str): コンソールに表示する文字列
    """
    print("\r\033[J" + string, end="")
