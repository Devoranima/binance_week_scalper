from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from updater.db.models import Base
import os

from dotenv import load_dotenv
load_dotenv() 

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DATABASE_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE_NAME}")
if not database_exists(engine.url):
  create_database(engine.url)
  
if __name__ == "__main__":
  Base.metadata.create_all(engine)