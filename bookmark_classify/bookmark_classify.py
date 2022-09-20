"""ブックマークを整理するモジュール"""

import asyncio
from typing import Awaitable, Callable, List

from pixivpy_async import AppPixivAPI

from .consts import RESTRICT_PRIVATE
from .exceptions import (BookmarkAddRateLimited, BookmarkDeleteRateLimited,
                         BookmarkDetailRateLimited, RateLimited)
from .get_bookmarks import is_limit_unknown
from .utils import BookmarkDetail, BookmarkTag, Illust, IllustTag, PreferredTag
from .consts import LIMITS

TAGS_LIMIT = 10


async def bookmark_classify_on_ratelimited(
    index: int,
    illust: Illust,
    exception: RateLimited
) -> None:
    print("レート制限が発生したため、10分間sleepします...")
    await asyncio.sleep(600)
    return


def in_partial_match(tag: str, tags: List[str]) -> bool:
    """`tag`と部分的に一致するアイテムが`tags`に含まれているかを調べます。

    Args:
        tag (str): 評価するタグ。
        tags (List[str]): タグのリスト。

    Returns:
        bool: `tag`と部分的に一致するアイテムが`tags`に含まれているか。
    """
    return len([t for t in tags if t in tag]) > 0


def in_exact_match(tag: str, tags: List[str]) -> bool:
    """`tag`と完全に一致するアイテムが`tags`に含まれているかを調べます。

    Args:
        tag (str): 評価するタグ。
        tags (List[str]): タグのリスト。

    Returns:
        bool: `tag`と完全に一致するアイテムが`tags`に含まれているか。
    """
    return len([t for t in tags if t == tag]) > 0


def get_tag_names(tags: List[IllustTag]) -> List[str]:
    """`illust_detail.tags`を、タグ名のListに変換します。

    Args:
        tags (List[IllustTag]): IllustTagのリスト。

    Returns:
        List[str]: タグ名のリスト。
    """
    return list(map(lambda tag: tag.name, tags))


def get_bookmark_tag_names(tags: List[BookmarkTag]) -> List[str]:
    """`bookmark_detail.tags`を、ブックマークのタグだけに絞り込み、タグ名のListに変換します。

    Args:
        tags (List[BookmarkTag]): BookmarkTagのリスト。

    Returns:
        List[str]: タグ名のリスト。
    """
    bookmark_tags = [tag for tag in tags if tag.is_registered]
    return get_tag_names(bookmark_tags)


async def bookmark_delete(
    api: AppPixivAPI,
    illust_id: int
) -> BookmarkDetail:
    """指定したイラストをブックマークから削除します。

    Args:
        api (AppPixivAPI): AppPixivAPIのインスタンス。
        illust_id (int): イラストのID。

    Raises:
        BookmarkDeleteRateLimited: ブックマークを削除するAPIで、レート制限が発生した場合に発生する例外。

    Returns:
        BookmarkDetail: 削除後のブックマークの詳細情報。
    """
    await api.illust_bookmark_delete(illust_id)

    json_result = await api.illust_bookmark_detail(illust_id)
    bookmark_detail = json_result.bookmark_detail

    if bookmark_detail.is_bookmarked:
        raise BookmarkDeleteRateLimited(illust_id)

    return bookmark_detail


async def bookmark_edit_if_needed(
    api: AppPixivAPI,
    illust: Illust,
    exclude_tags: List[str] | None = None,
    private_tags: List[str] | None = None,
    preferred_tags: PreferredTag = "bookmark",
) -> BookmarkDetail:
    """ブックマークのタグ、プライバシーを編集します。

    Args:
        api (AppPixivAPI): AppPixivAPIのインスタンス。
        illust (Illust): ブックマークに追加するイラスト。
        exclude_tags (List[str] | None, optional): 除外対象のタグのリスト。 指定したタグは、ブックマークのタグに追加されません。
        部分一致で評価されます。 デフォルトは`None`です。
        private_tags (List[str] | None, optional): 非公開対象のタグのリスト。
        指定したタグがイラストに付いている場合、ブックマークが非公開になります。 完全一致で評価されます。 デフォルトは`None`です。
        preferred_tags (PreferredTag, optional): イラストのタグとブックマークのタグを結合する際、どちらを優先して残すか。
        優先しないタグは、切り捨てられる可能性があります。 デフォルトは`bookmark`です。

    Raises:
        BookmarkDetailRateLimited: ブックマークの詳細を取得するAPIで、レート制限が発生した場合に発生する例外。
        BookmarkAddRateLimited: ブックマークを追加するAPIで、レート制限が発生した場合に発生する例外。

    Returns:
        BookmarkDetail: 編集後のブックマークの詳細情報。
    """

    # 閲覧制限がかかっている場合はスキップ
    if illust.image_urls.square_medium in LIMITS:
        return

    json_result = await api.illust_bookmark_detail(illust.id)
    before_bookmark_detail = json_result.bookmark_detail

    if before_bookmark_detail is None:
        raise BookmarkDetailRateLimited(illust.id)

    raw_illust_tags = get_tag_names(illust.tags)

    if exclude_tags:
        illust_tags = [tag for tag in raw_illust_tags if not in_partial_match(tag, exclude_tags)]
    else:
        illust_tags = raw_illust_tags

    before_bookmark_tags = get_bookmark_tag_names(before_bookmark_detail.tags)

    if 0 < len(before_bookmark_tags):
        # ブックマークのタグが、追加するタグをすべて含んでいる場合は終了
        if set(before_bookmark_tags).issuperset(set(illust_tags)):
            return

        tags = list(set(before_bookmark_tags).union(set(illust_tags)))

        if 10 < len(tags):
            match preferred_tags:
                case "illust":
                    add_tags = illust_tags + before_bookmark_tags[:TAGS_LIMIT - len(illust_tags)]
                case _:
                    add_tags = before_bookmark_tags + \
                        illust_tags[:TAGS_LIMIT - len(before_bookmark_tags)]
        else:
            add_tags = tags
    else:
        add_tags = illust_tags

    # タグの文字数を20文字以内にする -> 重複を消す
    add_tags = list(set(map(lambda tag: tag[:20], add_tags)))

    # プライバシー
    if (private_tags) and \
       (len([tag for tag in raw_illust_tags if in_exact_match(tag, private_tags)]) > 0):
        restrict = RESTRICT_PRIVATE
    else:
        restrict = before_bookmark_detail.restrict

    await api.illust_bookmark_add(
        illust.id,
        restrict=restrict,
        tags=[" ".join(add_tags)]
    )

    json_result = await api.illust_bookmark_detail(illust.id)
    after_bookmark_detail = json_result.bookmark_detail
    if after_bookmark_detail is None:
        raise BookmarkDetailRateLimited(illust.id)

    after_bookmark_tags = get_bookmark_tag_names(
        after_bookmark_detail.tags)

    if set(add_tags) != set(after_bookmark_tags):
        raise BookmarkAddRateLimited(illust.id)

    return after_bookmark_detail


async def bookmarks_classify(
    api: AppPixivAPI,
    illusts: List[Illust],
    exclude_tags: List[str] | None = None,
    private_tags: List[str] | None = None,
    preferred_tags: PreferredTag = "bookmark",
    delete_tags: List[str] | None = None,
    delete_if_unknown: bool = False,
    interval_seconds: int = 5,
    on_success: Callable[[int, Illust], Awaitable[None]] | None = None,
    # TODO: bookmark_add_tag_if_neededで、スキップした場合に例外を投げるようにしたとき用
    # on_skipped: Callable[[int, Illust], Awaitable[None]] | None = None,
    on_ratelimited: Callable[[int, Illust, RateLimited],
                             Awaitable[None]] | None = bookmark_classify_on_ratelimited,
    retry_if_ratelimited: bool = True
) -> None:
    """illustsのブックマークタグに、イラストのタグを追加します。
    `delete_if_unknown`が`True`の場合、非公開もしくは削除済みのイラストはブックマークが解除されます。
    `delete_tags`のいずれかがタグに含まれているイラストは、ブックマークが解除されます。

    `interval_seconds`の値が小さい場合、pixivからアクセスを制限される可能性があります。
    `on_ratelimited`には、5~10分間処理を止める関数を渡すことをおすすめします。

    Args:
        api, illusts, exclude_tags, private_tags, preferred_tagsについては、
        `bookmark_add_tag_if_needed`を参照してください。

        delete_tags (List[str] | None, optional): 削除対象のタグ。 指定したタグがイラストに付いている場合、ブックマークが解除されます。
        デフォルトはNoneです。
        delete_if_unknown (bool): 非公開もしくは削除済みのイラストのブックマークを解除するか。 デフォルトは`False`です。
        interval_seconds (int, optional): 取得する間隔。  秒単位で指定してください。  デフォルトは`5`です。
        on_success (Callable[[int, Illust], None] | None, optional): 各イラストへの処理が成功した場合に呼び出される非同期関数。
        引数はイラストのインデックス、処理を行ったイラストです。 デフォルトは`None`です。
        on_ratelimited (Callable[[int, Illust, RateLimited], None] | None, optional):
        処理の最中に例外`RateLimited`が発生した場合に呼び出される非同期関数。
        引数はイラストのインデックス、処理に失敗したイラスト、例外情報です。
        デフォルトは`bookmark_classify_on_ratelimited`(10分間処理を止める関数)です。
        retry_if_ratelimited (bool): 例外`RateLimited`が発生した場合、処理をリトライするか。 デフォルトは`True`です。
    """

    async def _bookmark_classify(index, illust):
        """for文内で使う関数。"""
        raw_illust_tags = get_tag_names(illust.tags)

        # 非公開/削除済みか, 削除対象の場合はフラグをTrueに
        if (delete_if_unknown and is_limit_unknown(illust)) or \
           ((delete_tags) and
           len([tag for tag in raw_illust_tags if in_exact_match(tag, delete_tags)]) > 0):
            should_delete = True
        else:
            should_delete = False

        try:
            if should_delete:
                await bookmark_delete(api, illust.id)
            else:
                await bookmark_edit_if_needed(
                    api,
                    illust,
                    exclude_tags,
                    private_tags,
                    preferred_tags
                )
        except RateLimited as e:
            if on_ratelimited is not None:
                await on_ratelimited(index, illust, e)
            if retry_if_ratelimited:
                await _bookmark_classify(index, illust)
        else:
            if on_success is not None:
                await on_success(index, illust)
        finally:
            await asyncio.sleep(interval_seconds)

    for index, illust in enumerate(illusts):
        await _bookmark_classify(index, illust)
        continue
