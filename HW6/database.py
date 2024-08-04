import databases
import sqlalchemy
from fastapi import HTTPException
from typing import Type
from enum import Enum
from sqlalchemy import select

DATABASE_URL = "sqlite:///databases.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table("users", metadata,
                         sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                         sqlalchemy.Column("name", sqlalchemy.String(32)),
                         sqlalchemy.Column("surname", sqlalchemy.String(32)),
                         sqlalchemy.Column("email", sqlalchemy.String(128)),
                         sqlalchemy.Column("password", sqlalchemy.String(32)),
                         )

products = sqlalchemy.Table("products", metadata,
                            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                            sqlalchemy.Column("title", sqlalchemy.String(50)),
                            sqlalchemy.Column("description", sqlalchemy.String(300)),
                            sqlalchemy.Column("price", sqlalchemy.Integer)
                            )

orders = sqlalchemy.Table("orders", metadata,
                          sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                          sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id")),
                          sqlalchemy.Column("prod_id", sqlalchemy.ForeignKey("products.id")),
                          sqlalchemy.Column("date", sqlalchemy.String),
                          sqlalchemy.Column("status", sqlalchemy.String(20))
                          )

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

class DataType(str, Enum):
    users = "users"
    products = "products"
    orders = "orders"


async def insert_into_table(table_name_str: str, item: dict):
    values_dict = item.dict()
    table_object = metadata.tables[table_name_str]
    query = table_object.insert().values(**values_dict)
    last_record_id = await database.execute(query)
    return {**values_dict, "id": last_record_id}


async def fetch_by_id(table_name: str, id_value: int, model: Type):
    stmt = select(table_name).where(table_name.c.id == id_value)
    result = await database.fetch_one(stmt)
    if result is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} with id {id_value} not found")
    return result


async def update_and_fetch_by_id(
    table_name: str, id_value: int, new_data: dict, model: Type):
    await database.execute(table_name.update().where(table_name.c.id == id_value).values(**new_data))
    result = await database.fetch_one(table_name.select().where(table_name.c.id == id_value))
    if result is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} with id {id_value} not found")
    return {**new_data, "id": id_value}


async def delete_item(table_name: str, id_value: int, success_message: str):
    result = await database.fetch_one(table_name.select().where(table_name.c.id == id_value))
    if result is None:
        raise HTTPException(status_code=404, detail=f"{table_name} with id {id_value} not found")
    await database.execute(table_name.delete().where(table_name.c.id == id_value))
    return {"message": success_message}
