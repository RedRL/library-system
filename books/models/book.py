class Book:
    def __init__(self, title, isbn, genre):
        self.title = title
        self.isbn = isbn
        self.genre = genre
        self.authors = None
        self.publisher = None
        self.published_date = None

    def to_dict(self):
        # Convert the Book object to a dictionary
        return {
            'title': self.title,
            'ISBN': self.isbn,
            'genre': self.genre,
            'authors': self.authors,
            'publisher': self.publisher,
            'publishedDate': self.published_date
        }
