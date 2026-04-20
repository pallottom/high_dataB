import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import engine, Base, SessionLocal
from models import *
from CRUD import *

"""
def init_db():
    Base.metadata.create_all(bind=engine)

def main():
    init_db()
    db = SessionLocal()
    # do stuff...
    db.close()

if __name__ == "__main__":
    main()

    """

import toml
from pprint import pprint


_config_path = os.path.join(os.path.dirname(__file__), "..", "config.toml")
with open(_config_path, "r") as file:
    config: dict = toml.load(file)


pprint(config)