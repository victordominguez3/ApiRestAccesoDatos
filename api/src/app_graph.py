from flask import Flask, jsonify, request, abort
from dotenv import dotenv_values
from src.repositories.usuario_repo_mongo import UsuarioRepoMongo
from src.repositories.usuario_repo_maria import UsuarioRepoMaria
from src.models.usuario import Usuario
from src.models.usuario_type import UsuarioType
from src.repositories.tarea_repo_mongo import TareaRepoMongo
from src.repositories.tarea_repo_maria import TareaRepoMaria
from src.models.tarea import Tarea
from src.models.tarea_type import TareaType
from mariadb import mariadb
from graphene import ObjectType, String, Schema, ID, List, Field, Mutation ,InputObjectType, Boolean, Int, UUID

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

env = dotenv_values()

if env["ACTUAL_DB"] == "maria":

    try:
        connection = mariadb.connect(
            host="maria",
            port=3306,
            password=env["DB_PASSWORD"],
            database="mariadb"
        )
        print("Connected to MariaDB!")
    except mariadb.Error as e: print(e)

    usuario_repo = UsuarioRepoMaria(connection, "usuarios")
    tarea_repo = TareaRepoMaria(connection, "tareas")

if env["ACTUAL_DB"] == "mongo":
    tarea_repo = TareaRepoMongo("tareas", env["DB_USER"], env["DB_PASSWORD"])
    usuario_repo = UsuarioRepoMongo("usuarios", env["DB_USER"], env["DB_PASSWORD"])

class CrearUsuario(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)
        name = String(required=True)

    usuario = Field(UsuarioType)
    def mutate(self, info, email, password, name):
        if usuario_repo.email_existe(email): return Exception('Ya existe un usuario con el mismo email')
        new_usuario = Usuario(email, password, name)
        result = usuario_repo.save_usuario(new_usuario, new_usuario.password)
        if result is None: return Exception('Usuario no guardado')
        return CrearUsuario(UsuarioType(
            result.email,
            result.password,
            result.name,
            result.isVerified,
            result.verificationCode))
    
class EditarUsuario(Mutation):
    class Arguments:
        email = String(required=True)
        old_password = String(required=True)
        new_password = String()
        name = String()

    usuario = Field(UsuarioType)
    def mutate(self, info, email, old_password, new_password, name):
        new_usuario = usuario_repo.get_usuario(email, old_password)
        if new_usuario is None: return Exception('Usuario no autentificado')
        if not usuario_repo.is_verified(email): return Exception('Usuario no verificado')

        new_usuario.name = name if name is not None else new_usuario.name
        new_usuario.password = new_password if new_password is not None else new_usuario.password

        result = usuario_repo.save_usuario(new_usuario, old_password)
        if result is None: return Exception('Usuario no editado')
        return EditarUsuario(UsuarioType(
            result.email,
            result.password,
            result.name,
            result.isVerified,
            result.verificationCode))
    
class EliminarUsuario(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    usuario = Field(UsuarioType)
    def mutate(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception('Usuario no autentificado')
        if not usuario_repo.is_verified(email): return Exception('Usuario no verificado')

        if not usuario_repo.delete_usuario(email, password): return Exception('No se pudo completar el borrado del usuario')
        if env["ACTUAL_DB"] == "mongo": tarea_repo.delete_all_tareas(email)
        return jsonify({"Mensaje": "Usuario y tareas vinculadas eliminados con éxito"})
    
class CrearTarea(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)
        title = String(required=True)
        text = String()
        checked = Boolean()
        important = Boolean()
        priority = Int()

    tarea = Field(TareaType)
    def mutate(self, info, email, password, title, text, checked, important, priority):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        new_tarea = Tarea(email, title, text, checked, important, priority)
        result = tarea_repo.save_tarea(email, new_tarea)
        if result is None: return Exception('Tarea no guardada')
        return CrearTarea(TareaType(
            result.id,
            result.email,
            result.title,
            result.text,
            result.fCreated,
            result.fUpdated,
            result.checked,
            result.important,
            result.priority))
    
class EditarTarea(Mutation):
    class Arguments:
        id = UUID(required=True)
        email = String(required=True)
        password = String(required=True)
        title = String(required=True)
        text = String()
        checked = Boolean()
        important = Boolean()
        priority = Int()

    tarea = Field(TareaType)
    def mutate(self, info, id, email, password, title, text, checked, important, priority):
        new_usuario = usuario_repo.get_usuario(email, password)
        if new_usuario is None: return Exception('Usuario no autentificado')
        if not usuario_repo.is_verified(email): return Exception('Usuario no verificado')
        
        new_tarea = tarea_repo.get_tarea_by_id(email, id)
        new_tarea.title = title if title is not None else new_tarea.title
        new_tarea.text = text if text is not None else new_tarea.text
        new_tarea.checked = checked if checked is not None else new_tarea.checked
        new_tarea.important = important if important is not None else new_tarea.important
        new_tarea.priority = priority if priority is not None else new_tarea.priority

        result = tarea_repo.save_tarea(email, new_tarea)
        if result is None: return Exception('Tarea no editada')
        return EditarTarea(TareaType(
            result.id,
            result.email,
            result.title,
            result.text,
            result.fCreated,
            result.fUpdated,
            result.checked,
            result.important,
            result.priority))
    
class EliminarTarea(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)
        id = UUID(required=True)

    tarea = Field(TareaType)
    def mutate(self, info, email, password, id):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception('Usuario no autentificado')
        if not usuario_repo.is_verified(email): return Exception('Usuario no verificado')
        if tarea_repo.get_tarea_by_id(email, id) is None: return jsonify({"Mensaje": "No existe una tarea con el id proporcionado"})
        if not tarea_repo.delete_tarea(email, id): return jsonify({"Mensaje": "No se pudo completar el borrado de la tarea"})
        return jsonify({"Mensaje": "Tarea eliminada con éxito"})
    
class EliminarTareas(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    tarea = Field(TareaType)
    def mutate(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tareas = tarea_repo.get_tareas(email)
        if tareas == [] or tareas is None: return jsonify({"Mensaje": "No hay tareas para este usuario"})
        if not tarea_repo.delete_all_tareas(email): return jsonify({"Mensaje": "No se pudo completar el borrado de las tareas"})
        return jsonify({"Mensaje": "Todas las tareas eliminadas con éxito"})

class Mutation(ObjectType):
    crear_usuario = CrearUsuario.Field()
    editar_usuario = EditarUsuario.Field()
    eliminar_usuario = EliminarUsuario.Field()

    crear_tarea = CrearTarea.Field()
    editar_tarea = EditarTarea.Field()
    eliminar_tareas = EliminarTarea.Field()
    eliminar_todas_tareas = EliminarTareas.Field()

class Query(ObjectType):
    
    usuario = Field(UsuarioType, email=String(required=True), password=String(required=True))
    tareas = List(TareaType, email=String(required=True), password=String(required=True))
    tarea = Field(TareaType, email=String(required=True), password=String(required=True), id=UUID(required=True))
    tareas_filtered = List(TareaType, email=String(required=True), password=String(required=True), code=String(required=True))
    tareas_ordered = List(TareaType, email=String(required=True), password=String(required=True), code=String(required=True), reverse=Boolean(required=True))

    def resolve_usuario(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is not None: return jsonify(usuario.__dict__)
        return jsonify({"Mensaje": "No existe el usuario"})

    def resolve_tareas(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tareas = tarea_repo.get_tareas(email)
        if tareas == [] or tareas is None: return jsonify({"Mensaje": "No hay tareas para este usuario"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)

    def resolve_tarea(self, info, email, password, id):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tarea = tarea_repo.get_tarea_by_id(email, id)
        if tarea is None: return jsonify({"Mensaje": "No existe tarea con el id proporcionado"})
        return jsonify(tarea.__dict__)
    
    def resolve_tareas_filtered(self, info, email, password, code):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        if code not in ["important", "checked", "notimportant", "notchecked"]: return jsonify({"Mensaje": "Filtro incorrecto. Filtros: checked, important, notchecked, notimportant"})
        tareas = tarea_repo.filter(tarea_repo.get_tareas(email), code)
        if tareas == []: return jsonify({"Mensaje": "No hay tareas con este filtro"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)
    
    def resolve_tareas_ordered(Self, info, email, password, code, reverse):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        if code not in ["title", "priority", "updated_date", "created_date"]: return jsonify({"Mensaje": "Filtro incorrecto. Filtros: title, priority, updated_date, created_date"})
        if reverse not in ["true", "false"]: return jsonify({"Mensaje": "Reverse incorrecto (true o false)"})
        tareas = tarea_repo.order(tarea_repo.get_tareas(email), code, True if reverse == "true" else False)
        if tareas == []: return jsonify({"Mensaje": "No hay tareas para este usuario"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)

schema = Schema(query=Query, mutation=Mutation)

if __name__ == '__main__':
    app.run(debug=True)