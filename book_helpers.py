import os
import requests

from urllib.parse import quote
from flask import redirect, render_template, request, session
from functools import wraps

def make_https(url):
    if isinstance(url, str) and url.startswith('http://'):
        url = url.replace('http://', 'https://')
    return url

class BookClient(object):

    def __init__(self):
        self.host = "www.googleapis.com/books/v1/volumes"
        self.session = requests.session()
        self.session.header =  self.host

    def _get(self, path):
        try:
            response = self.session.get('https://{}'.format(self.host) + path)
            response.raise_for_status()
        except requests.RequestException:
            return None

        try:
            return response.json()

        except (KeyError, TypeError, ValueError):
            return None

    def search_any(self, query):
        path = '?q={}&printType=books&projection=lite&langRestrict=en'.format(quote(query))
        response = self._get(path)
        raw = response['items']
        booklist = []
        for row in raw:
            mydict = {
                "id": row['id'],
                "title": row['volumeInfo']['title'],
                "authors": row['volumeInfo'].get('authors', []),
                "publisher": row['volumeInfo'].get('publisher'),
                "description": row['volumeInfo'].get('description'),
                "smallimage": make_https(row['volumeInfo'].get('imageLinks', {}).get('thumbnail')),
                "mediumimage": make_https(row['volumeInfo'].get('imageLinks', {}).get('medium')),
                "largeimage": make_https(row['volumeInfo'].get('imageLinks', {}).get('large'))
            }
            booklist.append(mydict)
        return booklist

    #path = '?q=intitle:{}&printType=books&projection=lite'.format(quote(title))
    #path = '?q=inauthor:{}&printType=books&projection=lite'.format(quote(author))
    #path = '?q=subject:{}&printType=books&projection=lite'.format(quote(subject))
    #path = '?q=isbn:{}&printType=books&projection=lite'.format(quote(isbn))

    def get_id(self, volume_id):
        path = '/{}?&projection=lite&langRestrict=en'.format(quote(volume_id))
        response = self._get(path)
        raw = response
        book = {
            "id": raw['id'],
            "title": raw['volumeInfo']['title'],
            "authors": raw['volumeInfo'].get('authors', []),
            "publisher": raw['volumeInfo'].get('publisher'),
            "description": raw['volumeInfo'].get('description'),
           "smallimage": make_https(raw['volumeInfo'].get('imageLinks', {}).get('thumbnail')),
            "mediumimage": make_https(raw['volumeInfo'].get('imageLinks', {}).get('medium')),
            "largeimage": make_https(raw['volumeInfo'].get('imageLinks', {}).get('large'))
        }
        return book


#client = BookClient()

#r = client.search_any("'alice in wonderland'")
#print(r)




