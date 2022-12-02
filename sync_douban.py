import os
import logging
import argparse
from dotenv import load_dotenv
from douban.sync import DoubanNotionSync
from douban.notion_database import create_database

load_dotenv()


def main(args):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                        datefmt='%a %d %b %Y %H:%M:%S',
                        handlers=[logging.FileHandler("douban.log", mode='w', encoding='utf-8'),
                                  logging.StreamHandler()])

    user_agent = os.getenv("USER_AGENT")
    cookie = os.getenv("DOUBAN_COOKIE")
    ck = os.getenv("CK")
    uid = os.getenv("UID")
    token = os.getenv("NOTION_TOKEN")
    movie_database_id = os.getenv("MOVIE_DATABASE_ID")
    book_database_id = os.getenv("BOOK_DATABASE_ID")
    if args.init:
        page_id = os.getenv("BASE_PAGE_ID")
        create_database(token=token, page_id=page_id, media_type="movie")
        create_database(token=token, page_id=page_id, media_type="book")
    elif args.sync:
        sync = DoubanNotionSync(user_agent=user_agent,
                                cookie=cookie,
                                ck=ck,
                                uid=uid,
                                token=token,
                                movie_database_id=movie_database_id,
                                book_database_id=book_database_id)
        sync.sync()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--sync", action="store_true", help="同步数据")   

    args = parser.parse_args()
    main(args)
