class Rating:
    def __init__(self, title):
        self.title = title
        self.values = []
        self.average = 0

    def to_dict(self):
        # Convert the Rating object to a dictionary
        return {
            'title': self.title,
            'values': self.values,
            'average': self.average,
        }

    def add_value(self, new_rating):
        # Add a new value to the values array
        self.values.append(new_rating)

