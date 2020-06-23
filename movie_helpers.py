import os
import requests
import logging

from urllib.parse import quote
from flask import redirect, render_template, request, session
from functools import wraps


logger = logging.getLogger()
api_key = os.getenv("API_KEY")

class MovieClient(object):

    def __init__(self):
        self.host = "imdb-internet-movie-database-unofficial.p.rapidapi.com"
        self.key = api_key
        self.session = requests.session()
        self.session.headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.key,
        }

    def _get(self, path):
        try:
            response = self.session.get('https://{}'.format(self.host) + path)
            logger.info(response.status_code)
            response.raise_for_status()
        except requests.RequestException:
            return None

        try:
            return response.json()
        except (KeyError, TypeError, ValueError):
            return None


    def search_titles(self, query):
        path = '/search/{}'.format(quote(query))
        response = self._get(path)
        return response['titles']

    def get_film(self, film_id):
        path = '/film/{}'.format(film_id)
        response = self._get(path)
        return response

#client.search_titles("killing eve")






