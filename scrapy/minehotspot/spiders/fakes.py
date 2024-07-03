import csv

import scrapy

from minehotspot.items import TiebaComment, TiebaTotalComment


class TiebaPostSpider(scrapy.Spider):
    name = "tiebapost_fake"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, pid: int, cookies_text: str = None, *args, **kwargs):
        super(TiebaPostSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid

        cookies_text = """
        FAKE_COOKIES=xxx
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request("https://www.baidu.com", self.fake_callback, dont_filter=True)

    def fake_callback(self, response):
        with open("post20240702.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield TiebaComment(
                    pid=row["pid"],
                    title=row["title"],
                    text=row["text"],
                    floor=row["floor"],
                    time=row["time"],
                    uid=row["uid"],
                )


class TiebaListSpider(scrapy.Spider):
    name = "tiebalist_fake"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, start: str, end: str, cookies_text: str = None, *args, **kwargs):
        """
        start, end:
            - (2000, 5000)
        """
        super(TiebaListSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{start=}, {end=}, {cookies_text=}")
        self.start = int(start)
        self.end = int(end)

        cookies_text = """
        FAKE_COOKIES=xxx
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request("https://www.baidu.com", self.fake_callback, dont_filter=True)

    def fake_callback(self, response):
        with open("list20240702.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield TiebaTotalComment(
                    pid=row["pid"],
                    title=row["title"],
                    time=row["time"],
                    total=row["total"],
                )
