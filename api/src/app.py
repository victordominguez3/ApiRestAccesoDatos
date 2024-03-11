from flask import Flask, jsonify, request, abort
from dotenv import dotenv_values
from src.repositories.usuario_repo_mongo import UsuarioRepoMongo
from src.models.usuario import Usuario
from src.repositories.tarea_repo_mongo import TareaRepoMongo
from src.repositories.tarea_repo_maria import TareaRepoMaria
from src.models.tarea import Tarea
from pymongo.errors import PyMongoError
from datetime import datetime

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

env = dotenv_values()

if env["ACTUAL_DB"] == "maria":
    tarea_repo = TareaRepoMaria("tareas", env["DB_USER"], env["DB_PASSWORD"])
if env["ACTUAL_DB"] == "mongo":
    tarea_repo = TareaRepoMongo("tareas", env["DB_USER"], env["DB_PASSWORD"])

usuario_repo = UsuarioRepoMongo("usuarios", env["DB_USER"], env["DB_PASSWORD"])

# @app.route('/ping', methods=['GET'])
# def index():
#     response = {'pong': 'pong'}
#     return jsonify(response)

@app.route('/usuario/<email>', methods = ["GET"])
def get_usuario(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is not None: return jsonify(usuario.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el get del usuario"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})
    
@app.route('/usuario', methods = ["POST"])
def post_usuario():
    try:
        body = request.get_json()
        if not all(key in body for key in ["email", "password", "name"]): return jsonify({"Mensaje": "Faltan campos"})
        if usuario_repo.email_existe(body["email"]): return jsonify({"Mensaje": "Ya existe un usuario con el mismo email"})
        usuario = Usuario(body["email"], body["password"], body["name"])
        result = usuario_repo.save_usuario(usuario, usuario.password)
        if result is not None: return jsonify(result.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el post del usuario"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})
    
@app.route('/usuario/<email>', methods = ["PUT"])
def put_usuario(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        body = request.get_json()
        if "email" in body and usuario_repo.email_existe(body["email"]): return jsonify({"Mensaje: Ya existe un usuario con el mismo email"})
        newUsuario = Usuario(
            body["email"] if "email" in body else usuario.email,
            body["password"] if "password" in body else usuario.password,
            body["name"] if "name" in body else usuario.name,
            usuario.isVerified,
            usuario.verificationCode)
        result = usuario_repo.save_usuario(newUsuario, password)
        if result is not None: return jsonify(result.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el put del usuario"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/usuario/<email>', methods = ["DELETE"])
def delete_usuario(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.email_existe(email): return jsonify({"Mensaje": "No existe un usuario con el email proporcionado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        usuario_repo.delete_usuario(email, password)
        return jsonify({"Mensaje": "Usuario eliminado con éxito"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})
    
@app.route('/usuario/verify/<email>/<vc>', methods = ["PUT"])
def verify_user(email, vc):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if vc != usuario.verificationCode: return jsonify({"Mensaje": "Código de verificación incorrecto"})
        newUsuario = Usuario(
            usuario.email,
            usuario.password,
            usuario.name,
            True,
            usuario.verificationCode)
        result = usuario_repo.save_usuario(newUsuario, password)
        if result is not None: return jsonify(result.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el put del usuario"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/<email>', methods = ["GET"])
def get_tareas(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tareas = tarea_repo.get_tareas(email)
        if tareas == []: return jsonify({"Mensaje": "No hay tareas para este usuario"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)
        return jsonify({"Mensaje": "No pudo completarse el get de las tareas"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})
    
@app.route('/tarea/<email>/<id>', methods = ["GET"])
def get_tarea_by_id(email, id):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tarea = tarea_repo.get_tarea_by_id(email, id)
        if tarea is None: return jsonify({"Mensaje": "No existe tarea con el id proporcionado"})
        return jsonify(tarea.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el get de la tarea"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/<email>', methods = ["POST"])
def post_tarea(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        body = request.get_json()
        if not all(key in body for key in ["title", "text", "checked", "important", "priority"]): return jsonify({"Mensaje": "Faltan campos"})
        tarea = Tarea(
            email,
            body["title"],
            body["text"],
            body["checked"],
            body["important"],
            body["priority"])
        result = tarea_repo.save_tarea(email, tarea)
        if result is not None: return jsonify(result.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el post de la tarea"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/<email>/<id>', methods = ["PUT"])
def put_tarea(email, id):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tarea = tarea_repo.get_tarea_by_id(email, id)
        if tarea is None: return jsonify({"Mensaje": "No existe la tarea"})
        body = request.get_json()
        newTarea = Tarea(
            email,
            body["title"] if "title" in body else tarea.title,
            body["text"] if "text" in body else tarea.text,
            body["checked"] if "checked" in body else tarea.checked,
            body["important"] if "important" in body else tarea.important,
            body["priority"] if "priority" in body else tarea.priority,
            tarea.id,
            tarea.fCreated)
        result = tarea_repo.save_tarea(email, newTarea)
        if result is not None: return jsonify(result.__dict__)
        return jsonify({"Mensaje": "No pudo completarse el put de la tarea"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/<email>/<id>', methods = ["DELETE"])
def delete_tarea(email, id):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        if not tarea_repo.tarea_existe(email, id): return jsonify({"Mensaje": "No existe una tarea con el id proporcionado"})
        tarea_repo.delete_tarea(email, id)
        return jsonify({"Mensaje": "Tarea eliminada con éxito"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/<email>', methods = ["DELETE"])
def delete_all_tareas(email):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        tarea_repo.delete_all_tareas(email)
        return jsonify({"Mensaje": "Todas las tareas eliminadas con éxito"})
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/filter/<email>/<code>', methods = ["GET"])
def filter_tareas(email, code):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        if code not in ["important", "checked", "notimportant", "notchecked"]: return jsonify({"Mensaje": "Filtro incorrecto. Filtros: checked, important, notchecked, notimportant"})
        tareas = tarea_repo.filter(tarea_repo.get_tareas(email), code)
        if tareas == []: return jsonify({"Mensaje": "No hay tareas con este filtro"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

@app.route('/tarea/order/<email>/<code>/<reverse>', methods = ["GET"])
def order_tareas(email, code, reverse):
    try:
        password = request.args.get("password")
        usuario = usuario_repo.get_usuario(email, password)
        if usuario is None: return jsonify({"Mensaje": "Usuario no autentificado"})
        if not usuario_repo.is_verified(email): return jsonify({"Mensaje": "Usuario no verificado"})
        if code not in ["title", "priority", "updated_date", "created_date"]: return jsonify({"Mensaje": "Filtro incorrecto. Filtros: title, priority, updated_date, created_date"})
        if reverse not in ["true", "false"]: return jsonify({"Mensaje": "Reverse incorrecto (true o false)"})
        tareas = tarea_repo.order(tarea_repo.get_tareas(email), code, True if reverse == "true" else False)
        if tareas == []: return jsonify({"Mensaje": "No hay tareas para este usuario"})
        tareas_dict = [tarea.__dict__ for tarea in tareas]
        return jsonify(tareas_dict)
    except PyMongoError as e:
        return jsonify({"Error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)