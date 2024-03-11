from mariadb import mariadb
from src.models.tarea import Tarea
import uuid

class TareaRepoMaria():



    def __init__(self, tabla: str, user: str, password: str):
        try:

            config = {
                'host': 'maria',
                'port': 3306,
                'user': user,
                'password': password,
                'database': 'mariadb'
            }

            conn = mariadb.connect(**config)
            self.cursor = conn.cursor()
            
            self.cursor.execute("SELECT 'Hello, world!'")
            result = self.cursor.fetchone()[0]
            print(result)

        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")



    # def __init__(self, tabla: str, user: str, password: str):
    #     try:
    #         self.tabla = tabla
    #         self.connection = mariadb.connect(
    #             host="maria",
    #             port=3306,
    #             password="example",
    #             database="mariadb"
    #         )
    #         self.cursor = self.connection.cursor()
    #         print("Connected to MariaDB!")
    #         self.init_db()
    #     except mariadb.Error as e: print(e)

    def init_db(self):
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {self.tabla} (
                            EMAIL VARCHAR(100),
                            ID VARCHAR(36) PRIMARY KEY,
                            TITLE VARCHAR(200),
                            TEXT VARCHAR(500),
                            FCREATED DATETIME,
                            FUPDATED DATETIME,
                            CHECKED BOOLEAN,
                            IMPORTANT BOOLEAN
        )""")
        self.connection.commit()

    def get_tareas(self, email: str):
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}'")
        return [Tarea(email = tarea[0],
                      id = tarea[1],
                      title = tarea[2],
                      text = tarea[3],
                      fCreated = tarea[4],
                      fUpdated = tarea[5],
                      checked = tarea[6],
                      important = tarea[7]) for tarea in self.cursor]
    
    def get_tarea_by_id(self, email: str, id_tarea) -> Tarea:
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}' AND ID = '{id_tarea}'")
        tarea = self.cursor.fetchone()
        if tarea is not None:
            return Tarea(email = tarea[0],
                        id = tarea[1],
                        title = tarea[2],
                        text = tarea[3],
                        fCreated = tarea[4],
                        fUpdated = tarea[5],
                        checked = tarea[6],
                        important = tarea[7])
        return None

    def save_tarea(self, email: str, tarea: Tarea):
        result = self.get_tarea_by_id(email, tarea.id)
        if result is not None:
            tarea = self.update_tarea(tarea)
        else: tarea = self.new_tarea(tarea)
        return tarea
    
    def new_tarea(self, tarea: Tarea):
        data = (tarea.email, tarea.id, tarea.title, tarea.text, tarea.fCreated, tarea.fUpdated, tarea.checked, tarea.important)
        self.cursor.execute(f"INSERT INTO {self.tabla} VALUES(?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.connection.commit()
        if self.cursor.rowcount > 0:
            return tarea
        return None

    def update_tarea(self, tarea: Tarea):
        data = (tarea.email, tarea.title, tarea.text, tarea.fCreated, tarea.fUpdated, tarea.checked, tarea.important, tarea.id)
        self.cursor.execute(f"UPDATE {self.tabla} SET EMAIL = ?, TITLE = ?, TEXT = ?, FCREATED = ?, FUPDATED = ?, CHECKED = ?, IMPORTANT = ? WHERE ID = ?", data)
        self.connection.commit()
        if self.cursor.rowcount > 0:
            return tarea
        return None

    def delete_tarea(self, email: str, id_tarea: uuid) -> bool:
        self.connection.execute(f"DELETE FROM {self.tabla} WHERE EMAIL = '{email}' AND ID = '{id_tarea}'")
        self.connection.commit()
        result = self.get_tarea_by_id(email, id_tarea)
        if result is None:
            return True
        return False