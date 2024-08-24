"""
Adapted from https://github.com/echo724/notion2md/blob/8eb7747dd81e513d3d3baef957749c3080ce14f7/notion2md/convertor/block.py
"""

import concurrent.futures
import hashlib
import os
import logging
import urllib.request as request
from urllib.parse import urlparse

from .richtext import richtext_convertor
from notion_client import Client


def singleton(cls):
    instance = {}

    def get_instance():
        if cls not in instance:
            instance[cls] = cls()
        return instance[cls]

    return get_instance


@singleton
class NotionClient:
    def __init__(self):
        token = self._get_env_variable()
        self._client = Client(auth=token)

    def _get_env_variable(self):
        try:
            return os.environ["NOTION_TOKEN"]
        except Exception:
            raise "NOTION_TOKEN is not set!"

    def get_children(self, parent_id):
        # Most pages are small
        results = []
        start_cursor = None
        # Avoid infinite loops
        for _ in range(100):
            resp = self._client.blocks.children.list(
                parent_id, start_cursor=start_cursor, page_size=100
            )
            results.extend(resp["results"])
            start_cursor = resp["next_cursor"] if resp["has_more"] else None
            if start_cursor is None:
                return results
        raise Exception(
            "Can't parse notion page of > 10,000 children! (e.g. blocks)"
        )


class BlockConvertor:
    def __init__(self, client: NotionClient, download=True, tmp_path="./tmp"):
        self.download = download
        self.tmp_path = tmp_path
        self._client = client

    def convert(self, blocks: dict) -> str:
        outcome_blocks: str = ""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(self.convert_block, blocks)
            outcome_blocks = "".join([result for result in results])
        return outcome_blocks

    def convert_block(
            self,
            block: dict,
            depth=0,
    ):
        outcome_block: str = ""
        block_type = block["type"]
        # Special Case: Block is blank
        if check_block_is_blank(block, block_type):
            return blank() + "\n\n"
        # Normal Case
        try:
            if block_type in BLOCK_TYPES:
                outcome_block = (
                    BLOCK_TYPES[block_type](
                        self.collect_info(block[block_type])
                    )
                    + "\n\n"
                )
            else:
                outcome_block = f"[//]: # ({block_type} is not supported)\n\n"
            # Convert child block
            if block["has_children"]:
                # create child page
                if block_type == "child_page":
                    # call make_child_function
                    pass
                # create table block
                elif block_type == "table":
                    depth += 1
                    child_blocks = self._client.get_children(block["id"])
                    outcome_block = self.create_table(cell_blocks=child_blocks)
                # create indent block
                elif block_type == "column_list":
                    depth += 1
                    child_blocks = self._client.get_children(block["id"])
                    outcome_block = self.create_column_list(column_blocks=child_blocks)
                else:
                    depth += 1
                    child_blocks = self._client.get_children(block["id"])
                    for block in child_blocks:
                        converted_block = self.convert_block(
                            block,
                            depth,
                        )
                        outcome_block += "\t" * depth + converted_block
        except Exception as e:
            logging.error(f"{e}: Error occured block_type:{block_type}")
        return outcome_block

    def create_table(self, cell_blocks: dict):
        table_list = []
        for cell_block in cell_blocks:
            cell_block_type = cell_block["type"]
            table_list.append(
                BLOCK_TYPES[cell_block_type](
                    self.collect_info(cell_block[cell_block_type])
                )
            )
        # convert to markdown table
        for index, value in enumerate(table_list):
            if index == 0:
                table = " | " + " | ".join(value) + " | " + "\n"
                table += (
                    " | " + " | ".join(["----"] * len(value)) + " | " + "\n"
                )
                continue
            table += " | " + " | ".join(value) + " | " + "\n"
        table += "\n"
        return table

    def create_column_list(self, column_blocks: dict):
        table_list = []
        table = "| "
        for cell_block in column_blocks:
            blocks = self._client.get_children(cell_block["id"])
            block_str = self.to_string(blocks).replace('\n\n', '<br/>')
            table_list.append(block_str)
            table += block_str
            table += " |"
        table += "\n"
        table += ("| " + " | ".join(["----"] * len(table_list)) + " |" + "\n\n")
        return table

    def collect_info(self, payload: dict) -> dict:
        info = dict()
        if "rich_text" in payload:
            info["text"] = richtext_convertor(payload["rich_text"])
        if "icon" in payload:
            info["icon"] = payload["icon"]["emoji"]
        if "checked" in payload:
            info["checked"] = payload["checked"]
        if "expression" in payload:
            info["text"] = payload["expression"]
        if "url" in payload:
            info["url"] = payload["url"]
        if "caption" in payload:
            info["caption"] = richtext_convertor(payload["caption"])
        if "external" in payload:
            info["url"] = payload["external"]["url"]
            name, file_path = self.download_file(info["url"])
            info["file_name"] = name
            info["file_path"] = file_path
        if "language" in payload:
            info["language"] = payload["language"]
        # interal url
        if "file" in payload:
            info["url"] = payload["file"]["url"]
            name, file_path = self.download_file(info["url"])
            info["file_name"] = name
            info["file_path"] = file_path
        # table cells
        return info

    def download_file(self, url: str) -> str:
        file_name = os.path.basename(urlparse(url).path)
        if self.download:
            if file_name:
                name, extension = os.path.splitext(file_name)

                if not extension:
                    return file_name, url

                url_hash = hashlib.blake2s(
                    urlparse(url).path.encode()
                ).hexdigest()[:8]
                downloaded_file_name = f"{url_hash}_{file_name}"

                fullpath = os.path.join(
                    self.tmp_path, downloaded_file_name
                )

                request.urlretrieve(url, fullpath)
                return name, downloaded_file_name
            else:
                logging.error(f"invalid {url}")
        else:
            return file_name, url

    def to_string(self, blocks: dict) -> str:
        return self.convert(blocks)


def check_block_is_blank(block, block_type):
    return (
        block_type == "paragraph"
        and not block["has_children"]
        and not block[block_type]["rich_text"]
    )


# Converting Methods
def paragraph(info: dict) -> str:
    return info["text"]


def heading_1(info: dict) -> str:
    return f"# {info['text']}"


def heading_2(info: dict) -> str:
    return f"## {info['text']}"


def heading_3(info: dict) -> str:
    return f"### {info['text']}"


def callout(info: dict) -> str:
    return f"{info['icon']} {info['text']}"


def quote(info: dict) -> str:
    return f"> {info['text']}"


# toggle item will be changed as bulleted list item
def bulleted_list_item(info: dict) -> str:
    return f"- {info['text']}"


# numbering is not supported
def numbered_list_item(info: dict) -> str:
    """
    input: item:dict = {"number":int, "text":str}
    """
    return f"1. {info['text']}"


def to_do(info: dict) -> str:
    """
    input: item:dict = {"checked":bool, "test":str}
    """
    return f"- {'[x]' if info['checked'] else '[ ]'} {info['text']}"


# not yet supported
# child_database will be changed as child page
# def child_page(info:dict) -> str:
#     """
#     input: item:dict = {"id":str,"text":str}
#     """
#     #make_page(info['id'])
#     text = info['text']
#     return f'[{text}]({text})'


def code(info: dict) -> str:
    """
    input: item:dict = {"language":str,"text":str}
    """
    return f"\n```{info['language']}\n{info['text']}\n```"


def embed(info: dict) -> str:
    """
    input: item:dict ={"url":str,"text":str}
    """
    return f"[{info['url']}]({info['url']})"


def image(info: dict) -> str:
    """
    input: item:dict ={"url":str,"text":str,"caption":str}
    """
    # name,file_path = downloader(info['url'])

    if info["caption"]:
        return (
            f"![{info['file_name']}]({info['file_path']})\n\n{info['caption']}"
        )
    else:
        return f"![{info['file_name']}]({info['file_path']})"


def file(info: dict) -> str:
    # name,file_path = downloader(info['url'])
    return f"[{info['file_name']}]({info['file_path']})"


def bookmark(info: dict) -> str:
    """
    input: item:dict ={"url":str,"text":str,"caption":str}
    """
    if info["caption"]:
        return f"[{info['url']}]({info['url']})\n\n{info['caption']}"
    else:
        return f"[{info['url']}]({info['url']})"


def equation(info: dict) -> str:
    return f" $${info['text']}$$ "


def divider(info: dict) -> str:
    return "---"


def blank() -> str:
    return "<br/>"


def table_row(info: list) -> list:
    """
    input: item:list = [[richtext],....]
    """
    column_list = []
    for column in info["cells"]:
        column_list.append(richtext_convertor(column))
    return column_list


def column_list(info: list) -> list:
    """
    input: item:list = [[richtext],....]
    """
    column_list = []
    # for column in info["cells"]:
    # column_list.append(richtext_convertor(column))
    return "[//]: # column_list"


def column_str(info: list) -> str:
    """
    input: item:list = [[richtext],....]
    """
    return "[//]: # column"

# Since Synced Block has only child blocks, not name, it will return blank


def synced_block(info: list) -> str:
    return "[//]: # (Synced Block)"


# Block type map
BLOCK_TYPES = {
    "paragraph": paragraph,
    "heading_1": heading_1,
    "heading_2": heading_2,
    "heading_3": heading_3,
    "callout": callout,
    "toggle": bulleted_list_item,
    "quote": quote,
    "bulleted_list_item": bulleted_list_item,
    "numbered_list_item": numbered_list_item,
    "to_do": to_do,
    # "child_page": child_page,
    "code": code,
    "embed": embed,
    "image": image,
    "bookmark": bookmark,
    "equation": equation,
    "divider": divider,
    "file": file,
    "table_row": table_row,
    "column_list": column_list,
    "column": column_str,
    "synced_block": synced_block,
}
