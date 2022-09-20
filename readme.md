# pixiv Bookmark Classify

pixivのブックマークに自動でタグを付けるスクリプト

## 使い方

### 事前準備

#### 1. リフレッシュトークンを取得する

[Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)を参考に、リフレッシュトークンを取得し、[`config.json`](config.json)内の`refresh_token`の値にセットしてください。

例: `"refresh_token": "pixiv_refresh_token"`

#### 2. 設定ファイルを編集する

[config.jsonの説明](#configjsonの説明)を参考に、[`config.json`](config.json)を編集してください。
設定したい項目が無い場合は、そのままで構いません。

#### 3. 閲覧制限を解除する

R-18,R-18Gを「表示しない」に設定している場合、ブックマークされたR-18,R-18Gのイラスト情報が取得できません。
`設定 > 閲覧制限 - 年齢制限作品`から、R-18,R-18Gを「表示する」に設定しておくことをおすすめします。

#### 4. ブロックを解除する

ブロックしたユーザーのイラストをブックマークしている場合、タグの追加ができずに処理がループしてしまいます。
前もってブロックを解除しておくか、ブロックしたユーザーのイラストのブックマークを解除しておくことをおすすめします。

### 実行

コマンドプロンプト、PowerShellなどで`main.py`を実行してください。
実行には、Python及び`requirements.txt`に記載されているライブラリが必要です。(requestsは[リフレッシュトークンを取得する](#1-リフレッシュトークンを取得する)際に必要です)

例:
`python main.py`

未分類のブックマークのみを整理する場合: `python main.py --only-uncategorized`
(ブックマークが増えたため)再取得して整理したい場合: `python main.py --get-bookmarks`

### config.jsonの説明

以下に、各Keyの説明を示します。

`refresh_token`: pixivのログインに必要リフレッシュトークン。
`progress_public`: 公開ブックマークの進捗。 システムが変更します。
`progress_private`: 非公開ブックマークの進捗。 システムが変更します。
`bookmarks_public`: 公開ブックマークのキャッシュのパス。 システムが変更します。
`bookmarks_private`: 非公開ブックマークのキャッシュのパス。 システムが変更します。
`exclude_tags`: ブックマークのタグから除外するワード。 いずれかのワードが含まれるタグはブックマークのタグに追加されません。(`users`を設定した場合、`オリジナル10000users`や`原神5000users`は追加されません。 また、既にブックマークに付けられている場合は外されません。) 部分一致で評価されます。
`private_tags`: ブックマークを非公開にするタグ。 指定したタグのいずれかが付けられているイラストは、非公開になります。 (`R-18`を設定した場合、`R-18`のタグが付いているイラストは非公開になります。) 完全一致で評価されます。
`preferred_tags`: イラスト自体のタグと、既にブックマークに付いているタグの合計が10を超えた場合、どちらのタグを優先して残すか。 `"illust`もしくは`bookmark`を指定してください。
`delete_tags`: ブックマークを解除するタグ。 指定したタグのいずれかが付けられているイラストは、ブックマークが解除されます。 完全一致で評価されます。
`delete_if_unknown`: 非公開/削除済みで閲覧できないイラストのブックマークを解除するか。

例:
`users`と`寒いタグ芸`を除外、`R-18`と`R-18G`を非公開に、イラストのタグを優先、`地雷タグ`を解除したい場合は、次のように設定してください。

```json
{
    "refresh_token": "",
    "progress_public": -1,
    "progress_private": -1,
    "bookmarks_public": null,
    "bookmarks_private": null,
    "exclude_tags": ["users", "寒いタグ芸"],
    "private_tags": ["R-18", "R-18G"],
    "preferred_tags": "illust",
    "delete_tags": ["地雷タグ"],
    "delete_if_unknown": false
}
```

## 注意事項

`pixivpy-async`は非公式のAPIラッパーです。
本スクリプトを実行することで以下の事が起こる可能性があります。注意の上、自己責任で使用してください。

- pixivからアクセスを制限される
- pixivのアカウントが予告無く停止される
- 実行した端末やネットワークで、一時的にreCHAPTCHAの認証ができなくなる

ソースコードを編集する際は、pixivへアクセスする頻度にご注意ください。
Pythonの知識が無い場合は、ソースコードを編集しないことをおすすめします。

本スクリプトではアプリ版pixivのAPIを使用しているため、ブックマークされているイラスト全てに「いいね」が付きます。

## LICENSE

This software is released under the MIT License, see [LICENSE](LICENSE).

ja: 本ソフトウェアはMITライセンスのもとで公開されています。詳細は[LICENSE](LICENSE)を確認してください。

[MIT LICENSE 日本語訳](https://licenses.opensource.jp/MIT/MIT.html)
実際に適応されるのは英語の原文となります。ご注意ください。
