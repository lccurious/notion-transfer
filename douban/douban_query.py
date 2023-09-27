import asyncio
import aiohttp
import logging
import json
import re
from bs4 import BeautifulSoup
from douban.constants import DoubanRexxarURL


def get_single_info_str(str_list, str_key):
    return str_list[str_list.index(str_key) + 1] if str_key in str_list else ""


def get_multiple_infos_list(infos_list, str_key, next_number):
    """
    解析媒体info, 必须豆瓣中是':'和名称不一起的数据

    :param infos_list: 字符串列表
    :param str_key: 字符串字典关键字
    :param next_number: 豆瓣中/的位置
    :return: 对应key值信息的列表
    """
    str_list = []
    try:
        if str_key in infos_list:
            first_index = infos_list.index(str_key) + next_number
            str_list.append(infos_list[first_index])
            next_index = first_index
            while True:
                if infos_list[next_index + 1] == '/':
                    next_index += 2
                    str_list.append(infos_list[next_index])
                else:
                    break
        else:
            logging.warn(f"未解析到{str_key}数据，返回空值")
        return str_list
    except Exception as err:
        logging.error(f"未解析到{str_key}数据：{err}")
        return  str_list


def get_single_info_list(infos_list, str_key):
    """
    获取豆瓣信息， 针对豆瓣:和关键字在一起的

    :param infos_list: 字符串列表
    :param str_key: 字符串字典关键字
    :return: 对应key值信息的列表
    """
    str_list = []
    try:
        if str_key in infos_list:
            data_list_tmp = infos_list[infos_list.index(str_key) + 1]
            data_list_tmp = data_list_tmp.split('/')

            for i in data_list_tmp:
                str_list.append(i.strip(' '))
        else:
            logging.warn(f"未解析到<{str_key}>信息")
        return str_list
    except Exception as err:
        logging.error(f"未解析到<{str_key}>信息:{err}")
        return str_list


def get_media_related_infos(info):
    """
    获取媒体简介

    :param info:
    :return: 媒体简介 str类型
    """
    try:
        if info:
            related_infos = list(info[0].strings)
            related_infos = [i.strip() for i in related_infos if i.strip() != '']
            related_infos = "\n".join(related_infos)
            return related_infos
        else:
            return "暂无。"
    except Exception as err:
        logging.error(f"未解析到简介{err}")
        return "暂无。。。"


class DoubanAPI(object):
    def __init__(self, user_agent, cookie, ck):
        self.user_agent = user_agent
        self.cookie = cookie
        self.ck = ck
    
    async def fetch_interests_total(self, uid):
        header = {
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'Referer': 'https://m.douban.com/mine/'
        }
        total_interests_url = DoubanRexxarURL.INTERESTS_TOTAL.format(uid=uid, ck=self.ck)
        async with aiohttp.ClientSession(headers=header) as session:
            async with session.get(total_interests_url) as resp:
                data = await resp.text()
                try:
                    data_u = json.loads(data)
                except:
                    data_u = {'msg': 'Cookie Expired'}
                return resp.status, data_u

    async def fetch_interests(self, uid, interest_type, status, start, count):
        headers = {
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'Referer': 'https://m.douban.com/mine/' + interest_type
        }
        interest_url = DoubanRexxarURL.INTERESTS.format(
            uid=uid, 
            type=interest_type, 
            status=status, 
            start=start,
            count=count,
            ck=self.ck)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(interest_url) as resp:
                data = await resp.text()
                try:
                    data_u = json.loads(data)
                except:
                    data_u = {'msg': 'Cookie Expired'}
                return resp.status, data_u

    async def fetch_movie_detail(self, url):
        headers = {
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                html = await resp.text()
                try:
                    return self.parse_movie_detail(html)
                except:
                    return None

    def parse_movie_detail(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        info = soup.select('#info')
        info_list = info[0].get_text(strip=True, separator='\n').splitlines()

        if '导演' in info_list:
            movie_director = get_multiple_infos_list(info_list, '导演', 2)
        else:
            movie_director = ""
        screenwriter = get_multiple_infos_list(info_list, "编剧", 2)
        starring = get_multiple_infos_list(info_list, "主演", 2)
        movie_type = get_multiple_infos_list(info_list, "类型:", 1)
        # 国家或地区 语言
        c_or_r = get_single_info_list(info_list, "制片国家/地区:")
        language_list = get_single_info_list(info_list, "语言:")

        # 分类 电影和电视剧 以及 动画片（电影）和动漫（剧集）
        if '上映时间:' in info_list or '上映日期:' in info_list:
            if '动画' in movie_type:
                movie_categories = "动画片"
            else:
                movie_categories = '电影'
        elif "首播:" in info_list or "首播时间:" in info_list:
            if '动画' in movie_type:
                movie_categories = "动漫"
            else:
                movie_categories = "电视剧"
        else:
            movie_categories = "未知"

        imdb = info_list[info_list.index('IMDb:') + 1] if 'IMDb:' in info_list else ""
        length = info_list[info_list.index('片长:') + 1] if '片长:' in info_list else ""
        # movie_duration = length.split("分钟")[0] if length else ""
        movie_duration = re.match(length, r'(\d+)分钟').group(1) if length else ""

        related_info = soup.select("#content > div > div.article > div > div.indent > span")
        related_infos = get_media_related_infos(related_info)
        data = {
            'subject': {}
        }
        data['subject'].update({
            "movie_director": movie_director,
            "screenwriter": screenwriter,
            "starring": starring,
            "movie_type": movie_type,
            "c_or_r": c_or_r,
            "language_list": language_list,
            "movie_categories": movie_categories,
            "imdb": imdb,
            "movie_duration": movie_duration,
            "related_intro": related_infos
        })
        return data

    async def fetch_book_detail(self, url):
        headers = {
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                html = await resp.text()
                return self.parse_book_detail(html)
    
    def parse_book_detail(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        info = soup.select('#info')
        info_list = info[0].get_text(strip=True, separator='\n').splitlines()
        book_isbn = get_single_info_str(str_list=info_list, str_key="ISBN:")
        book_price = get_single_info_str(str_list=info_list, str_key="定价:")
        # 价格
        book_price_list = [float(s) for s in re.findall(r'-?\d+\.?\d*', book_price)]
        if len(book_price_list):
            book_price = book_price_list[0]
        else:
            book_price = 0

        data = {
            'subject': {}
        }
        data['subject'].update({
            'isbn': book_isbn,
            'book_price': book_price,
        })
        return data
