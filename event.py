import uuid

class Event():
    """docstring for Event."""

    def __init__(self, title, date, description=""):
        self.id = str(uuid.uuid4())
        self.updated = None
        self.title = title
        self.description = description
        self.url = None
        self.status = 'new'        

        if not date:
            self.date = {
                'start': None,
                'end': None
                }
        else:
            date = date
