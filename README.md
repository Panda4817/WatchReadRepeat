# CS50x 2020 Final Project - Web application: Watch-Read-Repeat

## About

A website where you login and keep track of movies and tv shows you have watched, are watching or want to watch.
Also the site lets you keep track of books you are reading, already read or want to read.
The dashboard presents the user's data visually using bar charts, top 5 lists through the user's ratings, carousel of movies posters and books covers.

I have deployed the website on pythonAnywhere: [Link](https://watchreadrepeat.eu.pythonanywhere.com/)

## Programming used

It uses python and flask with SQL database for back-end.
It uses HTML, CSS with Bootstrap4, Javascript, jquery and AJAX for front-end.

## API usage

I have created a movie client and book client to make api calls.
The movie client makes calls to an api that searches IMDB database.
The book client makes calls to Google Books API that seaches for data on books.

## Project files

- Application.py
- Helpers.py files (movie, book, apology, login)
- SQLite3 database with several tables including, user data(with password hash) and book and movie/tv data tables
- Static files (styles.css, logo for browser)
- Templates folder (html files including index.html)
- Any sensitive information is stored as environment variables
