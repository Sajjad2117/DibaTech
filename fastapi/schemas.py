from pydantic import BaseModel


class Product(BaseModel):
    name: str
    description: str
    number: int

    class Config:
        orm_mode = True
