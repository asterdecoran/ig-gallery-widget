import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

from notion_client import Client as NotionClient


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_notion_database(notion_token, database_id):
    """Get a Notion database's details."""
    try:
        notion = NotionClient(auth=notion_token)
        response = notion.databases.query(**{'database_id': database_id})
        items = []
        for item in response['results']:
            name = item['properties']['Name']['title'][0]['text']['content']
            publish_date: str = item['properties']['Publish Date']['date']['start']
            attachment = item['properties']['Attachment']['files'][0]['file']['url']

            items.append({
                'name': name,
                'publish_date': publish_date,
                'attachment': attachment
            })

        items.sort(key=lambda x: x['publish_date'], reverse=True)
        return items

    except Exception as e:
        print(f"Error connecting to Notion and/or retrieving Notion database: {e}")
        return None

