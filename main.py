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

import yaml
from pprint import pprint


with open("config.toml", "r") as file:
    config: dict = yaml.safe_load(file)


pprint(config)