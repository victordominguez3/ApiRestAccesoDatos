from graphene import ObjectType, String, Boolean, UUID

class UsuarioType(ObjectType):
    email = String()
    password = String()
    name = String()
    is_verified = Boolean()
    verification_code = String()