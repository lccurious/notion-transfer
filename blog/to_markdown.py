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


def generate_front_matter(title: str, date: str, tags: list, categories: list, thumbnail: str, giscus_comments: bool, toc_sidebar: bool) -> str:
    """
    自动生成Jekyll博客帖子的YAML Front Matter头部。

    参数:
    - title: 文章标题
    - date: 发布日期，格式: YYYY-MM-DD
    - tags: 文章标签列表
    - categories: 文章分类列表
    - thumbnail: 文章缩略图路径
    - giscus_comments: 是否启用Giscus评论
    - toc_sidebar: 目录是否侧栏显示
    """
    # 将标签和分类列表转换为YAML格式的字符串
    tags_str = "\n  - ".join(tags)
    categories_str = "\n  - ".join(categories)
    
    return (
        f"---\n"
        f"layout: post\n"
        f"title: {title}\n"
        f"date: {date}\n"
        f"tags:\n"
        f"  - {tags_str}\n"
        f"categories:\n"
        f"  - {categories_str}\n"
        f"thumbnail: {thumbnail}\n"
        f"giscus_comments: {'true' if giscus_comments else 'false'}\n"
        f"toc:\n"
        f"  sidebar: {'true' if toc_sidebar else 'false'}\n"
        f"---\n"
    )


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
    md_head = generate_front_matter(
        title=args.title,
        date=args.date,
        tags=args.tags,
        categories=args.categories,
        thumbnail=args.thumbnail,
        giscus_comments=args.giscus_comments,
        toc_sidebar=args.toc_sidebar
    )
    md_file = md_head + "\n\n" + convertor.convert(blocks)

    with open(args.output, "w", encoding="utf-8") as fp:
        fp.write(md_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--page_url", help="Specify the page url, ⌘ + L to copy the link to the page", required=True)
    parser.add_argument("-o", "--output", help="Specify the output file name", default="output.md")
    parser.add_argument('--title', required=True, help='Title of the post')
    parser.add_argument('--date', required=True, help='Date of the post')
    parser.add_argument('--tags', required=True, nargs='+', help='Tags of the post, space-separated')
    parser.add_argument('--categories', required=True, nargs='+', help='Categories of the post, space-separated')
    parser.add_argument('--thumbnail', required=False, help='Thumbnail path of the post')
    parser.add_argument('--giscus_comments', action='store_true', help='Enable Giscus comments if set')
    parser.add_argument('--toc_sidebar', action='store_true', help='Enable TOC sidebar if set')

    args = parser.parse_args()
    main(args)
