# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass


@dataclass
class TiebaComment:
    pid: int
    text: str
    floor: int
    time: int
    uid: int
    uname: str


@dataclass
class TiebaTotalComment:
    pid: str
    title: str
    topic: str
    time: int
    total: int
