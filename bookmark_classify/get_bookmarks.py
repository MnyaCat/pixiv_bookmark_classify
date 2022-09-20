"""ユーザーのブックマークを取得するモジュール"""

import asyncio
from typing import List

from pixivpy_async import AppPixivAPI

from .utils import Illust, Restrict
from .consts import LIMIT_UNKNOWN, LIMIT_AGE

"""
閲覧制限がかかっているかどうかは、`illust.image_urls.square_medium`で判別できる。
削除/非公開: `https://s.pximg.net/common/images/limit_unknown_360.png`
R-18: `https://s.pximg.net/common/images/limit_r18_360.png`
R-18G: `https://s.pximg.net/common/images/limit_r18g_360.png`
それ以外: サムネイルのリンク
"""


def is_limit_unknown(illust: Illust):
    return illust.image_urls.square_medium == LIMIT_UNKNOWN


def is_limit_age(illust: Illust):
    return illust.image_urls.square_medium in LIMIT_AGE


async def get_all_bookmarks_illust(
    api: AppPixivAPI,
    user_id: int | str,
    restrict: Restrict = "public",
    tag: str | None = None,
    interval_seconds: int = 5
) -> List[Illust]:
    """指定されたユーザーのブックマークを全て取得します。
    `interval_seconds`の値が小さい場合、pixivからアクセスを制限される可能性があります。

    Args:
        api (AppPixivAPI): AppPixivAPIのインスタンス。
        user_id (int | str): ブックマークを取得するユーザーのID。
        restrict (Restrict): 取得するブックマークのプライバシー設定。 デフォルトは`"public"`です。
        tag (str | None): 絞り込むタグ。 指定したタグが付いたブックマークのみを取得できます。 デフォルトは`None`です。
        Interval_seconds (int, optional): 取得する間隔。 秒単位で指定してください。 デフォルトは`5`です。

    Returns:
        List[Illust]: ブックマークしているイラストの一覧。
    """
    bookmark_illusts = []
    next_qs = None

    while True:
        if next_qs is not None:
            json_result = await api.user_bookmarks_illust(**next_qs)
        else:
            json_result = await api.user_bookmarks_illust(user_id, restrict=restrict, tag=tag)
        illusts = json_result.illusts
        bookmark_illusts.extend(illusts)

        next_url = json_result.next_url
        if next_url is None:
            break
        next_qs = api.parse_qs(next_url)

        await asyncio.sleep(interval_seconds)

    return bookmark_illusts


def get_unknown_bookmarks_illust(
    illusts: List[Illust],
) -> List[Illust]:
    """`illusts`から、削除済みもしくは非公開のイラストを取得します。

    Args:。
        illusts (List[Illust]): イラストのリスト。

    Returns:
        List[Illust]: 削除済みもしくは非公開のイラストのリスト。
    """
    return [illust for illust in illusts if is_limit_unknown(illust)]


def get_limit_bookmarks_illust(
    illusts: List[Illust],
) -> List[Illust]:
    """`illusts`から、閲覧が制限されているイラストを取得します。
    ここでの「閲覧が制限されている」は、設定でR-18,R-18Gを「表示しない」に設定しているため、閲覧できないことを指します。

    Args:
        illusts (List[Illust]): イラストのリスト。

    Returns:
        List[Illust]: 閲覧が制限されているイラストのリスト。
    """
    return [illust for illust in illusts if is_limit_age(illust)]
