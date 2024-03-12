from src.models.usuario import Usuario

class UsuarioRepoMaria():

    def __init__(self, connection, tabla: str):
        self.tabla = tabla
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {tabla} (
                            EMAIL VARCHAR(100) PRIMARY KEY,
                            PASSWORD VARCHAR(100),
                            NAME VARCHAR(100),
                            VERIFIED BOOLEAN,
                            VERIFICATIONCODE VARCHAR(36)
        )""")
        self.connection.commit()
        print("Tabla usuarios creada")

    def get_usuario(self, email: str, password: str) -> Usuario:
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}' AND PASSWORD = '{password}'")
        usuario = self.cursor.fetchone()
        if usuario is None: return None
        return Usuario(email = usuario[0],
                       password = usuario[1],
                       name = usuario[2],
                       isVerified = usuario[3],
                       verificationCode = usuario[4])
        
    def save_usuario(self, usuario: Usuario, oldPassword: str) -> Usuario:
        result = self.get_usuario(usuario.email, oldPassword)
        if result is None: return self.new_usuario(usuario)
        return self.update_usuario(usuario)

    def new_usuario(self, usuario: Usuario):
        data = (usuario.email, usuario.password, usuario.name, usuario.isVerified, usuario.verificationCode)
        self.cursor.execute(f"INSERT INTO {self.tabla} VALUES(?, ?, ?, ?, ?)", data)
        self.connection.commit()
        if self.cursor.rowcount > 0: return usuario
        return None

    def update_usuario(self, usuario: Usuario):
        data = (usuario.email, usuario.password, usuario.name, usuario.isVerified, usuario.verificationCode, usuario.email)
        self.cursor.execute(f"UPDATE {self.tabla} SET EMAIL = ?, PASSWORD = ?, NAME = ?, VERIFIED = ?, VERIFICATIONCODE = ? WHERE EMAIL = ?", data)
        self.connection.commit()
        if self.cursor.rowcount > 0: return usuario
        return None

    def delete_usuario(self, email: str, password: str) -> bool:
        self.cursor.execute(f"DELETE FROM {self.tabla} WHERE EMAIL = '{email}' AND PASSWORD = '{password}'")
        self.connection.commit()
        result = self.get_usuario(email, password)
        if result is None: return True
        return False

    def email_existe(self, email: str) -> bool:
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}'")
        result = self.cursor.fetchone()
        if result is not None: return True
        return False
    
    def is_verified(self, email: str) -> bool:
        self.cursor.execute(f"SELECT * FROM {self.tabla} WHERE EMAIL = '{email}'")
        usuario = self.cursor.fetchone()
        if usuario is None: return False
        return bool(usuario[3])