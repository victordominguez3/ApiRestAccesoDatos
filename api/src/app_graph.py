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
from graphene import ObjectType, String, Schema, List, Field, Mutation, Boolean, Int
from graphql_server.flask import GraphQLView

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
        if usuario_repo.email_existe(email): return Exception("Ya existe un usuario con el mismo email")
        new_usuario = Usuario(email, password, name)
        result = usuario_repo.save_usuario(new_usuario, new_usuario.password)
        if result is None: return Exception("Usuario no guardado")
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
        if new_usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")

        new_usuario.name = name if name is not None else new_usuario.name
        new_usuario.password = new_password if new_password is not None else new_usuario.password

        result = usuario_repo.save_usuario(new_usuario, old_password)
        if result is None: return Exception("Usuario no editado")
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
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")

        if not usuario_repo.delete_usuario(email, password): return Exception("No se pudo completar el borrado del usuario")
        if env["ACTUAL_DB"] == "mongo": tarea_repo.delete_all_tareas(email)
        return Exception("Usuario y tareas vinculadas eliminados con éxito")
    
class VerificarUsuario(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)
        verification_code = String(required=True)

    usuario = Field(UsuarioType)
    def mutate(self, info, email, password, verification_code):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if verification_code != usuario.verificationCode: return Exception("Código de verificación incorrecto")
        usuario.isVerified = True
        result = usuario_repo.save_usuario(usuario, password)
        if result is None: return Exception("Usuario no editado")
        return VerificarUsuario(UsuarioType(
            result.email,
            result.password,
            result.name,
            result.isVerified,
            result.verificationCode))
    
class CrearTarea(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)
        title = String(required=True)
        text = String(required=True)
        checked = Boolean(required=True)
        important = Boolean(required=True)
        priority = Int(required=True)

    tarea = Field(TareaType)
    def mutate(self, info, email, password, title, text, checked, important, priority):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): Exception("Usuario no verificado")
        new_tarea = Tarea(email, title, text, checked, important, priority)
        result = tarea_repo.save_tarea(email, new_tarea)
        if result is None: return Exception("Tarea no guardada")
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
        id = String(required=True)
        email = String(required=True)
        password = String(required=True)
        title = String()
        text = String()
        checked = Boolean()
        important = Boolean()
        priority = Int()

    tarea = Field(TareaType)
    def mutate(self, info, id, email, password, title, text, checked, important, priority):
        new_usuario = usuario_repo.get_usuario(email, password)
        if new_usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        tarea = tarea_repo.get_tarea_by_id(email, id)
        if tarea is None: return jsonify({"Mensaje": "No existe la tarea"})
        new_tarea = Tarea(
            email,
            title if title is not None else tarea.title,
            text if text is not None else tarea.text,
            checked if checked is not None else tarea.checked,
            important if important is not None else tarea.important,
            priority if priority is not None else tarea.priority,
            tarea.id,
            tarea.fCreated)
        result = tarea_repo.save_tarea(email, new_tarea)
        if result is None: return Exception("Tarea no editada")
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
        id = String(required=True)

    tarea = Field(TareaType)
    def mutate(self, info, email, password, id):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        if tarea_repo.get_tarea_by_id(email, id) is None: return Exception("No existe una tarea con el id proporcionado")
        if not tarea_repo.delete_tarea(email, id): return Exception("No se pudo completar el borrado de la tarea")
        return Exception("Tarea eliminada con éxito")
    
class EliminarTareas(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    tarea = Field(TareaType)
    def mutate(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        tareas = tarea_repo.get_tareas(email)
        if tareas == [] or tareas is None: return Exception("No hay tareas para este usuario")
        if not tarea_repo.delete_all_tareas(email): return Exception("No se pudo completar el borrado de las tareas")
        return Exception("Todas las tareas eliminadas con éxito")

class Mutation(ObjectType):
    crear_usuario = CrearUsuario.Field()
    editar_usuario = EditarUsuario.Field()
    eliminar_usuario = EliminarUsuario.Field()
    verificar_usuario = VerificarUsuario.Field()

    crear_tarea = CrearTarea.Field()
    editar_tarea = EditarTarea.Field()
    eliminar_tareas = EliminarTarea.Field()
    eliminar_todas_tareas = EliminarTareas.Field()

class Query(ObjectType):
    
    usuario = Field(UsuarioType, email=String(required=True), password=String(required=True))
    tareas = List(TareaType, email=String(required=True), password=String(required=True))
    tarea = Field(TareaType, email=String(required=True), password=String(required=True), id=String(required=True))
    tareas_filtered = List(TareaType, email=String(required=True), password=String(required=True), code=String(required=True))
    tareas_ordered = List(TareaType, email=String(required=True), password=String(required=True), code=String(required=True), reverse=Boolean(required=True))

    def resolve_usuario(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("No existe el usuario")
        return UsuarioType(
            usuario.email,
            usuario.password,
            usuario.name,
            usuario.isVerified,
            usuario.verificationCode)

    def resolve_tareas(self, info, email, password):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        tareas = tarea_repo.get_tareas(email)
        if tareas == [] or tareas is None: return Exception("No hay tareas para este usuario")
        return [TareaType(
            id = tarea.id,
            email = tarea.email,
            title = tarea.title,
            text = tarea.text,
            created_date = tarea.fCreated,
            updated_date = tarea.fUpdated,
            checked = tarea.checked,
            important = tarea.important,
            priority = tarea.priority) for tarea in tareas]

    def resolve_tarea(self, info, email, password, id):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): Exception("Usuario no verificado")
        tarea = tarea_repo.get_tarea_by_id(email, id)
        if tarea is None: return Exception("No existe tarea con el id proporcionado")
        return TareaType(
            id = tarea.id,
            email = tarea.email,
            title = tarea.title,
            text = tarea.text,
            created_date = tarea.fCreated,
            updated_date = tarea.fUpdated,
            checked = tarea.checked,
            important = tarea.important,
            priority = tarea.priority)
    
    def resolve_tareas_filtered(self, info, email, password, code):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        if code not in ["important", "checked", "notimportant", "notchecked"]: return Exception("Filtro incorrecto. Filtros: checked, important, notchecked, notimportant")
        tareas = tarea_repo.filter(tarea_repo.get_tareas(email), code)
        if tareas == []: return Exception("No hay tareas con este filtro")
        return [TareaType(
            id = tarea.id,
            email = tarea.email,
            title = tarea.title,
            text = tarea.text,
            created_date = tarea.fCreated,
            updated_date = tarea.fUpdated,
            checked = tarea.checked,
            important = tarea.important,
            priority = tarea.priority) for tarea in tareas]
    
    def resolve_tareas_ordered(Self, info, email, password, code, reverse):
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return Exception("Usuario no autentificado")
        if not usuario_repo.is_verified(email): return Exception("Usuario no verificado")
        if code not in ["title", "priority", "updated_date", "created_date"]: return Exception("Filtro incorrecto. Filtros: title, priority, updated_date, created_date")
        if reverse not in ["true", "false"]: return Exception("Reverse incorrecto (true o false)")
        tareas = tarea_repo.order(tarea_repo.get_tareas(email), code, True if reverse == "true" else False)
        if tareas == []: return Exception("No hay tareas para este usuario")
        return [TareaType(
            id = tarea.id,
            email = tarea.email,
            title = tarea.title,
            text = tarea.text,
            created_date = tarea.fCreated,
            updated_date = tarea.fUpdated,
            checked = tarea.checked,
            important = tarea.important,
            priority = tarea.priority) for tarea in tareas]

schema = Schema(query=Query, mutation=Mutation)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True)