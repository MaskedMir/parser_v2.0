from dotenv import load_dotenv
import os

load_dotenv()

DB_SECRET = os.getenv('DB_SECRET')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
