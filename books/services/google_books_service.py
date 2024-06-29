import requests

GOOGLE_BOOK_BY_ISBN_API = "https://www.googleapis.com/books/v1/volumes?q=isbn:"


def get_book_authors_publisher_published_date(isbn):
    # Make a request to Google books API to get the book's authors, publisher and published date
    try:
        response = requests.get(f'{GOOGLE_BOOK_BY_ISBN_API}{isbn}')
    except:
        return -1

    try:
        data = response.json()['items'][0]['volumeInfo']
        return data
    except:
        # If retrieving data failed, return the 'totalItems' retrieved (numerical value)
        # If retrieving 'totalItems' also fails return -1
        return response.json().get('totalItems', -1)
