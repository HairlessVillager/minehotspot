# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass


@dataclass
class TiebaComment:
    pid: int = None
    title: str = None
    text: str = None
    floor: int = None
    time: str = None  # format: "%Y-%m-%d %H:%M", e.g. "2024-05-15 10:42"
    uid: str = None  # TODO: unknown format


@dataclass
class TiebaTotalComment:
    pid: str = None
    title: str = None
    time: str = None  # format: "%Y-%m-%d %H:%M", e.g. "2024-05-15 10:42"
    total: int = None
