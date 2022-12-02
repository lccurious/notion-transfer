import os
import asyncio
import time
import logging
from datetime import datetime
import numpy as np
from douban.douban_query import DoubanAPI
from douban.notion_database import NotionBookDatabase, NotionMovieDatabase


class DoubanNotionSync(object):
    def __init__(self, 
                 user_agent, 
                 cookie, 
                 ck, 
                 uid, 
                 token, 
                 movie_database_id, 
                 book_database_id) -> None:
        self.api = DoubanAPI(user_agent=user_agent,
                             cookie=cookie,
                             ck=ck)
        self.uid = uid
        self.movie_db = NotionMovieDatabase(
            notion_token=token,
            notion_database_id=movie_database_id)
        self.book_db = NotionBookDatabase(
            notion_token=token,
            notion_database_id=book_database_id)
        self.last_sync_time = self._load_last_sync_time()
        self.PAGE_SIZE = 20
        self.total = 0
    
    def _load_last_sync_time(self):
        if os.path.exists("last_sync_time.txt"):
            with open("last_sync_time.txt", "r") as f:
                return datetime.fromisoformat(f.read())
        else:
            return datetime.fromisoformat("2006-01-01T00:00:00")
    
    def _save_last_sync_time(self):
        with open("last_sync_time.txt", "w") as f:
            f.write(datetime.now().isoformat())
    
    def _random_sleep(self):
        sleep_time = np.random.uniform(0.5, 5.5)
        time.sleep(sleep_time)
    
    def fetch_total(self):
        loop = asyncio.get_event_loop()
        resp_code, interests = loop.run_until_complete(
            self.api.fetch_interests_total(uid=self.uid))
        return int(interests['total'])

    def sync(self):
        self.total = self.fetch_total()
        loop = asyncio.get_event_loop()
        for interest_type in ["movie", "book"]:
            for status in ["doing", "done", "mark"]:
                page_count = 1
                i = 0
                while i < page_count:
                    start = i * self.PAGE_SIZE
                    resp_code, interests = loop.run_until_complete(
                        self.api.fetch_interests(uid=self.uid,
                                                 interest_type=interest_type,
                                                 status=status,
                                                 start=start, 
                                                 count=self.PAGE_SIZE))
                    if resp_code != 200:
                        if resp_code == 500:
                            # try to fetch this page sliced
                            for j in range(self.PAGE_SIZE):
                                start_sliced = start + j
                                resp_code, interests = loop.run_until_complete(
                                    self.api.fetch_interests(uid=self.uid,
                                                             interest_type=interest_type,
                                                             status=status,
                                                             start=start_sliced,
                                                             count=1))
                                if resp_code != 200:
                                    continue
                                    
                                sync_flag = self.sync_interests(interests, interest_type)
                                self._random_sleep()
                                if interests['total'] == start_sliced:
                                    continue
                                
                    page_count = np.ceil(self.total / self.PAGE_SIZE)
                    sync_flag = self.sync_interests(interests['interests'], interest_type)
                    self._random_sleep()
                    
                    if sync_flag == 'Already synced':
                        logging.info(f"{interest_type}/{status} 已是最新，跳过")
                        break

                    # update the start page index
                    i += 1

        # save the last sync time
        self._save_last_sync_time()

    def sync_interests(self, interests, interest_type):
        loop = asyncio.get_event_loop()
        for interest in interests:
            timestamp = datetime.fromisoformat(interest['create_time'])
            if timestamp <= self.last_sync_time:
                return 'Already synced'

            detail_url = interest['subject']['url']
            try:
                if interest_type == "movie":
                    is_exist, page_id = self.movie_db.check_exist(interest)
                    if not is_exist:
                        details = loop.run_until_complete(self.api.fetch_movie_detail(detail_url))
                        interest['subject'].update(details['subject'])
                        self._random_sleep()
                    else:
                        logging.info(f"{interest['subject']['title']} 已有记录")
                    self.movie_db.sync(interest)
                elif interest_type == "book":
                    is_exist, page_id = self.book_db.check_exist(interest)
                    if not is_exist:
                        details = loop.run_until_complete(self.api.fetch_book_detail(detail_url))
                        interest['subject'].update(details['subject'])
                        self._random_sleep()
                    else:
                        logging.info(f"{interest['subject']['title']} 已有记录")
                    self.book_db.sync(interest)
            except Exception as err:
                logging.error(f"处理 {interest} 遇到错误: {err}")
        return 'Continue syncing'
