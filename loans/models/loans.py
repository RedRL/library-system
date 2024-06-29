class Loan:
    def __init__(self, member_name, isbn, loan_date, title, book_id):
        self.member_name = member_name
        self.isbn = isbn
        self.loan_date = loan_date
        self.title = title
        self.book_id = book_id

    def to_dict(self):
        # Convert the Book object to a dictionary
        return {
            'memberName': self.member_name,
            'ISBN': self.isbn,
            'loanDate': self.loan_date,
            'title': self.title,
            'bookID': self.book_id,
        }
