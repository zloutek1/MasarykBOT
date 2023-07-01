import re
import json
from datetime import datetime
from typing import List, Dict

import aiohttp
import inject
from bs4 import BeautifulSoup

from src.bot import CourseEntity, CourseRepository


class CourseFetchingService:
    API_URL = "https://is.muni.cz/predmety/predmety_ajax.pl"

    COURSES_PARAMS = {
        "type": "result",
        "operace": "get_courses",
        "pvysl": "5960510",
        "search_text": "",
        "records_per_page": "50"
    }

    COURSES_ALL_PARAMS = {
        "type": "result",
        "operace": "get_courses_all",
        "more_courses": "1",
        "pvysl": "5960510"
    }

    @inject.autoparams('course_repository')
    async def fetch(self, course_repository: CourseRepository) -> List[CourseEntity]:
        courses = await self._fetch(self.COURSES_PARAMS, course_repository)
        courses_all = await self._fetch(self.COURSES_ALL_PARAMS, course_repository)

        return courses + courses_all

    async def _fetch(self, params: Dict, course_repository: CourseRepository) -> List[CourseEntity]:
        content = await self._scrape(params)
        entites = self._parse(content)
        for entity in entites:
            await course_repository.insert(entity)
        return entites

    async def _scrape(self, params: Dict) -> bytes:
        filters = {
            "terms": ["jaro 2023", "podzim 2022"],
            "offered": ["1"],
            "faculties": [1490, 1456, 1451, 1441, 1433, 1431, 1423, 1422, 1421, 1416, 1411],
            "depts_type": ["3"]
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(self.API_URL, data={
                **params,
                "filters": json.dumps(filters)
            })
            resp.raise_for_status()
            return await resp.read()

    def _parse(self, content: bytes) -> List[CourseEntity]:
        data = json.loads(content)
        return [
            self._convert_tag(BeautifulSoup(course, 'lxml'))
            for course in data["table_tr"]
        ]

    @staticmethod
    def _convert_tag(tag) -> CourseEntity:
        content = tag.find("div", {"class": "cat-result-radek"})
        code_link = content.find("a", {"class": "course_link"})
        if ":" in code_link.text:
            faculty, code = code_link.text.split(":")
        else:
            faculty, code = "FI", code_link.text

        url = code_link.attrs.get("href")

        term = re.search(r"\(((?:podzim|jaro)\s\d+)\)", content.find("span").text)
        if term:
            term = term.group(1)

        name = content.find("span").text
        name = name.lstrip().lstrip(faculty).lstrip(":").lstrip(code).strip()
        name = name.rstrip(")").rstrip(term).rstrip("(").strip()

        return CourseEntity(faculty, code, name, "https://is.muni.cz" + url, term, created_at=datetime.now())

