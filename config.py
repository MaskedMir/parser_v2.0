from dotenv import load_dotenv
import os

load_dotenv()

DB_SECRET = os.getenv('testpass')
DB_USER = os.getenv('user1')
DB_NAME = os.getenv('db_digsearch')
DB_HOST = os.getenv('rc1a-3r7wr8qzh4gvbrk9.mdb.yandexcloud.net')
