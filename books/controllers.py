from flask import Blueprint, jsonify, request
from models.book import Book
from models.rating import Rating
from services.google_books_service import get_book_authors_publisher_published_date
from services.mongodb_service import MongoDBService
import re

controllers_bp = Blueprint('controllers', __name__)

# Create a global instance of MongoDBService
mongodb_service = MongoDBService(books_db_name='books', ratings_db_name='ratings')


# Define /books route for GET and POST requests
@controllers_bp.route('/books', methods=['GET', 'POST'])
def books():
    if request.method == 'GET':
        try:
            res_books_list = mongodb_service.get_all_books()
        except Exception as e:
            error_message = f"Error fetching books from the database: {str(e)}"
            return jsonify({'error': error_message}), 500

        keys = list(request.args.keys())

        # Define a list of allowed query parameters
        allowed_params = {'id', 'ID', 'title', 'authors', 'isbn', 'ISBN', 'genre', 'publisher', 'publishedDate'}
        # Check for invalid query parameters
        invalid_params = [key for key in keys if key not in allowed_params]
        if invalid_params:
            return jsonify({"error": f"Invalid query parameters: {', '.join(invalid_params)}. "
                                     f"Parameters allowed - {allowed_params - {'id', 'isbn'} }"}), 422

        # Validate parameters' values
        errors = validate_query_params()
        if errors:
            return jsonify(errors), 422

        # Filter books according to query
        for key in keys:
            # Check if books need to be filtered by some field
            fields = allowed_params
            if key in fields and (key + '=') in request.url:
                values = request.args.getlist(key)
                for value in values:
                    res_books_list = filtered_book_by_field(res_books_list, key, value)

        # Return a list of all the books
        return jsonify(res_books_list), 200

    elif request.method == 'POST':
        # Check if the request content type is JSON
        if request.content_type != 'application/json':
            return jsonify({"error": "Unsupported media type. Only JSON data is supported."}), 415

        # Get the JSON data from the request
        book_data = request.json
        title = book_data.get('title')
        genre = book_data.get('genre')
        isbn = book_data.get('isbn')
        if not isbn:
            isbn = book_data.get('ISBN')

        if not title or not isbn or not genre:
            return jsonify({"error": "Please provide all three fields - 'title', 'ISBN', and 'genre'"}), 422

        try:
            found_book = mongodb_service.get_book_by_isbn(isbn)
            if found_book:
                return jsonify({"error": "There already exists a book with the provided ISBN number"}), 422
        except Exception as e:
            error_message = f"Error accessing the database: {str(e)}"
            return jsonify({'error': error_message}), 500

        if title and not isinstance(title, str):
            return jsonify({"error": "'title' must be a string"}), 422

        if isbn and (not isinstance(isbn, str) or not isbn.isnumeric() or not len(isbn) == 13):
            return jsonify({"error": "'ISBN' must be a string of 13 digit"}), 422

        if (genre and genre not in
                ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']):
            return jsonify({"error": "'genre' must be one of 'Fiction', 'Children', 'Biography', 'Science',"
                                     "'Science Fiction', 'Fantasy', or 'Other'"}), 422

        # Set new book instance with received data - 'title', 'ISBN', 'genre'
        new_book = Book(title, isbn, genre)

        # Get additional book data - 'authors', 'publisher', 'publishedDate' - from the Google Books API
        res_err = load_authors_publisher_published_date(new_book)
        if res_err:
            return jsonify(res_err[0]), res_err[1]

        try:
            # Insert the new Book instance and its Rating instance to their appropriate Mongo databases
            # Use the MongoDB's generated IDs as the book and rating IDs
            book_id = mongodb_service.insert_book(new_book)
            print(f"Inserted book with ID: {book_id}")

            # Set a new Rating instance with the new book's id and title
            new_value = Rating(new_book.title)

            rating_id = mongodb_service.insert_rating(new_value, book_id)
            print(f"Inserted rating with ID: {rating_id}")

        except Exception as e:
            error_message = f"Error storing data in database: {str(e)}"
            return jsonify({'error': error_message}), 500

        # return jsonify({"success": f"A new book record has been created, with id={book_id}"}), 201
        return jsonify({"bookID": f"{book_id}"}), 201


def validate_query_params():
    params = request.args
    errors = []

    # Validate ID
    id_values = params.getlist('id') + params.getlist('ID')
    for id_value in id_values:
        if not id_value or not isinstance(id_value, str):
            errors.append("'ID' must be a non-empty string")
            break

    # Validate title
    title_values = params.getlist('title')
    for title_value in title_values:
        if not title_value:
            errors.append("'title' must have a value (including 'missing')")
            break

    # Validate authors
    authors_values = params.getlist('authors')
    for authors_value in authors_values:
        if not authors_value:
            errors.append("'authors' must have a value (including 'missing')")
            break

    # Validate ISBN
    isbn_values = params.getlist('isbn') + params.getlist('ISBN')
    for isbn_value in isbn_values:
        if not isbn_value or not isbn_value.isnumeric() or len(isbn_value) != 13:
            errors.append("'ISBN' must be 13 digits or 'missing'")
            break

    # Validate genre
    genre_values = params.getlist('genre')
    valid_genres = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other', 'missing']
    for genre_value in genre_values:
        if genre_value not in valid_genres:
            errors.append(
                f"'genre' must be either 'missing' or one of {', '.join(valid_genres)}"
            )
            break

    # Validate publisher
    publisher_values = params.getlist('publisher')
    for publisher_value in publisher_values:
        if not publisher_value:
            errors.append("'publisher' must have a value (including 'missing')")
            break

    # Validate publishedDate
    published_date_values = params.getlist('publishedDate')
    for published_date_value in published_date_values:
        if not published_date_value or not re.match(r'^\d{4}(-\d{2}-\d{2})?$', published_date_value):
            errors.append("'publishedDate' must be of format YYYY or YYYY-MM-DD, or 'missing'")
            break

    if errors:
        return {"error": "; ".join(errors)}


def filtered_book_by_field(res_books_list, key, value):
    if key != 'publishedDate':
        if key == 'isbn': key = 'ISBN'
        if key == 'ID': key = 'id'
        filtered_book_list = [book for book in res_books_list if book[key] == value]
    else:
        # '2014' query will find either '2014-01-01' or '2014'
        filtered_book_list = [book for book in res_books_list if
                              (book[key] == value or value == book[key].split('-')[0])]

    return filtered_book_list


def load_authors_publisher_published_date(book):
    res = get_book_authors_publisher_published_date(book.isbn)

    # If a numerical error was raised (0 or -1) -> return appropriate error
    if isinstance(res, int):
        if res == 0:
            return {"error": "No items returned from Google Book API for given ISBN number"}, 400
        return {"error": "Unable to connect to Google Book API"}, 500

    book.authors = res.get("authors", "missing")
    book.publisher = res.get("publisher", "missing")
    book.published_date = res.get("publishedDate", "missing")

    if book.authors != "missing":
        book.authors = authors_list_to_str(book.authors)


def authors_list_to_str(authors_list):
    if len(authors_list) == 1:
        return authors_list[0]

    authors_str = authors_list[0]
    for author_name in authors_list[1:len(authors_list)]:
        authors_str += " and " + author_name

    return authors_str


# Define /books/{id} route for GET, DELETE and PUT requests
@controllers_bp.route('/books/<id>', methods=['GET', 'DELETE', 'PUT'])
def book_by_id(id):
    try:
        # Attempt to get the book from the database
        book = mongodb_service.get_book(id)

        if book:
            if request.method == 'GET':
                # Return the book with the provided ID
                return jsonify(book), 200

            elif request.method == 'DELETE':
                # Delete the book and its ratings
                mongodb_service.delete_book(id)
                mongodb_service.delete_rating(id)
                return jsonify({"success": f"Book with ID={id} has been successfully deleted"}), 200

            elif request.method == 'PUT':
                # Check if the request content type is JSON
                if request.content_type != 'application/json':
                    return jsonify({"error": "Unsupported media type. Only JSON data is supported"}), 415

                # Get the JSON data from the request
                updated_book_data = request.json
                res = update_book(id, updated_book_data)

                # If the book was successfully updated, update the relevant book title in the ratings db as well
                if res[1] == 200:
                    book_rating = mongodb_service.get_rating(id)
                    book_rating['title'] = book['title']
                    mongodb_service.update_rating(id, book_rating)

                return jsonify(res[0]), res[1]

        # If no book was found with the given ID
        return jsonify({"error": f"No book found with ID={id}"}), 404

    except Exception as e:
        error_message = f"Error accessing the database: {str(e)}"
        return jsonify({'error': error_message}), 500


def update_book(id, updated_book_data):
    # Ensure that all required fields are provided in the request JSON
    required_fields = ['title', 'ISBN', 'genre', 'authors', 'publisher', 'publishedDate']
    missing_fields = []
    for field in required_fields:
        if field not in updated_book_data:
            missing_fields.append(field)

    if missing_fields:
        return {"error": f"Missing required fields: {missing_fields}"}, 422

    # Validate the updated book information
    errors = get_book_errors(updated_book_data)
    if errors:
        return errors, 422

    # Update the book
    mongodb_service.update_book(id, updated_book_data)

    return {"success": f"Book with ID={id} has been successfully updated"}, 200


def get_book_errors(book_info):
    errors = []

    # Validate 'title' field - non-empty string
    title = book_info['title']
    if not title or not isinstance(title, str):
        errors.append("'title' must be a non-empty string")

    # Validate 'authors' field - non-empty string
    authors = book_info['authors']
    if not authors or not isinstance(authors, str):
        errors.append("'authors' must be a non-empty string")

    # Validate 'ISBN' field - 13 digits string
    isbn = book_info['ISBN']
    if not isinstance(isbn, str) or not isbn.isnumeric() or len(isbn) != 13:
        errors.append("'ISBN' must be a string of 13 digits")

    # Validate 'publisher' field - non-empty string
    publisher = book_info['publisher']
    if not publisher or not isinstance(publisher, str):
        errors.append("'publisher' must be a non-empty string")

    # Validate 'publishedDate' field - either YYYY or YYYY-MM-DD format
    published_date = book_info['publishedDate']
    if not isinstance(published_date, str) or not re.match(r'^\d{4}(-\d{2}-\d{2})?$', published_date):
        errors.append("'publishedDate' must be a string of format YYYY or YYYY-MM-DD")

    # Validate 'genre' field - one of the genre choices
    genre = book_info['genre']
    allowed_genres = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']
    if genre not in allowed_genres:
        errors.append("'genre' must be one of 'Fiction', 'Children', 'Biography', 'Science',"
                      "'Science Fiction', 'Fantasy', or 'Other'")

    if errors:
        return {"error": "; ".join(errors)}


# Define a /ratings route for GET request
@controllers_bp.route('/ratings', methods=['GET'])
def get_all_ratings():
    try:
        ratings = mongodb_service.get_all_ratings()
        return jsonify(ratings), 200
    except Exception as e:
        error_message = f"Error fetching ratings from the database: {str(e)}"
        return jsonify({'error': error_message}), 500


# Define a /ratings/{id} route for GET request
@controllers_bp.route('/ratings/<id>', methods=['GET'])
def get_rating(id):
    try:
        rating = mongodb_service.get_rating(id)
        if not rating:
            return jsonify({"error": f"ID={id} not found"}), 404
        rating['id'] = str(rating.pop('_id'))  # change _id to id and convert ObjectId to string
        return jsonify(rating), 200

    except Exception as e:
        error_message = f"Error fetching rating from the database: {str(e)}"
        return jsonify({'error': error_message}), 500


# Define a /ratings/{id}/values route for POST request
@controllers_bp.route('/ratings/<id>/values', methods=['POST'])
def ratings_id_value(id):
    try:
        rating = mongodb_service.get_rating(id)
        if not rating:
            return jsonify({"error": f"ID={id} not found"}), 404

        # Check if the request content type is JSON
        if request.content_type != 'application/json':
            return jsonify({"error": "Unsupported media type. Only JSON data is supported."}), 415

        # Extract the value from the JSON request
        data = request.json
        if 'value' not in data:
            return jsonify({"error": "Missing 'value' field in the request body"}), 422
        new_value = data.get('value')

        # Validate the value
        if not new_value or not isinstance(new_value, int) or new_value < 1 or new_value > 5:
            return jsonify({"error": "Invalid rating value. Must be an integer between 1 and 5."}), 422

        # Add the new rating value and updated average
        rating['values'].append(new_value)
        rating['average'] = round(sum(rating['values']) / len(rating['values']), 2)
        mongodb_service.update_rating(id, rating)

        # Return the updated average rating
        # return jsonify({"success": f"Average rating of '{rating['title']}' is {rating['average']}"}), 200
        return jsonify({"average": f"{rating['average']}"}), 201


    except Exception as e:
        error_message = f"Error accessing the database: {str(e)}"
        return jsonify({'error': error_message}), 500


# Define a /top route for GET request
@controllers_bp.route('/top', methods=['GET'])
def top_rated_books():
    try:
        books_ratings = mongodb_service.get_all_ratings()
    except Exception as e:
        error_message = f"Error fetching ratings from the database: {str(e)}"
        return jsonify({'error': error_message}), 500

    # Filter books' ratings that have at least 3 values
    filtered_books_ratings = [book_rating for book_rating in books_ratings if len(book_rating['values']) >= 3]
    if len(filtered_books_ratings) == 0:
        return jsonify([]), 200

    # Sort the filtered_book_ratings based on their average rating in descending order
    sorted_books_ratings = sorted(filtered_books_ratings, key=lambda obj: obj['average'], reverse=True)

    # Extract unique average ratings from sorted_book_ratings
    unique_averages = list(set(book_rating['average'] for book_rating in sorted_books_ratings))

    # Select the top 3 unique average ratings
    top_3_unique_averages = sorted(unique_averages, reverse=True)[:3]

    top_books_ratings = []
    # Iterate over sorted_book_ratings and append book_rating with average in top_3_unique_averages
    for book_rating in sorted_books_ratings:
        if book_rating['average'] in top_3_unique_averages:
            top_books_ratings.append(book_rating)

    # Create a JSON array of top-rated books
    top_books_json = []
    for book_rating in top_books_ratings:
        top_books_json.append({
            "id": book_rating['id'],
            "title": book_rating['title'],
            "average": book_rating['average']
        })

    # Return the JSON array
    return jsonify(top_books_json), 200


# Secure API key
# THIS IS A SIMPLIFIED MEASURE TO ENSURE THAT 'get_book_title_and_id(isbn)' IS TRIGGERED ONLY BY THE LOANS SERVICE
API_KEY = 'loans-service-api-key'


@controllers_bp.route('/books/isbn/<isbn>', methods=['GET'])
def get_book_title_and_id(isbn):
    # Check for the API key in the request headers
    api_key = request.headers.get('API-KEY')
    if api_key != API_KEY:
        return jsonify({'error': 'Forbidden: Invalid API key'}), 403

    try:
        # Attempt to get the book from the database
        book = mongodb_service.get_book_by_isbn(isbn)
        if book:
            return {
                "title": book['title'],
                "id": book['id']
            }
        else:
            return {}

    except Exception as e:
        error_message = f"Error accessing the database: {str(e)}"
        return jsonify({'error': error_message}), 500
