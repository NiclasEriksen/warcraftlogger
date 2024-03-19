from typing import Union

from .constants import *
import requests
from .query import reports_query, report_query
from datetime import datetime, timedelta


class APIException(Exception):
    message: str = "Warcraft Logs API threw an unknown error"

    def __str__(self):
        return f"API Exception: {self.message}"


def get_id_from_url(url: str) -> Union[str, None]:
    if not len(url) or not "reports/" in url:
        return None
    u: str = url.split("reports/")[-1]
    return u.split("#")[0]


def sec_to_str(sec: float) -> str:
    if sec > 3600:
        return f"{int(sec // 3600)}h{int(sec % 3600) // 60}m"
    elif sec > 60:
        return f"{int(sec) // 60}m{int(sec) % 60}s"
    return f"{int(sec)}s"


class Character:
    name: str = ""
    player_class_id: int = -1


    def __init__(self, api_obj: dict):
        if "name" in api_obj:
            self.name = api_obj["name"]
        if "classID" in api_obj:
            self.player_class_id = api_obj["classID"]
            if self.player_class_id == 0:
                print(api_obj)
        else:
            print("classID not in api_obj")
            print(api_obj)

    @property
    def player_class(self) -> str:
        if self.player_class_id in CLASS_NAME:
            print(f"{self.name}: {self.player_class_id}, {CLASS_NAME[self.player_class_id]}")
            return CLASS_NAME[self.player_class_id]
        return "UNKNOWN CLASS ID: " + str(self.player_class_id)

    def __repr__(self) -> str:
        return f"<Player '{self.name}' -- {self.player_class}>"


class Fight:
    name: str = ""
    start_time: timedelta = timedelta(seconds=0)
    end_time: timedelta = timedelta(seconds=0)

    def __init__(self, api_obj: dict):
        if "name" in api_obj:
            self.name = api_obj["name"]
        if "startTime" in api_obj:
            self.start_time = timedelta(seconds=api_obj["startTime"] / 1000)
        if "endTime" in api_obj:
            self.end_time = timedelta(seconds=api_obj["endTime"] / 1000)

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time

    @property
    def duration_str(self) -> str:
        return sec_to_str(self.duration.seconds)

    def __repr__(self) -> str:
        return f"<Fight '{self.name}' -- {self.duration_str}>"


class Report:
    title: str = ""
    id: str = ""
    start_time: datetime = datetime.now()
    end_time: datetime = datetime.now()
    segment_count: int = 0
    characters: list = []
    fights: list = []
    raid: str = ""
    deaths: int = 0
    execution_rank: int = 0
    speed_rank: int = 0

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time

    @property
    def duration_str(self) -> str:
        return sec_to_str(self.duration.seconds)

    def get_earliest_start(self) -> Union[timedelta, None]:
        earliest = None
        for f in self.fights:
            if earliest is None or f.start_time < earliest:
                earliest = f.start_time
        return earliest

    def get_latest_end(self) -> Union[timedelta, None]:
        latest = None
        for f in self.fights:
            if latest is None or f.end_time > latest:
                latest = f.end_time
        return latest

    def get_rankings_from_data(self, data: dict):
        full_raid = None
        try:
            for encounter in data:
                if encounter["encounter"]["name"] == self.raid:
                    full_raid = encounter
                    break
            if full_raid is not None:
                self.speed_rank = full_raid["speed"]["rankPercent"]
                self.execution_rank = full_raid["execution"]["rankPercent"]
                self.deaths = full_raid["deaths"]
            else:
                print("NO FULL RAID")
        except KeyError as e:
            print(e)

    def from_api_object(self, obj: dict):
        if "code" in obj:
            self.id = obj["code"]
        if "title" in obj:
            self.title = obj["title"]
        if "segments" in obj:
            self.segment_count = obj["segments"]
        if "rankedCharacters" in obj:
            self.characters = [
                Character(c) for c in obj["rankedCharacters"]
            ]
            if "masterData" in obj:
                if "actors" in obj["masterData"]:
                    for c in self.characters:
                        if c.player_class_id == 0:
                            actor = None
                            for a in obj["masterData"]["actors"]:
                                c.player_class_id = lookup_class_id(a["subType"])

        if "fights" in obj:
            self.fights = [
                Fight(f) for f in obj["fights"]
            ]
        if "zone" in obj:
            if obj["zone"] is not None:
                self.raid = obj["zone"]["name"]
        if "startTime" in obj:
            start_offset = self.get_earliest_start()
            end_offset = self.get_latest_end()
            if start_offset is not None:
                self.start_time = datetime.fromtimestamp(obj["startTime"] / 1000) + start_offset
                self.end_time = datetime.fromtimestamp(obj["startTime"] / 1000) + end_offset
            else:
                self.start_time = datetime.fromtimestamp(obj["startTime"] / 1000)
                if "endTime" in obj:
                    self.end_time = datetime.fromtimestamp(obj["endTime"] / 1000)
        if "zone" in obj:
            if obj["zone"] is not None:
                self.raid = obj["zone"]["name"]
            if "rankings" in obj:
                self.get_rankings_from_data(obj["rankings"]["data"])

    def __repr__(self) -> str:
        return f"<Report '{self.title}' -- {self.id}>"


class APIManager:
    def __init__(self):
        self.token = ""
        self.user_id = WARCRAFT_LOGS_CLIENT_ID
        self.secret = WARCRAFT_LOGS_SECRET
        self.headers = {}
        self.reports = {}
        self.authenticated = False

    async def auth_user(self) -> str:
        try:
            response = requests.post(
                WARCRAFT_LOGS_AUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=(self.user_id, self.secret)
            )
            self.token = response.json()["access_token"]
            self.headers["Authorization"] = f'Bearer {self.token}'
            self.authenticated = True
        except Exception as e:
            print("Error authenticating against API.")
            raise APIException(f"Authentication error: {e}")

    async def get_reports(self):
        variables = {"guild_id": GUILD_ID}
        try:
            response = requests.get(
                url=WARCRAFT_LOGS_API_URL,
                json={"query": reports_query, "variables": variables},
                headers=self.headers
            )
        except Exception as e:
            raise APIException(f"Unable to fetch reports, undefined error.")
        if response.status_code == 200:
            try:
                data = response.json()["data"]["reportData"]["reports"]["data"]
            except KeyError:
                print(response.json())
                print("Key error when requesting data")
                data = []
            if len(data) > 0:
                for log in data:
                    r = Report()
                    r.from_api_object(log)
                    self.reports[r.id] = r
            else:
                print(data)
        else:
            print("Error during fetching of reports")
            print(response)
            raise APIException(f"Unable to fetch reports, status code {response.status_code}")

    async def get_report(self, report_id: str) -> Union[Report, None]:
        variables = {"report_id": report_id}
        try:
            response = requests.get(
                url=WARCRAFT_LOGS_API_URL,
                json={"query": report_query, "variables": variables},
                headers=self.headers
            )
            if response.status_code == 200:
                # print(response.json())
                data = response.json()["data"]["reportData"]["report"]
                r = Report()
                r.from_api_object(data)
                return r
            else:
                print(response.content)
                raise APIException(f"Unable to fetch single report, status code {response.status_code}")

        except Exception as e:
            print(e)
            raise APIException(f"Error during fetching of report: {e}")
