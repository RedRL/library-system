import os
import requests
from bson import ObjectId
from pymongo import MongoClient


class MongoDBService:
    def __init__(self, host='mongo', port=27017, loans_db_name='loans'):
        mongo_uri = os.getenv('MONGO_URI', f'mongodb://{host}:{port}/{loans_db_name}')
        self.client = MongoClient(mongo_uri)
        self.loans_db = self.client.get_database()
        self.loans_collection = self.loans_db['loans']
        self.books_service_url = os.getenv('BOOKS_SERVICE_URL', 'http://books-service:5001')
        self.api_key = 'loans-service-api-key'  # API key for the books-service

    def get_loan(self, id):
        loan = self.loans_collection.find_one({'_id': ObjectId(id)})
        if loan:
            loan['loanID'] = str(loan.pop('_id'))  # change _id to id and convert ObjectId to string
        return loan

    def get_book_title_and_id(self, isbn):
        url = f"{self.books_service_url}/books/isbn/{isbn}"
        headers = {'API-KEY': self.api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # raise an exception for HTTP errors
        book_data = response.json()
        return {
            "title": book_data.get("title"),
            "id": book_data.get("id")
        }

    def get_loan_by_isbn(self, isbn):
        loan = self.loans_collection.find_one({'ISBN': isbn})
        if loan:
            loan['loanID'] = str(loan.pop('_id'))
        return loan

    def get_all_loans(self):
        loans = list(self.loans_collection.find())
        for loan in loans:
            loan['loanID'] = str(loan.pop('_id'))
        return loans

    def count_loans_by_member_name(self, member_name):
        count = self.loans_collection.count_documents({'memberName': member_name})
        return count

    def insert_loan(self, loan):
        loan_dict = loan.to_dict()
        result = self.loans_collection.insert_one(loan_dict)
        return result.inserted_id

    def delete_loan(self, id):
        result = self.loans_collection.delete_one({'_id': ObjectId(id)})
        return result.deleted_count
