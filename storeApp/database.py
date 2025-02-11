import os
from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select
load_dotenv('.env')
from models import User

DATABASE_URL = os.environ['DATABASE_URL']

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    print("Tables created")

def get_session():
    """Create database session per request, close it after returning response"""
    with Session(engine) as session:
        yield session


import logging

def find_user(name):
    with Session(engine) as session:
        statement = select(User).where(User.userName == name)
        logging.debug(f"Executing query: {statement}")
        
        user = session.exec(statement).first()
        if user:
            logging.debug(f"User found: {user.userName}")
        else:
            logging.error(f"No user found with userName: {name}")
        return user


def verify_password(login, password):
    check = False
    if login == password:
        check = True
    return check
