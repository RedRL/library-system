from flask import Blueprint, jsonify, request
from models.loans import Loan
import re
from services.mongodb_service import MongoDBService

controllers_bp = Blueprint('controllers', __name__)

# Create a global instance of MongoDBService
mongodb_service = MongoDBService()


# Define /loans route for GET and POST requests
@controllers_bp.route('/loans', methods=['GET', 'POST'])
def loans():
    if request.method == 'GET':
        try:
            res_loans_list = mongodb_service.get_all_loans()
        except Exception as e:
            error_message = f"Error fetching loans from the database: {str(e)}"
            return jsonify({'error': error_message}), 500

        keys = list(request.args.keys())

        # Define a list of allowed query parameters
        allowed_params = {'memberName', 'isbn', 'ISBN', 'title', 'loanID', 'loanDate', 'loanID'}
        # Check for invalid query parameters
        invalid_params = [key for key in keys if key not in allowed_params]
        if invalid_params:
            return jsonify({"error": f"Invalid query parameters: {', '.join(invalid_params)}. "
                                     f"Parameters allowed - {allowed_params - {'isbn'} }"}), 422

        # Validate parameters' values
        errors = validate_query_params()
        if errors:
            return jsonify(errors), 422

        # Filter loans according to query
        for key in keys:
            # Check if loans need to be filtered by some field
            fields = allowed_params
            if key in fields and (key + '=') in request.url:
                values = request.args.getlist(key)
                for value in values:
                    if key == 'isbn': key = 'ISBN'
                    if key == 'ID': key = 'id'
                    res_loans_list = [loan for loan in res_loans_list if loan[key] == value]

        # Return a list of all the loans
        return jsonify(res_loans_list), 200

    elif request.method == 'POST':
        # Check if the request content type is JSON
        if request.content_type != 'application/json':
            return jsonify({"error": "Unsupported media type. Only JSON data is supported."}), 415

        # Get the JSON data from the request
        loan_data = request.json
        member_name = loan_data.get('memberName')
        loan_date = loan_data.get('loanDate')
        isbn = loan_data.get('isbn')
        if not isbn:
            isbn = loan_data.get('ISBN')

        if not member_name or not isbn or not loan_date:
            return jsonify({"error": "Please provide all three fields - 'memberName', 'ISBN', and 'loanDate'"}), 422

        if member_name and not isinstance(member_name, str):
            return jsonify({"error": "'memberName' must be a string"}), 422

        if isbn and (not isinstance(isbn, str) or not isbn.isnumeric() or not len(isbn) == 13):
            return jsonify({"error": "'ISBN' must be a string of 13 digit"}), 422

        if not loan_date or not re.match(r'^\d{4}-\d{2}-\d{2}$', loan_date):
            return jsonify({"error": "'loan_date' must be of format YYYY-MM-DD"}), 422

        try:
            book_data = mongodb_service.get_book_title_and_id(isbn)
            if not book_data['id']:
                return jsonify({"error": "The book with the provided ISBN wasn't found"}), 422

            found_loan = mongodb_service.get_loan_by_isbn(isbn)
            if found_loan:
                return jsonify({"error": "There already exists a loan for the book with the provided ISBN"}), 422

            number_of_member_loans = mongodb_service.count_loans_by_member_name(member_name)
            if number_of_member_loans >= 2:
                return jsonify({"error": "Member already has 2 or more books on loan"}), 422

            # Set new loan instance with received data - 'memberName', 'ISBN', 'loanDate'
            new_loan = Loan(member_name, isbn, loan_date, book_data['title'], book_data['id'])

            # Insert the new loan instance to the Mongo databases
            loan_id = mongodb_service.insert_loan(new_loan)

        except Exception as e:
            error_message = f"Error storing data in database: {str(e)}"
            return jsonify({'error': error_message}), 500

        # return jsonify({"success": f"A new loan record has been created, with id={loan_id}"}), 201
        return jsonify({"loanID": f"{loan_id}"}), 201


def validate_query_params():
    params = request.args
    errors = []

    # Validate memberName
    member_name_values = params.getlist('memberName')
    for member_name_value in member_name_values:
        if not member_name_value or not isinstance(member_name_value, str):
            errors.append("'memberName' must be a non-empty string")
            break

    # Validate ISBN
    isbn_values = params.getlist('isbn') + params.getlist('ISBN')
    for isbn_value in isbn_values:
        if not isbn_value or not isbn_value.isnumeric() or len(isbn_value) != 13:
            errors.append("'ISBN' must be 13 digits or 'missing'")
            break

    # Validate title
    title_values = params.getlist('title')
    for title_value in title_values:
        if not title_value:
            errors.append("'title' must have a value (including 'missing')")
            break

    # Validate loanID
    loan_id_values = params.getlist('loanID')
    for loan_id_value in loan_id_values:
        if not loan_id_value or not isinstance(loan_id_value, str):
            errors.append("'loanID' must be a non-empty string")
            break

    # Validate loanDate
    loan_date_values = params.getlist('loanDate')
    for loan_date_value in loan_date_values:
        if not loan_date_value or not re.match(r'^\d{4}-\d{2}-\d{2}$', loan_date_value):
            errors.append("'loanDate' must be of format YYYY-MM-DD")
            break

    if errors:
        return {"error": "; ".join(errors)}


# Define /loans/{id} route for GET and DELETE
@controllers_bp.route('/loans/<id>', methods=['GET', 'DELETE'])
def loan_by_id(id):
    try:
        # Attempt to get the loan from the database
        loan = mongodb_service.get_loan(id)

        if loan:
            if request.method == 'GET':
                # Return the loan with the provided ID
                return jsonify(loan), 200

            elif request.method == 'DELETE':
                mongodb_service.delete_loan(id)
                return jsonify({"success": f"loan with ID={id} has been successfully deleted"}), 200

        # If no loan was found with the given ID
        return jsonify({"error": f"No loan found with ID={id}"}), 404

    except Exception as e:
        error_message = f"Error accessing the database: {str(e)}"
        return jsonify({'error': error_message}), 500
