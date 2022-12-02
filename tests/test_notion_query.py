import os
import unittest
from dotenv import load_dotenv
from douban.notion_query import get_notion_media_status, query_notion_data


class TestNotionQuery(unittest.TestCase):
    def test_notion_query(self):
        load_dotenv()
        media_url = "https://book.douban.com/subject/26729910/"
        status, timestamp = get_notion_media_status(
            token=os.environ.get("NOTION_TOKEN"), 
            database_id=os.environ.get("BOOK_DATABASE_ID"), 
            media_url=media_url)
        self.assertIsInstance(status, dict)
        print(status, timestamp)
    
    def test_notion_query_data(self):
        load_dotenv()
        media_url = "https://book.douban.com/subject/35571615/"
        data = query_notion_data(
            token=os.environ.get("NOTION_TOKEN"), 
            database_id=os.environ.get("BOOK_DATABASE_ID"), 
            media_url=media_url)
        self.assertIsInstance(data, dict)
