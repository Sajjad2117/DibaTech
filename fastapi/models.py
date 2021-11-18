from mongoengine import Document, StringField, IntField


class Product(Document):
    name = StringField(max_length=100)
    description = StringField(max_length=200)
    number = IntField()


class User(Document):
    username = StringField(max_length=32)
    password = StringField()

