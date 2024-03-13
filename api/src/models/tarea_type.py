from graphene import ObjectType, String, Boolean, UUID, DateTime, Int

class TareaType(ObjectType):
    id = String()
    email = String()
    title = String()
    text = String()
    created_date = DateTime()
    updated_date = DateTime()
    checked = Boolean()
    important = Boolean()
    priority = Int()