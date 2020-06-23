import os
import requests

from urllib.parse import quote
from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

db = SQL("sqlite:////home/watchreadrepeat/watch_read_repeat/tracker.db")

def apology(message, code):
    if session.get("user_id") is not None:
        user = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])
        message = message
        code = code
        return render_template("apology.html", message=message, code=code, username=user[0]["username"])
    else:
        message = message
        code = code
        return render_template("apology.html", message=message, code=code)