import os
import unittest
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from douban.douban_query import DoubanAPI
from douban.notion_database import NotionBookDatabase, NotionMovieDatabase


class TestDoubanSync(unittest.TestCase):
    def test_douban_sync(self):
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
                        movie_db.sync(interest)
                    elif interest_type == "book":
                        details = loop.run_until_complete(api.fetch_book_detail(detail_url))
                        interest['subject'].update(details['subject'])
                        book_db.sync(interest)
