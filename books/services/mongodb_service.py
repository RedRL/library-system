import os
import logging
from bson import ObjectId
from pymongo import MongoClient

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self, host='mongo', port=27017, books_db_name='books', ratings_db_name='ratings'):
        mongo_uri = os.getenv('MONGO_URI', f'mongodb://{host}:{port}/')
        self.client = MongoClient(mongo_uri)
        self.books_db = self.client[books_db_name]
        self.ratings_db = self.client[ratings_db_name]
        self.books_collection = self.books_db['books']
        self.ratings_collection = self.ratings_db['ratings']
        logger.debug(f"MongoDBService initialized with URI: {mongo_uri}")

    # Books Collection Operations
    def get_book(self, id):
        logger.debug(f"Fetching book with ID: {id}")
        book = self.books_collection.find_one({'_id': ObjectId(id)})
        if book:
            book['id'] = str(book.pop('_id'))  # change _id to id and convert ObjectId to string
        logger.debug(f"Found book: {book}")
        return book

    def get_book_by_isbn(self, isbn):
        logger.debug(f"Fetching book with ISBN: {isbn}")
        book = self.books_collection.find_one({'ISBN': isbn})
        if book:
            book['id'] = str(book.pop('_id'))
        logger.debug(f"Found book: {book}")
        return book

    def get_all_books(self):
        logger.debug("Fetching all books")
        try:
            books = list(self.books_collection.find())
            logger.debug(f"Raw books from DB: {books}")

            for book in books:
                book['id'] = str(book.pop('_id'))

            logger.debug(f"Processed books: {books}")
            return books
        except Exception as e:
            logger.error(f"Error fetching books: {e}", exc_info=True)
            raise

    def insert_book(self, book):
        book_dict = book.to_dict()
        logger.debug(f"Inserting book into MongoDB: {book_dict}")
        result = self.books_collection.insert_one(book_dict)
        logger.debug(f"Inserted book with ID: {result.inserted_id}")
        return result.inserted_id

    def update_book(self, id, updated_data):
        logger.debug(f"Updating book with ID: {id} with data: {updated_data}")
        result = self.books_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
        logger.debug(f"Updated book count: {result.modified_count}")
        return result.modified_count

    def delete_book(self, id):
        logger.debug(f"Deleting book with ID: {id}")
        result = self.books_collection.delete_one({'_id': ObjectId(id)})
        logger.debug(f"Deleted book count: {result.deleted_count}")
        return result.deleted_count

    # Ratings Collection Operations
    def get_rating(self, id):
        logger.debug(f"Fetching rating with ID: {id}")
        rating = self.ratings_collection.find_one({'_id': ObjectId(id)})
        logger.debug(f"Found rating: {rating}")
        return rating

    def get_all_ratings(self):
        logger.debug("Fetching all ratings")
        ratings_list = list(self.ratings_collection.find())
        for rating in ratings_list:
            rating['id'] = str(rating.pop('_id'))
        logger.debug(f"Found ratings: {ratings_list}")
        return ratings_list

    def insert_rating(self, rating, book_id):
        rating_dict = rating.to_dict()
        rating_dict['_id'] = book_id
        logger.debug(f"Inserting rating into MongoDB: {rating_dict}")
        result = self.ratings_collection.insert_one(rating_dict)
        logger.debug(f"Inserted rating with ID: {result.inserted_id}")
        return result.inserted_id

    def update_rating(self, rating_id, updated_data):
        logger.debug(f"Updating rating with ID: {rating_id} with data: {updated_data}")
        result = self.ratings_collection.update_one({'_id': ObjectId(rating_id)}, {'$set': updated_data})
        logger.debug(f"Updated rating count: {result.modified_count}")
        return result.modified_count

    def delete_rating(self, id):
        logger.debug(f"Deleting rating with ID: {id}")
        result = self.ratings_collection.delete_one({'_id': ObjectId(id)})
        logger.debug(f"Deleted rating count: {result.deleted_count}")
        return result.deleted_count
