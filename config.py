import os

# Find the exact path of your project folder dynamically
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define where the SQLite database file will be saved
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

# A secret key is required by Flask for secure sessions (like logging in)
SECRET_KEY = 'super_secret_thesis_key'