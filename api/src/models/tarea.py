import uuid
from datetime import datetime

class Tarea():
    def __init__(self, email: str, title: str, text: str, checked: bool, important: bool, priority: int, id: str = None, fCreated = None, fUpdated = None):
        self.email = email
        self.id = id if id is not None else str(uuid.uuid4())
        self.title = title
        self.text = text
        self.fCreated = fCreated if fCreated is not None else datetime.now()
        self.fUpdated = fUpdated if fUpdated is not None else datetime.now()
        self.checked = checked
        self.important = important
        self.priority = priority