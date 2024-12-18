from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from .models import Base
import os

base_path = os.path.dirname(os.path.abspath(__file__))

sqlite_filepath = os.path.join(base_path, "klines.db")

engine = create_engine(f"sqlite:///{sqlite_filepath}")
if not database_exists(engine.url):
  create_database(engine.url)
  
if __name__ == "__main__":
  Base.metadata.create_all(engine)

