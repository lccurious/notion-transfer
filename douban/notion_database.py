import re
import logging
import abc
import collections
from datetime import datetime, timezone, timedelta
from notion_client import Client
from notion_client import APIErrorCode, APIResponseError
from douban.constants import MediaType


def make_iso_datetime_str(douban_datetime):
    """
    将豆瓣时间转换为ISO时间
    :param douban_datetime: 豆瓣时间
    :return: ISO时间
    """
    raw_datetime = datetime.fromisoformat(douban_datetime)
    clean_datetime = raw_datetime.replace(tzinfo=timezone(timedelta(hours=8)))
    return clean_datetime.isoformat()


def create_database(token, page_id, media_type):
    """
    创建新的数据库
    :param media_type: 媒体类型 book music tv movie
    :param token: notion->setting->integrations->develop your own integrations
    :param page_id: 浏览器打开notion，链接的尾部获取
    :return: databases_id，可以通过该id定位到数据库
    """
    create_db_data = {}
    if media_type == MediaType.BOOK.value:
        create_db_data = {
            "parent": {"type": "page_id", "page_id": f"{page_id}"},
            "title": [{"type": "text", "text": {"content": "豆瓣书单库"}}],
            "icon": {"type": "emoji", "emoji": "📚"},
            "properties": {
                "封面": {"files": {}},
                "书名": {"title": {}},
                "标记状态": {"select": {}},
                "个人评分": {"select": {"options": [
                    {"name": "⭐", "color": "yellow"},
                    {"name": "⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐⭐", "color": "yellow"}]}},
                "评分": {"number": {}},
                "评分人数": {"number": {}},
                "作者": {"multi_select": {}},
                "类型": {"multi_select": {}},
                "出版社": {"multi_select": {}},
                "出版年份": {"select": {}},
                "短评": {"rich_text": {}},
                "标记时间": {"date": {}},
                "豆瓣链接": {"url": {}},
                "ISBN": {"number": {}},
                "价格": {"number": {}},
                "页数": {"number": {}},
            }}
    elif media_type == MediaType.MUSIC.value:
        create_db_data = {
            "parent": {"type": "page_id", "page_id": f"{page_id}"},
            "title": [{"type": "text", "text": {"content": "豆瓣音乐库"}}],
            "icon": {"type": "emoji", "emoji": "🎵"},
            "properties": {
                "音乐": {"title": {}},
                "表演者": {"rich_text": {}},
                "封面": {"files": {}},
                "评分": {"number": {}},
                "出版者": {"select": {}},
                "发行时间": {"select": {}},
                "ISRC": {"url": {}},
                "豆瓣链接": {"url": {}},
                "评分人数": {"number": {}},
                "短评": {"rich_text": {}},
                "类型": {"multi_select": {}},
                "标记状态": {"select": {}},
                "标记时间": {"date": {}},
                "个人评分": {"select": {"options": [
                    {"name": "⭐", "color": "yellow"},
                    {"name": "⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐⭐", "color": "yellow"}]}},
            }}
    elif media_type == MediaType.MOVIE.value:
        """
        类型是获取豆瓣中的信息
            剧情 / 动作 / 科幻 / 犯罪
        分类是个人主观分的
            电视剧、电影、动画片（指的是电影）、动漫（剧集）、纪录片（电影和电视剧）
        """
        create_db_data = {
            "parent": {"type": "page_id", "page_id": f"{page_id}"},
            "title": [{"type": "text", "text": {"content": "豆瓣影视库"}}],
            "icon": {"type": "emoji", "emoji": "🎬"},
            "properties": {
                "封面": {"files": {}},
                "名字": {"title": {}},
                "标记状态": {"select": {}},
                "个人评分": {"select": {"options": [
                    {"name": "⭐", "color": "yellow"},
                    {"name": "⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐", "color": "yellow"},
                    {"name": "⭐⭐⭐⭐⭐", "color": "yellow"}]}},
                "评分": {"number": {}},
                "评分人数": {"number": {}},
                "分类": {"select": {}},
                "类型": {"multi_select": {}},
                "主演": {"multi_select": {}},
                "导演": {"multi_select": {}},
                "编剧": {"multi_select": {}},
                "短评": {"rich_text": {}},
                "时间": {"select": {}},
                "国家地区": {"multi_select": {}},
                "简介": {"rich_text": {}},
                "片长": {"number": {}},
                "标记时间": {"date": {}},
                "豆瓣链接": {"url": {}},
                "IMDb": {"url": {}},
            }}
    else:
        exit("暂不支持其他数据库的创建")

    _db_map = {
        MediaType.MOVIE.value: 'MOVIE_DATABASE_ID',
        MediaType.BOOK.value: 'BOOK_DATABASE_ID',
    }

    try:
        if create_db_data:
            logging.info(f"创建{media_type}数据库--初始化参数")
            notion = Client(auth=token)
            resp = notion.databases.create(**create_db_data)
            logging.info(f"更新 .env 中 {_db_map[media_type]}={resp['id']}")
        else:
            logging.warn(f"跳过创建{media_type}数据库")
    except Exception as err:
        exit(f"网络请求错误:{err}")


class NotionDatabase(metaclass=abc.ABCMeta):
    def __init__(self, notion_token, notion_database_id):
        self.notion = Client(auth=notion_token)
        self.notion_database_id = notion_database_id
        self.rating_value_name = [
            '',
            '⭐',
            '⭐⭐',
            '⭐⭐⭐',
            '⭐⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
        ]
    
    @abc.abstractclassmethod
    def construct_data(self, data):
        pass

    @abc.abstractclassmethod
    def check_exist(self, data):
        pass
    
    @abc.abstractclassmethod
    def create_item(self, item):
        pass

    @abc.abstractclassmethod
    def update_item(self, item):
        pass

    @abc.abstractclassmethod
    def compare(self, l, r):
        pass


class NotionBookDatabase(NotionDatabase):
    def __init__(self, notion_token, notion_database_id):
        super(NotionBookDatabase, self).__init__(notion_token, notion_database_id)
        self.book_status_name_dict = {
            "done": "读过",
            "doing": "在读",
            "mark": "想读",
        }
    
    def construct_data(self, data):
        body = {
            "parent": {
                "type": "database_id",
                "database_id": self.notion_database_id
            },
            "properties": {
                "书名": {
                    "title": [{
                        "type": "text",
                        "text": {
                            "content": data["subject"]["title"]
                        }
                    }]
                },
                "封面": {
                    "files": [{
                        "type": "external",
                        "name": data["subject"]["cover_url"][-13:],
                        "external": {
                            "url": data["subject"]["cover_url"]
                        }
                    }]
                },
                "作者": {
                    "multi_select": [
                        # NOTE: Notion select property can not accept comas
                        {"name": author.replace(',', '')} for author in data["subject"]["author"]
                    ]
                },
                "出版年份": {
                    "select": {
                        "name": data["subject"]["pubdate"][0][:4] if data["subject"]["pubdate"] else '未知'
                    }
                },
                "标记状态": {
                    "select": {
                        "name": self.book_status_name_dict[data["status"]]
                    },
                },
                "标记时间": {
                    "date": {
                        "end": None,
                        "start": make_iso_datetime_str(data["create_time"]),
                        # "time_zone": "Asia/Shanghai"
                    },
                },
                "豆瓣链接": {
                    "url": data["subject"]["url"]
                }
            }
        }

        if data['rating'] is not None:
            body["properties"].update({
                "个人评分": {
                    "select": {
                        "name": self.rating_value_name[int(data["rating"]["star_count"])],
                    },
                }
            })

        if len(data["comment"]):
            body["properties"].update({
                "短评": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": data["comment"]
                            }
                        }
                    ]
                }
            })

        if len(data["tags"]):
            body["properties"].update({
                "类型": {
                    "multi_select": [
                        {"name": tag} for tag in data["tags"]
                    ]
                }
            })

        if data["subject"]["rating"]:
            body["properties"].update({
                "评分": {
                    "number": data["subject"]["rating"]["value"],
                }
            })
            body["properties"].update({
                "评分人数": {
                    "number": data["subject"]["rating"]["count"],
                }
            })

        if data["subject"]["pages"]:
            body["properties"].update({
                "页数": {
                    # 有些书包括基本小书合订,所以要把页数都加总在一起
                    "number": sum([int(it) for it in re.sub(r'[^0-9]', ',', data["subject"]["pages"][0]).split(',') if it]),
                }
            })

        if data["subject"]["press"]:
            body["properties"].update({
                "出版社": {
                    "multi_select": [
                        # NOTE: Notion select property can not accept comas
                        {"name": press.replace(',', '')} for press in data["subject"]["press"]
                    ]
                }
            })
        
        if 'isbn' in data["subject"] and data['subject']["isbn"]:
            body["properties"].update({
                "ISBN": {
                    "number": int(data["subject"]["isbn"]),
                }
            })
        if 'book_price' in data["subject"] and data['subject']["book_price"]:
            body["properties"].update({
                "价格": {
                    "number": data["subject"]["book_price"],
                }
            })
        return body
    
    def check_exist(self, data):
        query = {
            "filter": {
                "and": [
                    {
                        "property": "豆瓣链接",
                        "url": {
                            "equals": data["subject"]["url"]
                        }
                    }
                ]
            }
        }
        result = self.notion.databases.query(
            database_id=self.notion_database_id,
            filter=query["filter"],
        )
        return len(result["results"]) > 0, result["results"][0]["id"] if len(result["results"]) > 0 else None
    
    def create_item(self, item):
        try:
            body = self.construct_data(item)
            self.notion.pages.create(**body)
        except Exception as err:
            logging.error(f"创建书籍 {item['subject']['title']}失败:{err}")

    def update_item(self, page_id, item):
        try:
            body = self.construct_data(item)
            self.notion.pages.update(page_id=page_id, **body)
        except Exception as err:
            logging.error(f"更新书籍 {item['subject']['title']}失败:{err}")
    
    def _parse_datetime(self, date_dict):
        raw_datetime = datetime.fromisoformat(date_dict['start'])
        clean_datetime = raw_datetime.replace(tzinfo=timezone(timedelta(hours=8)))
        return clean_datetime

    def compare(self, l, r):
        if (l["properties"]["标记状态"]["select"]["name"] != r["properties"]["标记状态"]["select"]["name"]):
            return False

        l_datetime = self._parse_datetime(l["properties"]["标记时间"]["date"])
        r_datetime = self._parse_datetime(r["properties"]["标记时间"]["date"])
        if (l_datetime != r_datetime):
            return False
        l_rating = l["properties"].get("个人评分", None)
        r_rating = r["properties"].get("个人评分", None)
        if l_rating is not None and r_rating is not None:
            return l_rating["select"]["name"] == r_rating["select"]["name"]
        elif l_rating is not None:
            l_rating = l_rating["select"]
            return l_rating == r_rating
        elif r_rating is not None:
            r_rating = r_rating["select"]
            return l_rating == r_rating
        l_tags = sorted([tag["name"] for tag in l['properties']['类型']['multi_select']])
        r_tags = sorted([tag["name"] for tag in r['properties']['类型']['multi_select']])
        if collections.Counter(l_tags) != collections.Counter(r_tags):
            return False
        return True

    def sync(self, data):
        exist, page_id = self.check_exist(data)
        body = self.construct_data(data)
        if exist:
            try:
                notion_record = self.notion.pages.retrieve(page_id=page_id)
            except APIResponseError as err:
                logging.error(f"查询书籍{data['subject']['title']}失败:{err}")
                return
            if not self.compare(notion_record, body):
                self.update_item(page_id, data)
                logging.info(f"更新书籍 {data['subject']['title']}")
            else:
                logging.info(f"书籍 {data['subject']['title']} 已存在")
        else:
            self.create_item(data)
            logging.info(f"创建书籍 {data['subject']['title']}")


class NotionMovieDatabase(NotionDatabase):
    def __init__(self, notion_token, notion_database_id):
        super(NotionMovieDatabase, self).__init__(notion_token, notion_database_id)
        self.movie_status_name_dict = {
            "done": "看完",
            "doing": "在看",
            "mark": "想看",
        }
    
    def construct_data(self, data):
        body = {
            "parent": {
                "type": "database_id",
                "database_id": self.notion_database_id
            },
            "properties": {
                "名字": {
                    "title": [{
                        "type": "text",
                        "text": {
                            "content": data["subject"]["title"]
                        }
                    }]
                },
                "导演": {
                    # NOTE: Notion select property can not accept comas
                    "multi_select": [d for d in data["subject"]["directors"] if d["name"]]
                }, 
                # "主演": {
                #     # notion 最多支持100个选项
                #     "multi_select": [a for a in data["subject"]["actors"] if a["name"]][:50]
                # },
                "类型": {
                    "multi_select": [
                        {"name": genre} for genre in data["subject"]["genres"]
                    ]
                },
                # "时间": {
                #     "select": {
                #         "name": data["subject"]["pubdate"][0][:4] if data["subject"]["pubdate"] else ""
                #     },
                # },
                "标记状态": {
                    "select": {
                        "name": self.movie_status_name_dict[data["status"]],
                    }
                }, 
                "标记时间": {
                    "date": {
                        "end": None,
                        "start": make_iso_datetime_str(data["create_time"]),
                        # "time_zone": "Asia/Shanghai"
                    },
                },
                "封面": {
                    "files": [{
                        "type": "external",
                        "name": data["subject"]["cover_url"][-15:],
                        "external": {
                            "url": data["subject"]["cover_url"]
                        }
                    }]
                },
                "豆瓣链接": {
                    "url": data["subject"]["url"]
                }
            }
        }

        if 'actors' in data['subject'] and data['subject']['actors']:
            body["properties"].update({
                "主演": {
                    "multi_select": [
                        # NOTE: Notion select property can not accept comas
                        {"name": actor["name"].replace(',', '')} for actor in data["subject"]["actors"]
                    ]
                },
            })

        if 'pubdate' in data['subject'] and data['subject']['pubdate']:
            body["properties"].update({
                "时间": {
                    "select": {
                        "name": data['subject']['pubdate'][0][:4],
                    }
                },
            })

        if 'screenwriter' in data['subject'] and data['subject']['screenwriter']:
            body["properties"].update({
                "编剧": {
                    "multi_select": [
                        # NOTE: Notion select property can not accept comas
                        {"name": writer.replace(',', '')} for writer in data["subject"]["screenwriter"]
                    ]
                }
            })
        
        if 'c_or_r' in data['subject'] and data['subject']['c_or_r']:
            body["properties"].update({
                "国家地区": {
                    "multi_select": [
                        # NOTE: Notion select property can not accept comas
                        {"name": c_or_r.replace(',', '')} for c_or_r in data["subject"]["c_or_r"]
                    ]
                },
            })
        
        if 'imdb' in data['subject'] and data['subject']['imdb']:
            imdb = data['subject']['imdb']
            body["properties"].update({
                "IMDb": {
                    "url": f"https://www.imdb.com/title/{imdb}"
                },
            })

        if 'movie_type' in data['subject'] and data['subject']['movie_type']:
            body["properties"].update({
                "分类": {
                    "select": {
                        "name": data['subject']['movie_categories'],
                    }
                },
            })
        
        if 'related_intro' in data['subject'] and data['subject']['related_intro']:
            body["properties"].update({
                "简介": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": data['subject']['related_intro'],
                        }
                    }]
                },
            })

        if data['rating'] is not None:
            body["properties"].update({
                "个人评分": {
                    "select": {
                        "name": self.rating_value_name[int(data["rating"]["star_count"])],
                    },
                }
            })

        if len(data["comment"]):
            body["properties"].update({
                "短评": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": data["comment"]
                            }
                        }
                    ]
                }
            })

        if len(data["tags"]):
            body["properties"].update({
                "类型": {
                    "multi_select": [
                        {"name": tag} for tag in data["tags"]
                    ]
                }
            })

        if data["subject"]["rating"]:
            body["properties"].update({
                "评分": {
                    "number": data["subject"]["rating"]["value"],
                }
            })
            body["properties"].update({
                "评分人数": {
                    "number": data["subject"]["rating"]["count"],
                }
            })

        if 'movie_duration' in data['subject'] and data['subject']['movie_duration']:
            body["properties"].update({
                "片长": {
                    "number": int(data['subject']['movie_duration']),
                }
            })
        
        return body

    def check_exist(self, data):
        query = {
            "filter": {
                "and": [
                    {
                        "property": "豆瓣链接",
                        "url": {
                            "equals": data["subject"]["url"]
                        }
                    }
                ]
            }
        }
        result = self.notion.databases.query(
            database_id=self.notion_database_id,
            filter=query["filter"],
        )
        return len(result["results"]) > 0, result["results"][0]["id"] if len(result["results"]) > 0 else None
        
    def create_item(self, item):
        try:
            body = self.construct_data(item)
            self.notion.pages.create(**body)
        except Exception as err:
            logging.error(f"创建电影 {item['subject']['title']} 失败:{err}")

    def update_item(self, page_id, item):
        try:
            body = self.construct_data(item)
            self.notion.pages.update(page_id=page_id, **body)
        except Exception as err:
            logging.error(f"更新电影 {item['subject']['title']} 失败:{err}")

    def _parse_datetime(self, date_dict):
        raw_datetime = datetime.fromisoformat(date_dict['start'])
        clean_datetime = raw_datetime.replace(tzinfo=timezone(timedelta(hours=8)))
        return clean_datetime

    def compare(self, l, r):
        if (l["properties"]["标记状态"]["select"]["name"] != r["properties"]["标记状态"]["select"]["name"]):
            return False
        
        # Douban: 2022-11-23 10:22:58
        # Notion: 2022-03-18T12:40:00.000+08:00
        l_datetime = self._parse_datetime(l["properties"]["标记时间"]["date"])
        r_datetime = self._parse_datetime(r["properties"]["标记时间"]["date"])
        if (l_datetime != r_datetime):
            return False
        l_rating = l["properties"].get("个人评分", None)
        r_rating = r["properties"].get("个人评分", None)
        if l_rating is not None and r_rating is not None:
            return l_rating["select"]["name"] == r_rating["select"]["name"]
        elif l_rating is not None:
            l_rating = l_rating["select"]
            return l_rating == r_rating
        elif r_rating is not None:
            r_rating = r_rating["select"]
            return l_rating == r_rating
        l_tags = sorted([tag["name"] for tag in l['properties']['类型']['multi_select']])
        r_tags = sorted([tag["name"] for tag in r['properties']['类型']['multi_select']])
        if collections.Counter(l_tags) != collections.Counter(r_tags):
            return False
        return True
    
    def sync(self, data):
        exist, page_id = self.check_exist(data)
        body = self.construct_data(data)
        if exist:
            try:
                notion_record = self.notion.pages.retrieve(page_id=page_id)
            except APIResponseError as err:
                logging.error(f"查询电影 {data['subject']['title']} 失败:{err}")
                return
            if not self.compare(notion_record, body):
                self.update_item(page_id, data)
                logging.info(f"更新电影 {data['subject']['title']}")
            else:
                logging.info(f"电影 {data['subject']['title']} 已存在")
        else:
            self.create_item(data)
            logging.info(f"创建电影 {data['subject']['title']}")
