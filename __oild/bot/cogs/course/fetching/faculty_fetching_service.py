import json
from datetime import datetime
from typing import List

import aiohttp
import inject
from bs4 import BeautifulSoup

from src.bot import FacultyEntity, FacultyRepository


class FacultyFetchingService:
    API_URL = "https://is.muni.cz/predmety/predmety_ajax.pl"

    PARAMS = {
        "type": "dropdown",
        "operace": "choice_chosen",
        "name": "dropdownsel",
        "value": "faculties",
        "filters": json.dumps({
            "terms": ["jaro 2023","podzim 2022"],
            "offered": ["1"]
        })
    }

    @inject.autoparams('faculty_repository')
    async def fetch(self, faculty_repository: FacultyRepository) -> List[FacultyEntity]:
        content = await self._scrape()
        entities = self._parse(content)
        for entity in entities:
            await faculty_repository.insert(entity)
        return entities

    async def _scrape(self) -> bytes:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(self.API_URL, data=self.PARAMS)
            resp.raise_for_status()
            return await resp.read()

    def _parse(self, content: bytes) -> List[FacultyEntity]:
        data = json.loads(content)
        soup = BeautifulSoup(data["data"], 'lxml')
        return [
            self._convert_tag(tag)
            for tag in soup.find_all("option")
        ]

    @staticmethod
    def _convert_tag(tag) -> FacultyEntity:
        return FacultyEntity(
            int(tag.attrs.get('value')),
            tag.attrs.get('data-abbr_fak'),
            tag.text,
            created_at=datetime.now()
        )
