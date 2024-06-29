import os
import requests


def get_book_title_and_id(isbn):
    # books_service_host = os.getenv('BOOKS_SERVICE_HOST', 'books_service')
    books_service_host = os.getenv('BOOKS_SERVICE_HOST', 'localhost')
    books_service_port = os.getenv('BOOKS_SERVICE_PORT', '5000')
    api_key = os.getenv('BOOKS_SERVICE_API_KEY', 'your-secure-api-key')

    try:
        # Construct the URL using environment variables and the provided ISBN
        url = f'http://{books_service_host}:{books_service_port}/books/isbn/{isbn}'
        headers = {'API-KEY': api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        book_data = response.json()
        return book_data['title'], book_data['id']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching book data: {e}")
        return None, None
