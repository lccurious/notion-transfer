import os
import re
import json
import logging
import argparse
from pathlib import Path
from pprint import pprint
from notion_client import Client
from notion_client.helpers import collect_paginated_api
from dotenv import load_dotenv
from convertor.block import BlockConvertor, NotionClient

load_dotenv()


def main(args):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                        datefmt='%a %d %b %Y %H:%M:%S',
                        handlers=[logging.FileHandler("blog.log", mode='w', encoding='utf-8'),
                                  logging.StreamHandler()])

    token = os.getenv("NOTION_TOKEN")

    notion = Client(auth=token)
    match = re.search(r"https://www.notion.so/[\w-]+/[\w-]*([a-f0-9]{32})[\\w-]*", args.page_url)
    if match:
        page_id = match.group(1)
    else:
        raise ValueError("Invalid page url")
    blocks = collect_paginated_api(notion.blocks.children.list, block_id=page_id)

    asset_path = Path(args.output).parent / Path(args.output).stem
    asset_path.mkdir(parents=True, exist_ok=True)
    with open(asset_path / "notion_data.json", "w", encoding="utf-8") as fp:
        json.dump(blocks, fp, indent=4, ensure_ascii=False)
    
    notion_client = NotionClient()
    convertor = BlockConvertor(notion_client, download=True, tmp_path=asset_path)
    md_file = convertor.convert(blocks)

    with open(args.output, "w", encoding="utf-8") as fp:
        fp.write(md_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--page_url", help="Specify the page url, ⌘ + L to copy the link to the page", required=True)
    parser.add_argument("-o", "--output", help="Specify the output file name", default="output.md")

    args = parser.parse_args()
    main(args)
