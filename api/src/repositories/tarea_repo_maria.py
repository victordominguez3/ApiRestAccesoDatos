from mariadb import mariadb
from src.models.tarea import Tarea
import uuid
from typing import List

class TareaRepoMaria():

    def __init__(self, connection, tabla: str):
        self.tabla = tabla
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {tabla} (
                            EMAIL VARCHAR(100),
                            ID VARCHAR(36) PRIMARY KEY,
                            TITLE VARCHAR(200),
                            TEXT VARCHAR(500),
                            FCREATED DATETIME,
                            FUPDATED DATETIME,
                            CHECKED BOOLEAN,
                            IMPORTANT BOOLEAN,
                            PRIORITY INT,
                            FOREIGN KEY (EMAIL) REFERENCES usuarios(EMAIL) ON DELETE CASCADE
        )""")
        self.connection.commit()
        print("Tabla tareas creada")

    def get_tareas(self, email: str):
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}'")
        return [Tarea(email = tarea[0],
                      id = tarea[1],
                      title = tarea[2],
                      text = tarea[3],
                      fCreated = tarea[4],
                      fUpdated = tarea[5],
                      checked = tarea[6],
                      important = tarea[7],
                      priority = tarea[8]) for tarea in self.cursor]
    
    def get_tarea_by_id(self, email: str, id_tarea) -> Tarea:
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}' AND ID = '{id_tarea}'")
        tarea = self.cursor.fetchone()
        if tarea is None: return None
        return Tarea(email = tarea[0],
                    id = tarea[1],
                    title = tarea[2],
                    text = tarea[3],
                    fCreated = tarea[4],
                    fUpdated = tarea[5],
                    checked = tarea[6],
                    important = tarea[7],
                    priority = tarea[8])

    def save_tarea(self, email: str, tarea: Tarea):
        result = self.get_tarea_by_id(email, tarea.id)
        if result is None: return self.new_tarea(tarea)
        return self.update_tarea(tarea)
    
    def new_tarea(self, tarea: Tarea):
        data = (tarea.email, tarea.id, tarea.title, tarea.text, tarea.fCreated, tarea.fUpdated, tarea.checked, tarea.important, tarea.priority)
        self.cursor.execute(f"INSERT INTO {self.tabla} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.connection.commit()
        if self.cursor.rowcount > 0: return tarea
        return None

    def update_tarea(self, tarea: Tarea):
        data = (tarea.email, tarea.title, tarea.text, tarea.fCreated, tarea.fUpdated, tarea.checked, tarea.important, tarea.priority,tarea.id)
        self.cursor.execute(f"UPDATE {self.tabla} SET EMAIL = ?, TITLE = ?, TEXT = ?, FCREATED = ?, FUPDATED = ?, CHECKED = ?, IMPORTANT = ?, PRIORITY = ? WHERE ID = ?", data)
        self.connection.commit()
        if self.cursor.rowcount > 0: return tarea
        return None

    def delete_tarea(self, email: str, id_tarea: uuid) -> bool:
        self.connection.execute(f"DELETE FROM {self.tabla} WHERE EMAIL = '{email}' AND ID = '{id_tarea}'")
        self.connection.commit()
        result = self.get_tarea_by_id(email, id_tarea)
        if result is None: return True
        return False
    
    def delete_all_tareas(self, email: str) -> bool:
        self.connection.execute(f"DELETE FROM {self.tabla} WHERE EMAIL = '{email}'")
        self.connection.commit()
        result = self.get_tareas(email)
        if result == []: return True
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