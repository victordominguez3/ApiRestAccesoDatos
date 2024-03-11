from pymongo import MongoClient
from src.models.usuario import Usuario
import uuid

class UsuarioRepoMongo():
    
    def __init__(self, coleccion: str, user: str, password: str):
        client = MongoClient(f"mongodb://{user}:{password}@mongo:27017/")
        #client = MongoClient(f"mongodb://root:example@mongo:27017/")
        self.db = client.mongodb
        self.coleccion_usuario = self.db[coleccion]

        try: self.db.command("serverStatus")
        except Exception as e: print(e)
        else: print("Connected to MongoDB users!")

    def get_usuario(self, email: str, password: str) -> Usuario:
        cursor = self.coleccion_usuario.find_one({"email": email, "password": password})
        if cursor is None: return None
        return Usuario(
            email=cursor.get("email", ""),
            name=cursor.get("name", ""),
            password=cursor.get("password", ""),
            isVerified=cursor.get("isVerified", False),
            verificationCode=cursor.get("verificationCode", str(uuid.uuid4())))
        
    def save_usuario(self, usuario: Usuario, oldPassword: str) -> Usuario:
        query = {"email": usuario.email, "password": oldPassword}
        data = {"$set": usuario.__dict__}
        result = self.coleccion_usuario.update_one(query, data, upsert=True)
        if result.matched_count > 0 or result.upserted_id: return usuario
        return None
    
    def delete_usuario(self, email: str, password: str):
        self.coleccion_usuario.delete_one({"email":email, "password":password})

    def email_existe(self, email: str) -> bool:
        cursor = self.coleccion_usuario.find_one({"email": email})
        if cursor is not None: return True
        return False
    
    def is_verified(self, email: str) -> bool:
        cursor = self.coleccion_usuario.find_one({"email": email})
        if cursor is None: return False
        return bool(cursor.get("isVerified"))