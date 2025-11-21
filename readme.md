# LAT Database – Creation & Testing Repository

This repository contains all scripts and modules required to create, populate, test, and remove the database used by the LAT project. It also includes tools to manage the database schema and data import workflows.

📁 Repository Structure
.
├── CRUD/
│   ├── createDB.py        # Creates the database schema
│   ├── run_imports.py     # Loads data into the database
│   ├── deleteDB.py        # Deletes the entire database
│
├── models/                # Database schema definitions (used by createDB.py)
│   └── ...
│
├── importers/             # Data import logic
│   └── ...
|
├── requirements.txt       # Python dependencies
└── README.md

## 🛠️ Environment Setup

This project uses Python 3.11.3 and a virtual environment.
Make sure you have pyenv installed before proceeding.

### macOS Setup

```pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 
```


### Windows Setup


**PowerShell**
```pyenv local 3.11.3
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Git Bash**
```pyenv local 3.11.3
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Note:
If `pip install --upgrade pip` fails, try:

```python.exe -m pip install --upgrade pip```


### 🚀 Usage
1. Create the Database Schema


```python CRUD/createDB.py```

This uses the schema definitions located in /models.

2. Import Data


```python CRUD/run_imports.py```


This script uses importer modules from the /importers folder.

3. Delete the Database

```python CRUD/deleteDB.py```


### 🗄️ Database Connection

Database connection details and helper functions are located in:

home/database.py


You can reference this module when writing scripts that interact with the database.

📦 Dependencies

All required librarie are listed in:

`requirements.txt`