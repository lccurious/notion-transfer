import os
import unittest
from dotenv import load_dotenv
from douban.notion_database import create_database


class TestCreateDatabase(unittest.TestCase):
    def test_create_book_db(self):
        load_dotenv()
        media_type = "book"
        page_id = os.environ.get("BOOK_DATABASE_ID")
        create_database(
            token=os.environ.get("NOTION_TOKEN"), 
            page_id=page_id,
            media_type=media_type)
    
    def test_create_movie_db(self):
        load_dotenv()
        media_type = "movie"
        page_id = os.environ.get("MOVIE_DATABASE_ID")
        create_database(
            token=os.environ.get("NOTION_TOKEN"), 
            page_id=page_id,
            media_type=media_type)
        