import uuid

class Usuario():
    def __init__(self, email, password, name, isVerified = None, verificationCode = None):
        self.email = email
        self.password = password
        self.name = name
        self.isVerified = isVerified if isVerified is not None else False
        self.verificationCode = verificationCode if verificationCode is not None else str(uuid.uuid4())