import argparse
import asyncio
import json
import sys
from typing import List
from datetime import datetime
import pathlib

from pixivpy_async import AppPixivAPI
from pixivpy_async.utils import JsonDict

from bookmark_classify import consts, get_bookmarks, bookmark_classify
from bookmark_classify.utils import print_override

config_path = "config.json"
RESTRICT_ALL = "all"

BOOKMARKS_PUBLIC_PATH = "bookmarks_public.json"
BOOKMARKS_PRIVATE_PATH = "bookmarks_private.json"

parser = argparse.ArgumentParser(description="ブックマークを整理します。")
parser.add_argument("-r", "--restrict", default=RESTRICT_ALL,
                    choices=[RESTRICT_ALL, consts.RESTRICT_PUBLIC, consts.RESTRICT_PRIVATE],
                    help="整理するブックマークのプライバシー設定を指定します。"
                    "'public'の場合は公開、'private'の場合は非公開、'all'の場合は両方が対象になります。"
                    "デフォルトは`%(default)s`です。")
parser.add_argument("-ou", "--only-uncategorized", action="store_true",
                    help="未分類のみを対象にするかを指定します。このオプションはフラグです。")
parser.add_argument("-gb", "--get-bookmarks", action="store_true",
                    help="キャッシュの有無に関わらず、ブックマークを取得するかを指定します。このオプションはフラグです。")
parser.add_argument("-cp", "--config-path", default=config_path, type=pathlib.Path,
                    help="configファイルのパスを指定します。指定しない場合、`%(default)s`から読み込まれます。")


class Config():
    def __init__(
        self,
        refresh_token: str,
        progress_public: int,
        progress_private: int,
        bookmarks_public: str,
        bookmarks_private: str,
        exclude_tags: List[str],
        private_tags: List[str],
        preferred_tags: str,
        delete_tags: List[str],
        delete_if_unknown: bool
    ) -> None:
        self.refresh_token = refresh_token or ""
        self.progress_public = progress_public or -1
        self.progress_private = progress_private or -1
        self.bookmarks_public = bookmarks_public
        self.bookmarks_private = bookmarks_private
        self.exclude_tags = exclude_tags
        self.private_tags = private_tags
        self.preferred_tags = preferred_tags or "bookmark"
        self.delete_tags = delete_tags
        self.delete_if_unknown = delete_if_unknown or False

        if self.progress_public < 0:
            self.progress_public = -1
        if self.progress_private < 0:
            self.progress_private = -1

    @staticmethod
    def from_jsonfile() -> "Config":
        with open(config_path, "r", encoding="utf-8") as f:
            config: "Config" = json.load(f, object_hook=lambda x: Config(**x))
            return config

    def to_jsonfile(self) -> None:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=4)


async def classify(api: AppPixivAPI, config: Config, args):

    if args.only_uncategorized:
        bookmark_tag = "未分類"
    else:
        bookmark_tag = None

    async def _classify(restrict):
        if restrict == consts.RESTRICT_PRIVATE:
            cache_path = config.bookmarks_private
            new_cache_path = BOOKMARKS_PRIVATE_PATH
            progress = config.progress_private
        else:
            cache_path = config.bookmarks_public
            new_cache_path = BOOKMARKS_PUBLIC_PATH
            progress = config.progress_public

        if not args.get_bookmarks and cache_path:
            try:
                print_override("ブックマークのキャッシュを読み込み中です...")
                with open(cache_path, "r", encoding="utf-8") as f:
                    bookmarks = json.load(f, object_hook=JsonDict)
                    should_get_bookmarks = False
            except Exception:
                should_get_bookmarks = True
            else:
                print_override("ブックマークのキャッシュを読み込みました。")
        else:
            should_get_bookmarks = True

        if should_get_bookmarks:
            if args.get_bookmarks:
                print_override("--get-bookmarksフラグが有効なため、ブックマークを取得しています...")
            else:
                print_override("ブックマークのキャッシュが読み込めなかったため、取得しています...")
            bookmarks = await get_bookmarks.get_all_bookmarks_illust(
                api,
                api.user_id,
                restrict, bookmark_tag)
            with open(new_cache_path, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, ensure_ascii=False, indent=4)

            if restrict == consts.RESTRICT_PRIVATE:
                config.bookmarks_private = new_cache_path
                config.progress_private = -1
            else:
                config.bookmarks_public = new_cache_path
                config.progress_public = -1

        bookmarks.reverse()
        bookmarks = bookmarks[progress + 1:]

        config.to_jsonfile()
        print_override("ブックマークを取得しました。")

        bookmarks_len = len(bookmarks)

        async def on_success(index, _):
            if restrict == consts.RESTRICT_PRIVATE:
                config.progress_private = progress + 1 + index
            else:
                config.progress_public = progress + 1 + index
            print_override(f"進捗: {restrict} - {index + 1} / {bookmarks_len}")

        async def on_ratelimited(index, illust, ratelimited):
            config.to_jsonfile()
            t_now = datetime.now().time()
            print_override(f"{ratelimited} date: {t_now}")
            await asyncio.sleep(600)

        await bookmark_classify.bookmarks_classify(
            api,
            bookmarks,
            config.exclude_tags,
            config.private_tags,
            config.preferred_tags,
            config.delete_tags,
            config.delete_if_unknown,
            on_success=on_success,
            on_ratelimited=on_ratelimited
            )

        config.to_jsonfile()
        print_override(f"進捗: {restrict} - 終了")

    if args.restrict in (RESTRICT_ALL, consts.RESTRICT_PUBLIC):
        await _classify(consts.RESTRICT_PUBLIC)
    if args.restrict in (RESTRICT_ALL, consts.RESTRICT_PRIVATE):
        await _classify(consts.RESTRICT_PRIVATE)

    config.to_jsonfile()
    print_override("ブックマークの整理が終了しました。")


async def _login(api: AppPixivAPI, config: Config):
    try:
        await api.login(refresh_token=config.refresh_token)
    except Exception as e:
        print_override("ログインできませんでした。リフレッシュトークンが正しいか確認してください。")
        print("\n例外情報を以下に示します。:")
        print(e)
        sys.exit(1)


async def _main(api: AppPixivAPI, config: Config, args):
    print_override("ログイン中...")
    await _login(api, config)
    print_override("ログインが完了しました。")
    await asyncio.gather(classify(api, config, args))


def main(args):
    if args.config_path:
        global config_path
        config_path = args.config_path

    try:
        print("config.jsonを読み込んでいます...", end="")
        config = Config.from_jsonfile()
        asyncio.run(_main(AppPixivAPI(), config, args))
    except KeyboardInterrupt:
        config.to_jsonfile()
        print(
            "\n進捗を保存し、処理を中断しました\n進捗:\n"
            f"公開 - {config.progress_public + 1}\n"
            f"非公開- {config.progress_private + 1}")
        sys.exit(0)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
