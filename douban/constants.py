from enum import Enum


class MediaType(Enum):
    """
    豆瓣三大类：影音书
    """
    BOOK = "book"
    MOVIE = "movie"
    MUSIC = "music"


class MediaStatus(Enum):
    """
    个人影音书的标记状态
    """
    DO = "do"
    WISH = "wish"
    COLLECT = "collect"


class MediaInfo(Enum):
    """
    媒体信息
    """
    # 通用 默认为字符串str, 后面加_F则为float型
    # 评分 个人评分 简介 短评
    TITLE = "title"                     # 媒体名称
    STATUS = "status"                   # 标记
    STATUS_DATE = "status_date"         # 标记日期
    IMG = "img"                         # 封面、海报
    URL = "url"                         # 链接
    TAG_LIST = "tag_list"               # 标签
    RATING_F = "rating"                 # 评分
    ASSESS = 'assess'                   # 评价数
    RELATED = "related_infos"

    # 书籍
    AUTHOR = "author"                   # 作者
    PUBLISHER = "publisher"             # 出版社
    PUB_DATE = "pub_date"               # 出版日期
    PRICE = "price"                     # 价格
    ISBN = 'isbn'                       # ISBN
    SUBHEAD = 'book_subhead'            # 副标题
    PAGES = 'pages'                     # 页数

    # 音乐
    PERFORMER = "performer"             # 表演者
    GENRE = "genre"                     # 流派
    ALBUM_TYPE = "album_type"           # 专辑类型
    MEDIUM = "medium"                   # 介质
    RELEASE_DATE = "release_date"       # 发行时间
    MUSIC_PUB = "music_pub"             # 出版者
    ISRC = "isrc"                       # 条形码

    # 电影
    DIRECTOR = "director"
    SCREENWRITER = "screenwriter"
    STARRING = "starring"
    MOVIE_TYPE = "movie_type"
    C_OR_R = "country_or_region"
    LANGUAGE = "language"
    CATEGORIES = "Categories"
    IMDB = "IMDb"


class DoubanRexxarURL(Enum):
    TIMELINE = "https://m.douban.com/rexxar/api/v2/status/user_timeline/{uid}?max_id={maxId}&ck={ck}&for_mobile=1"
    STATUS = "https://m.douban.com/rexxar/api/v2/status/{id}?ck={ck}&for_mobile=1"
    INTERESTS = "https://m.douban.com/rexxar/api/v2/user/{uid}/interests?type={type}&status={status}&start={start}&count={count}&ck={ck}&for_mobile=1"
    INTERESTS_TOTAL = "https://m.douban.com/rexxar/api/v2/user/{uid}/interests?ck={ck}&count=1&for_mobile=1"
    ANNOTATIONS = "https://m.douban.com/rexxar/api/v2/user/{uid}/annotations?start={start}&count={count}&ck={ck}&for_mobile=1"
    REVIEWS = "https://m.douban.com/rexxar/api/v2/user/{uid}/reviews?type={type}&start={start}&count={count}&ck={ck}&for_mobile=1"

    def format(self, **kwargs):
        return self.value.format(**kwargs)


class MediaXpathParam(Enum):
    """
    提取html的参数
    """
    # 书籍详情页获取信息
    B_NAME = '//span[@property="v:itemreviewed"]/text()'
    B_RATING_NUM = '//strong[@class="ll rating_num "][@property="v:average"]/text()'
    B_AUTHOR = '//div[@id="info"][@class]/span/a[@class][@href]/text()'
    B_PUB = '//div[@class="subject clearfix"]/div[@id="info"]/text()'
    B_SHORT = '//span[@class="short"]/div[@class="intro"]//following-sibling::*'

    # 个人状态页面[wish/do/collect]获取信息
    LIST_BOOK_URL = '//div[@class="pic"]/a[@class="nbg"]/@href'
    LIST_BOOK_NAME = '//div[@class="info"]/h2/a/@title'
    LIST_BOOK_DATE_STATUS = '//div[@class="short-note"]/div/span[@class="date"]/text()'
    LIST_BOOK_PIC = '//li[@class="subject-item"]/div[@class="pic"]/a/img/@sync_data'
    LIST_BOOK_PUB = '//div[@class="info"]/div[@class="pub"]/text()'


class DatabaseProperty(Enum):
    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDITED_TIME = "last_edited_time"
    LAST_EDITED_BY = "last_edited_by"


class ConfigName(Enum):
    USER_AGENT = "user_agent"
    DOUBAN = "douban"
    DOUBAN_USER_ID = 'user_id'
    DOUBAN_DAY = "day"

    NOTION = "notion"
    NOTION_TOKEN = 'token'
    NOTION_PAGE_ID = 'page_id'
    NOTION_BOOK = 'book_database_id'
    NOTION_MUSIC = 'music_database_id'
    NOTION_MOVIE = 'movie_database_id'


class UserConfig(object):

    def __init__(self):
        self.user_agent = ''
        self.douban = {}
        self.notion = {}


def get_desensitization_of_user_info(user_info):
    x_user_info = ''
    user_len = len(user_info)
    for i in range(user_len):
        if user_len / 2 - user_len / 4 < i < user_len / 2 + user_len / 4:
            x_user_info += "*"
        else:
            x_user_info += user_info[i]
    return x_user_info
