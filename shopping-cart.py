#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import cgi
import urllib
import logging
import json

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GENRE = 'Fiction'
#MAIN_URL = 'http://localhost:10080/'
MAIN_URL = 'https://satyajeet-gawas-shopping-cart.appspot.com/'


def bookstore_key(genre_name=DEFAULT_GENRE):
    """Constructs a Datastore key for a Bookstore entity.
    We use genre as the key.
    """
    genre_name = genre_name.upper()
    return ndb.Key('Bookstore', genre_name)

#cart key
def cart_key(cart_key):
    """Constructs a Datastore key for a cart entity.
    We use genre as the key.
    """
    return ndb.Key('Cart', cart_key)


class Book(ndb.Model):
    """A main model for representing an individual Bookstore entry."""
    author = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    price = ndb.FloatProperty(indexed=False)
    genre = ndb.StringProperty(indexed=True)


class Cart(ndb.Model):
    item = ndb.StructuredProperty(Book);




class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'main_url': MAIN_URL,
        }
        if self.request.cookies.get('key') is None:
            handmade_key = db.Key.from_path('Cart', 1)
            first_batch = db.allocate_ids(handmade_key, 1)
            cart_id = first_batch[0]
            new_key = db.Key.from_path('Cart', cart_id)
            self.response.headers.add_header('Set-Cookie', 'key='+str(new_key))
        logging.info(self.request.cookies.get('key'))
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

class Display(webapp2.RequestHandler):
    def get(self):
        genre = self.request.get('genre_name')
        items = self.request.get('items')
        bookstore_query = Book.query(
            ancestor=bookstore_key(genre))
        books = bookstore_query.fetch(50)
        template_values = {
            'main_url': MAIN_URL,
            'books': books,
            'genre': genre,
            'items': items,
            
        }
        template = JINJA_ENVIRONMENT.get_template('display.html')
        self.response.write(template.render(template_values))
        

class Enter(webapp2.RequestHandler):
    def get(self):
        genre_name = self.request.get('genre_name')
        genre_entry = "Non-fiction"
        if genre_name:
            genre_entry = genre_name
        template_values = {
            'main_url': MAIN_URL,
            'genre_name':genre_entry,

        }
        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))
  
    def post(self):
        genre = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        logging.info(genre)
        book = Book(id=self.request.get('title'),parent=bookstore_key(genre))

        book.author = self.request.get('author')
        book.title = self.request.get('title')
        book.genre = self.request.get("genre_name")
        book.price = float(self.request.get("price"))
        key = book.put()
        self.redirect('/display?genre_name=' + genre)

# class Add(webapp2.RequestHandler):
    

class Search(webapp2.RequestHandler):
     def get(self):
        genre_name = self.request.get('genre_name')
        genre_entry = "Non-fiction"
        items = self.request.get('items')
        if genre_name:
            genre_entry = genre_name
        template_values = {
            'main_url': MAIN_URL,
            'genre':genre_entry,
            'items':items
        }
        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))
     def post(self):
        genre = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        author = self.request.get('author')
        bookstore_query = Book.query(
            ancestor=bookstore_key(genre))
        books = bookstore_query.fetch()
        temp_books = []
        if author:
            for book in books:
                if author.upper() in book.author.upper():
                    temp_books.append(book)

            books = temp_books
        template_values = {
            'queried': 'TRUE',
            'main_url': MAIN_URL,
            'books': books,
            'genre': genre,
            
        }
        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))
                


class AddToCart(webapp2.RequestHandler):
    def post(self):
        cart_id = self.request.cookies.get('key')
        called_from = self.request.get('source')
        logging.info('Add To Cart with key '+cart_id)
        book_list = self.request.get('book_list')
        books = book_list.split(";")
        n_items = 0
        for book in books:
            prop_array = book.split('+')
            if len(prop_array) == 4:
                n_items = n_items+1
                cart = Cart(parent=cart_key(self.request.cookies.get('key')))
                cart.item = Book(author=prop_array[0],title=prop_array[1],
                    genre=prop_array[3],price=float(prop_array[2]))
                cart.put()
        src = self.request.get('source')
        genre_name = self.request.get('genre_name')
        if 'display' in self.request.referer:
            self.redirect('/display?genre_name='+genre_name+'&items='+str(n_items))
        else:
            self.redirect('/search?'+'&items='+str(n_items))
              



class ViewCart(webapp2.RequestHandler):
    def get(self):
        cart_id = self.request.cookies.get("key")
        cart_query = Cart.query(
            ancestor=cart_key(cart_id))
        items = cart_query.fetch(50)
        total = 0
        for cart_item in items:
            total = total + cart_item.item.price
        template_values = {
            'main_url': MAIN_URL,
            'items': items,
            'total': total
        }
        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))



class Delete(webapp2.RequestHandler):
    def get(self):
        cart_id = self.request.cookies.get("key")
        cart_query = Cart.query(
            ancestor=cart_key(cart_id))
        items = cart_query.fetch(50)
        cart = Cart(parent=cart_key(self.request.cookies.get('key')))
        del_item = self.request.get('item_id')
        index = self.request.get('index')
        i = 1
        for cart_item in items:
            if cart_item.item.title == del_item:
               if i == int(index):
                cart_item.key.delete()
            i=i+1
        self.redirect('/cart')



class Checkout(webapp2.RequestHandler):
    def post(self):
        cart_id = self.request.cookies.get("key")
        cart_query = Cart.query(
            ancestor=cart_key(cart_id))
        items = cart_query.fetch(50)
        cart = Cart(parent=cart_key(self.request.cookies.get('key')))
        i = 0 
        total = 0
        for cart_item in items:
            cart_item.key.delete()
            i=i+1
            total = total + cart_item.item.price

        template_values = {
            'main_url': MAIN_URL,
            'items': i,
            'amount': total
        }
        template = JINJA_ENVIRONMENT.get_template('checkout.html')
        self.response.write(template.render(template_values))



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/display', Display),('/enter', Enter),('/add', Enter),('/search',Search),('/addtocart',AddToCart),('/cart',ViewCart),
    ('/delete',Delete),('/checkout',Checkout),
], debug=True)