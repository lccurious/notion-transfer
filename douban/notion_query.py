import logging
from notion_client import Client
from notion_client import APIErrorCode, APIResponseError


def query_notion_data(token, database_id, media_url):
    notion = Client(auth=token)
    try:
        database = notion.databases.query(**{
            'database_id': database_id,
            'filter': {
                'property': '豆瓣链接',
                'url': {
                    'equals': f'{media_url}',
                },
            }
        })
    except APIResponseError as err:
        if err.code == APIErrorCode.ObjectNotFound:
            logging.warning("Database not found")
        else:
            logging.error(err)
    return database


def get_notion_media_status(token, database_id, media_url):
    database = query_notion_data(token=token, database_id=database_id, media_url=media_url)
    if not database['results']:
        return None
    else:
        notion_media_status = database['results'][0]['properties']['标记状态']['select']
        notion_media_timestamp = database['results'][0]['properties']['标记时间']['date']
        logging.info("Last state in database is: %s", notion_media_status)
        return notion_media_status, notion_media_timestamp
