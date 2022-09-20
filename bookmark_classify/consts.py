RESTRICT_PUBLIC = "public"
RESTRICT_PRIVATE = "private"

"""
閲覧制限がかかっているかどうかは、`illust.image_urls.square_medium`で判別できる。
削除/非公開: `https://s.pximg.net/common/images/limit_unknown_360.png`
R-18: `https://s.pximg.net/common/images/limit_r18_360.png`
R-18G: `https://s.pximg.net/common/images/limit_r18g_360.png`
それ以外: サムネイルのリンク
"""

LIMIT_UNKNOWN = r"https://s.pximg.net/common/images/limit_unknown_360.png"
LIMIT_R18 = r"https://s.pximg.net/common/images/limit_r18_360.png"
LIMIT_R18G = r"https://s.pximg.net/common/images/limit_r18g_360.png"
LIMIT_AGE = (LIMIT_R18, LIMIT_R18G)
LIMITS = (LIMIT_UNKNOWN, LIMIT_R18, LIMIT_R18G)
