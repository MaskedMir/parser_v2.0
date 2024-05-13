import asyncio
import json
import random
import re
import threading
import time
from datetime import datetime

import uvicorn
from fastapi import FastAPI, APIRouter, Request, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from playwright.async_api import async_playwright
from starlette.responses import RedirectResponse

app = FastAPI()
router = APIRouter(prefix="/digsearch")
templates = Jinja2Templates(directory="templates")


import MySQLdb

conn = MySQLdb.connect(
      host="rc1a-3r7wr8qzh4gvbrk9.mdb.yandexcloud.net",
      port=3306,
      db="db_digsearch",
      user="user1",
      passwd="testpass",
      ssl={'ca': r'C:\Users\Masked\PycharmProjects\dig-search-develop_2\database\MySQL.pem'}
      # ssl={'ca': r'C:\Users\max16\PycharmProjects\dig-search-develop_2\database\MySQL.pem'}
    )

cur = conn.cursor()



# Get all employees
@router.get("/employees")
def get_employees():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hhcomplist")
    result = cursor.fetchall()
    return {"employees": result}

# Get an employee by ID
@router.get("/employees/{id}")
def get_employee(name: str):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM hhcomplist WHERE name = {name}")
    result = cursor.fetchone()
    return {"employee": result}

# Add a new employee
@router.post("/employees")
def add_employee(name: str, id: int):
    cursor = conn.cursor()
    sql = "INSERT INTO hhcomplist (name, id) VALUES (%s, %s)"
    val = (name, id)
    cursor.execute(sql, val)
    conn.commit()
    return {"message": "Employee added successfully"}

# Delete an employee by ID
@router.delete("/employees/{id}")
def delete_employee(id: int):
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM hhcomplist WHERE id = {id}")
    conn.commit()
    return {"message": "Employee deleted successfully"}


from typing import List

@router.get("/autocomplete")
async def autocomplete(query: str):
    cursor = conn.cursor()
    query = f"%{query}%"  # Prepare the query string for a partial match
    cursor.execute("SELECT name FROM hhcomplist WHERE name LIKE %s", (query,))
    names = cursor.fetchall()
    return {"matches": [name[0] for name in names]}
