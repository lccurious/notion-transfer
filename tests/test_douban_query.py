import os
import unittest
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from douban.douban_query import DoubanAPI
from douban.notion_database import NotionBookDatabase, NotionMovieDatabase


class TestDoubanQuery(unittest.TestCase):
    def test_douban_query_movie(self):
        load_dotenv()
        loop = asyncio.get_event_loop()
        api = DoubanAPI(user_agent=os.environ.get("USER_AGENT"), 
                        cookie=os.environ.get("DOUBAN_COOKIE"),
                        ck=os.environ.get("DOUBAN_CK"))
        movie_url = "https://movie.douban.com/subject/30252495/"
        movie_details = loop.run_until_complete(api.fetch_movie_detail(movie_url))
        pprint(movie_details)

    def test_douban_query_book(self):
        load_dotenv()
        loop = asyncio.get_event_loop()
        api = DoubanAPI(user_agent=os.environ.get("USER_AGENT"), 
                        cookie=os.environ.get("DOUBAN_COOKIE"),
                        ck=os.environ.get("DOUBAN_CK"))
        book_url = "https://book.douban.com/subject/35571615/"
        book_details = loop.run_until_complete(api.fetch_book_detail(book_url))
        pprint(book_details)
    
    def test_douban_query_interests_total(self):
        load_dotenv()
        loop = asyncio.get_event_loop()
        api = DoubanAPI(user_agent=os.environ.get("USER_AGENT"),
                        cookie=os.environ.get("DOUBAN_COOKIE"),
                        ck=os.environ.get("DOUBAN_CK"))
        resp_code, interests = loop.run_until_complete(
            api.fetch_interests_total(uid=os.environ.get("UID")))
        pprint(interests)
    
    def test_douban_query_interest(self):
        load_dotenv()
        loop = asyncio.get_event_loop()
        api = DoubanAPI(user_agent=os.environ.get("USER_AGENT"), 
                        cookie=os.environ.get("DOUBAN_COOKIE"),
                        ck=os.environ.get("DOUBAN_CK"))
        book_db = NotionBookDatabase(
            notion_token=os.environ.get("NOTION_TOKEN"),
            notion_database_id=os.environ.get("BOOK_DATABASE_ID"))
        movie_db = NotionMovieDatabase(
            notion_token=os.environ.get("NOTION_TOKEN"),
            notion_database_id=os.environ.get("MOVIE_DATABASE_ID"))
        
        for interest_type in ["movie", "book"]:
            for status in ["mark", "doing", "done"]:
                resp_code, interests = loop.run_until_complete(
                    api.fetch_interests(uid=os.environ.get("UID"),
                                        interest_type=interest_type,
                                        status=status,
                                        start=0, 
                                        count=1))
                for interest in interests['interests']:
                    detail_url = interest['subject']['url']
                    if interest_type == "movie":
                        details = loop.run_until_complete(api.fetch_movie_detail(detail_url))
                        interest['subject'].update(details['subject'])
                        body = movie_db.construct_data(interest)
                        is_exist, page_id = movie_db.check_exist(interest)
                        print(interest['subject']['title'], is_exist)
                        # pprint(body)
                    elif interest_type == "book":
                        details = loop.run_until_complete(api.fetch_book_detail(detail_url))
                        interest['subject'].update(details['subject'])
                        body = book_db.construct_data(interest)
                        is_exist, page_id = book_db.check_exist(interest)
                        print(interest['subject']['title'], is_exist)
                        # pprint(body)
