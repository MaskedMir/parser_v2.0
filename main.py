import asyncio
import json
import logging
import random
import re
import threading
import time
from datetime import datetime

import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, APIRouter, Request, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from playwright.async_api import async_playwright
from starlette.responses import RedirectResponse

from database import SearchCompany, Company, IntegrityError, SearchTechnology, Project, Passport, Vacancy, Resume, \
    Industry, Product, db, technology, hhindustry
from hh_parser import HeadHunterParser, main_parser_hh_comp
from shared import should_stop
from tadv_parser import TadViserParser, main_parser_tv_comp

app = FastAPI()
router = APIRouter(prefix="/digsearch")
templates = Jinja2Templates(directory="templates")
parser_running = False
should_restart = False


def fromjson(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}

# Монтируем каталог статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

@router.get('/')
def index(request: Request):
    search_list = SearchCompany.select()
    companies = Company.select()
    technologies = SearchTechnology.select()
    industries = Industry.select()

    return templates.TemplateResponse('index.html', {"request": request, "search_list": search_list,
                                                     "companies": companies, "technologies": technologies,
                                                     "industry_list": industries})


@router.get("/sse")
async def get_notifications():
    async def event_stream():
        pass
        global parser_running
        while True:
            companies = SearchCompany.select()
            data = {}
            data["company"] = [{
                "company_name": c.company_name,
                "active_parsers_count": c.active_parsers_count,
                "id": c.id,
                "parser_statuses": c.parser_statuses
            } for c in companies]
            data["parser_running"] = parser_running
            data["should_stop"] = should_stop.is_set()

            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post('/add_company')
async def add_company(company_name: str = Form(...)):
    if company_name:
        company_names = [name.strip() for name in company_name.split(';')]
        for name in company_names:
            if name:
                try:
                    SearchCompany.create(company_name=name)
                except IntegrityError:
                    continue
    return RedirectResponse(url="/digsearch/", status_code=303)


@router.get('/delete_company/{company_id}')
async def delete_company(company_id: int):
    company = SearchCompany.get(SearchCompany.id == company_id)
    if company:
        company.delete_instance()
    return RedirectResponse(url="/digsearch/", status_code=303)


@router.post('/add_industry')
async def add_industry(industry_name: str = Form(...)):
    if industry_name:
        industry_names = [name.strip() for name in industry_name.split(';')]
        for name in industry_names:
            if name:
                try:
                    Industry.create(name=name)
                except IntegrityError:
                    continue
    return RedirectResponse(url="/digsearch/", status_code=303)


@router.get('/delete_industry/{industry_id}')
async def delete_industry(industry_id: int):
    industry = Industry.get(Industry.id == industry_id)
    if industry:
        industry.delete_instance()

    return RedirectResponse(url="/digsearch/", status_code=303)


@router.post('/add_technology')
async def add_technology(technology_name: str = Form(...)):
    if technology_name:
        technology_names = [name.strip() for name in technology_name.split(';')]
        for name in technology_names:
            if name:
                try:
                    SearchTechnology.create(name=name)
                    technology.create(technology=name)
                except IntegrityError:
                    continue
    return RedirectResponse(url="/digsearch/", status_code=303)


@router.get('/delete_technology/{tech_id}')
async def delete_technology(tech_id: int):
    tech = SearchTechnology.get(SearchTechnology.id == tech_id)
    if tech:
        tech.delete_instance()

    return RedirectResponse(url="/digsearch/", status_code=303)


@router.post('/show_technologies')
def show_technologies(request: Request, selected_company: str = Form(...)):
    print(selected_company)
    try:
        company = Company.get(Company.name == selected_company)
    except Company.DoesNotExist:
        return RedirectResponse(url="/digsearch/", status_code=303)

    if company:
        technologies_data = show_technologies_all_fields(company.id)
        search_list = SearchCompany.select()
        companies = Company.select()
        technologies = SearchTechnology.select()
        industries = Industry.select()

        return templates.TemplateResponse('index.html', {"request": request, "search_list": search_list,
                                                         "companies": companies, "technologies": technologies,
                                                         "industry_list": industries,
                                                         "company_technologies": technologies_data,
                                                         "selected_company": selected_company})
    else:
        raise HTTPException(status_code=400, detail="Company not found!")


@router.post("/toggle_parser")
async def toggle_parser():
    global parser_running
    if parser_running:
        should_stop.set()
    else:
        global should_restart
        should_restart = True

    return RedirectResponse(url="/digsearch/", status_code=303)


@router.get("/autocomplete")
async def autocomplete(query: str):
    try:
        conn = db
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute("SELECT name FROM hhcomplist WHERE name LIKE %s", (query,))
        names = cursor.fetchall()
        conn.close()
        return {"matches": [names[name][0] for name in range(5)]}
    except Exception as e:
        logging.info(e)


@router.get("/autocomplete2")
async def autocomplete2(query: str):
    try:
        conn = db
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute("SELECT technology FROM technology WHERE technology LIKE %s", (query,))
        names = cursor.fetchall()
        conn.close()
        return {"matches": [names[name][0] for name in range(5)]}
    except Exception as e:
        logging.info(e)

@router.get("/autocomplete3")
async def autocomplete2(query: str):
    try:
        conn = db
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute("SELECT name_industry FROM hhindustry WHERE name_industry LIKE %s", (query,))
        names = cursor.fetchall()
        conn.close()
        return {"matches": [names[name][0] for name in range(5)]}
    except Exception as e:
        logging.info(e)

@router.get("/start-parsing-company-hh")
def start_():
    main_parser_hh_comp()
@router.get("/start-parsing-company-tv")
def start_():
    main_parser_tv_comp()


def search_for_technologies(text, technologies):
    """Search for technologies in the given text and return a list of found technologies."""
    found_technologies = []
    for tech in technologies:
        # Создаем шаблон для поиска с использованием границ слова \b
        pattern = r'\b' + re.escape(tech.name) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            found_technologies.append(tech.name)
    return found_technologies


def search_technologies_in_record(record, search_technologies):
    """Search for technologies in all fields of a given record."""
    found_techs = set()

    # Retrieve all attributes (fields and methods) of the record
    attributes = dir(record)

    for attribute in attributes:
        if not attribute.startswith('_') and not callable(getattr(record, attribute)):
            value = getattr(record, attribute)
            if value and isinstance(value, str):  # We're only interested in string fields
                found_techs.update(search_for_technologies(value, search_technologies))

    return list(found_techs)


def show_technologies_all_fields(company_id):
    # Get the list of searched technologies
    search_technologies = list(SearchTechnology.select())

    company = Company.get(Company.id == company_id)

    # Initialize the results list
    results = []

    # Check each table
    for project in Project.select().where(Project.company == company):
        found_techs = search_technologies_in_record(project, search_technologies)
        for tech in found_techs:
            results.append({"technology": tech, "date": project.updated_date, "url": project.project_description})

    for passport in Passport.select().where(Passport.company == company):
        found_techs = search_technologies_in_record(passport, search_technologies)
        for tech in found_techs:
            results.append({"technology": tech, "date": passport.updated_date, "url": passport.project_name})

    for product in Product.select().where(Product.company == company):
        found_techs = search_technologies_in_record(product, search_technologies)
        for tech in found_techs:
            results.append({"technology": tech, "date": None, "url": product.href})

    for resume in Resume.select().where(Resume.company == company):
        found_techs = search_technologies_in_record(resume, search_technologies)
        for tech in found_techs:
            results.append({"technology": tech, "date": resume.publication_date, "url": resume.url})

    for vacancy in Vacancy.select().where(Vacancy.company == company):
        found_techs = search_technologies_in_record(vacancy, search_technologies)
        for tech in found_techs:
            results.append({"technology": tech, "date": vacancy.publication_date, "url": vacancy.url})

    # Sort the results by date
    sorted_data = sorted(results, key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)

    return sorted_data


async def start_hh_parsing(browser):
    print("start_hh_parsing")
    hh_parser = HeadHunterParser(browser)

    page = await hh_parser.get_new_page()

    all_companies_from_industries = []
    for industry in Industry.select():
        if should_stop.is_set():
            all_companies_from_industries = []
            break

        companies_for_industry = await hh_parser.find_all_companies(page, industry.name)
        all_companies_from_industries.extend(companies_for_industry)

    companies_from_search = []
    for search_item in SearchCompany.select():
        if should_stop.is_set():
            companies_from_search = []
            break

        company_url = await hh_parser.find_company_url(page, search_item.company_name)
        if company_url:
            companies_from_search.append({"url": company_url, "name": search_item.company_name})

    await page.close()

    combined_list = all_companies_from_industries + companies_from_search

    # Убираем дубликаты на основе URL
    seen = set()
    all_unique_companies = []
    for company in combined_list:
        if should_stop.is_set():
            all_unique_companies = []
            break

        if isinstance(company, dict):  # Если это словарь, берем URL
            url = company["url"]
        else:  # Если это строка, просто используем ее
            url = company

        if url not in seen:
            seen.add(url)
            all_unique_companies.append(company)

    for company_url in all_unique_companies:
        print(company_url)
        if should_stop.is_set():
            break

        # Находим компанию в базе данных и увеличиваем счетчик
        company = None
        try:
            company = SearchCompany.get(SearchCompany.company_name == company_url["name"])
        except SearchCompany.DoesNotExist:
            pass

        if company:
            company.active_parsers_count += 1
            company.save()

        await hh_parser.parse(company_url["name"], company_url["url"])

        try:
            company = SearchCompany.get(SearchCompany.company_name == company_url["name"])
        except SearchCompany.DoesNotExist:
            pass

        if company:
            # После парсинга уменьшаем счетчик
            company.active_parsers_count -= 1
            statuses = json.loads(company.parser_statuses)
            statuses["hh"] = True
            company.parser_statuses = json.dumps(statuses)
            company.save()

        time.sleep(30 + random.uniform(3, 7))


async def start_tv_parsing(browser):
    print("start_tv_parsing")
    tadv_parser = TadViserParser(browser)

    page = await tadv_parser.get_new_page()

    all_companies_from_industries = []
    for industry in Industry.select():
        if should_stop.is_set():
            all_companies_from_industries = []
            break
        print(industry.name)
        companies_for_industry = await tadv_parser.find_all_companies(page, industry.name)  #
        all_companies_from_industries.extend(companies_for_industry)

    companies_from_search = []
    for search_item in SearchCompany.select():
        if should_stop.is_set():
            companies_from_search = []
            break

        companies_from_search.append({"url": None, "name": search_item.company_name})

    await page.close()

    combined_list = all_companies_from_industries + companies_from_search

    # Убираем дубликаты на основе URL
    seen = set()
    all_unique_companies = []
    for company in combined_list:
        if should_stop.is_set():
            all_unique_companies = []
            break

        if isinstance(company, dict):  # Если это словарь, берем URL
            name = company["name"]
        else:  # Если это строка, просто используем ее
            name = company

        if name not in seen:
            seen.add(name)
            all_unique_companies.append(company)

    for company_url in all_unique_companies:
        if should_stop.is_set():
            break

        # Находим компанию в базе данных и увеличиваем счетчик
        company = None
        try:
            company = SearchCompany.get(SearchCompany.company_name == company_url["name"])
        except SearchCompany.DoesNotExist:
            pass

        if company:
            company.active_parsers_count += 1
            company.save()

        await tadv_parser.parse(company_url["name"], company_url["url"])

        try:
            company = SearchCompany.get(SearchCompany.company_name == company_url["name"])
        except SearchCompany.DoesNotExist:
            pass

        if company:
            # После парсинга уменьшаем счетчик
            company.active_parsers_count -= 1
            statuses = json.loads(company.parser_statuses)
            statuses["tv"] = True
            company.parser_statuses = json.dumps(statuses)
            company.save()

        time.sleep(30 + random.uniform(3, 7))


async def run_parsers():
    print("RUN PARSER")
    async with async_playwright() as p:
        global parser_running
        parser_running = True

        browser = await p.chromium.launch()

        for company in SearchCompany.select():
            company.active_parsers_count = 0
            company.parser_statuses = {}
            company.save()

        await asyncio.gather(start_hh_parsing(browser), start_tv_parsing(browser))
        await browser.close()

        parser_running = False


def start_server():
    # uvicorn.run(app, host="0.0.0.0", port=5000)
    uvicorn.run(app, host="127.0.0.1", port=5000)


app.include_router(router)
templates.env.filters["fromjson"] = fromjson

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    while True:
        if should_restart:
            should_restart = False
            should_stop.clear()
            asyncio.run(run_parsers())
            should_stop.clear()

        time.sleep(5)

    # server_thread.join()

    # Инициализация планировщика для ежедневного запуска парсеров
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(start_parsing, trigger='interval', days=1)
    # scheduler.start()
