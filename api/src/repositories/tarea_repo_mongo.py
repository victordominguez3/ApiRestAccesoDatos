from pymongo import MongoClient
from src.models.tarea import Tarea
import uuid
from datetime import datetime
from typing import List

class TareaRepoMongo():

    def __init__(self, coleccion: str, user: str, password: str):
        client = MongoClient(f"mongodb://{user}:{password}@mongo:27017/")
        #client = MongoClient(f"mongodb://root:example@mongo:27017/")
        self.db = client.mongodb
        self.coleccion_tarea = self.db[coleccion]

        try: self.db.command("serverStatus")
        except Exception as e: print(e)
        else: print("Connected to MongoDB tasks!")

    def get_tareas(self, email: str) -> List[Tarea]:
        cursor = self.coleccion_tarea.find({"email": email})
        if cursor is None: return None
        tareas = []
        for documento in cursor:
            tarea = Tarea(
                email = documento.get("email", ""),
                title = documento.get("title", ""),
                text = documento.get("text", ""),
                checked = documento.get("checked", False),
                important = documento.get("important", False),
                priority = documento.get("priority", 0),
                id = documento.get("id", str(uuid.uuid4())),
                fCreated = documento.get("fCreated", datetime.now()),
                fUpdated = documento.get("fUpdated", datetime.now()))
            tareas.append(tarea)
        return tareas
    
    def get_tarea_by_id(self, email: str, id_tarea) -> Tarea:
        cursor = self.coleccion_tarea.find_one({"email": email, "id": id_tarea})
        if cursor is None: return None
        return Tarea(
                email = cursor.get("email", ""),
                title = cursor.get("title", ""),
                text = cursor.get("text", ""),
                checked = cursor.get("checked", False),
                important = cursor.get("important", False),
                priority = cursor.get("priority", 0),
                id = cursor.get("id", str(uuid.uuid4())),
                fCreated = cursor.get("fCreated", datetime.now()),
                fUpdated = cursor.get("fUpdated", datetime.now()))

    def save_tarea(self, email: str, tarea: Tarea):
        query = {"email": email, "id": tarea.id}
        data = {"$set": tarea.__dict__}
        result = self.coleccion_tarea.update_one(query, data, upsert=True)
        if result.matched_count > 0 or result.upserted_id: return tarea
        return None
        
    def delete_tarea(self, email: str, id_tarea: str) -> bool:
        self.coleccion_tarea.delete_one({"email":email, "id":id_tarea})
        result = self.get_tarea_by_id(email, id_tarea)
        if result is None: return True
        return False

    def delete_all_tareas(self, email: str) -> bool:
        self.coleccion_tarea.delete_many({"email":email})
        result = self.get_tareas(email)
        if result is None or result == []: return True
        return False
    
    def filter(self, lista: List[Tarea], code: str) -> List[Tarea]:
        if code == "checked": return [tarea for tarea in lista if tarea.checked]
        if code == "important": return [tarea for tarea in lista if tarea.important]
        if code == "notchecked": return [tarea for tarea in lista if not tarea.checked]
        if code == "notimportant": return [tarea for tarea in lista if not tarea.important]

    def order(self, lista: List[Tarea], code: str, reverse: bool) -> List[Tarea]:
        if code == "title": return sorted(lista, key=lambda tarea: tarea.title, reverse=reverse)
        if code == "priority": return sorted(lista, key=lambda tarea: tarea.priority, reverse=reverse)
        if code == "updated_date": return sorted(lista, key=lambda tarea: tarea.fUpdated, reverse=reverse)
        if code == "created_date": return sorted(lista, key=lambda tarea: tarea.fCreated, reverse=reverse)