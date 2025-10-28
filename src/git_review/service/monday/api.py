import os

import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader


def fetch_monday_item_details(item_id: int):
    """
    Fetch item details from Monday.com API.

    Args:
        item_id (int): The ID of the item to fetch.

    Returns:
        tuple: A tuple containing the item name and its updates.
    """

    load_dotenv()
    apiKey = os.getenv("MONDAY_API_KEY")

    apiUrl = "https://api.monday.com/v2"
    headers = {"Authorization": apiKey}

    env = Environment(loader=FileSystemLoader("src/git_review/service/monday/templates"))
    query_template = env.get_template("graphql.jinja")

    query = query_template.render(item_id=item_id)

    data = {"query": query}

    res = requests.post(url=apiUrl, json=data, headers=headers)
    result = res.json()

    # FIXME: エラーハンドリングを追加する
    # FIXME: return res.json() だけで良い。呼び出し元で処理するようにする

    item_name = result["data"]["items"][0]["name"]
    item_updates_list = result["data"]["items"][0]["updates"]
    item_updates_str = "\n".join([update["body"] for update in item_updates_list][::-1])

    return item_name, item_updates_str
