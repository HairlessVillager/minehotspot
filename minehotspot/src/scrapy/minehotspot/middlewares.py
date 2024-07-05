# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from fake_useragent import UserAgent
import requests

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class RandomUserAgentDownloadMiddlware:

    def __init__(self, crawler):
        super(RandomUserAgentDownloadMiddlware, self).__init__()
        self.ua = UserAgent()
        self.ua_type = crawler.settings.get("RANDOM_UA_TYPE", "random")

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        def get_ua():
            return getattr(self.ua, self.ua_type)
        request.headers.setdefault('User-Agent', get_ua())

    def spider_opened(self, spider):
        pass
        # spider.logger.info("Spider opened: %s" % spider.name)


class ProxyMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def get_proxy(self, logger):
        cnt = 0
        while cnt < 10:
            try:
                proxy = requests.get("https://proxypool.scrape.center/random").text
                logger.debug(f"try {proxy=}...{cnt=}")
                ip = {"http": "http://" + proxy, "https": "https://" + proxy}
                r = requests.get("https://www.qq.com", proxies=ip, timeout=4)
                logger.debug(f"{r.status_code=}")
                if r.status_code in [301, 302, 200]:
                    return proxy
            except Exception as e:
                logger.debug(f"{e}")
            cnt += 1
        # with open("proxy_list.txt", "r", encoding="utf-8") as f:
        #     proxies = f.readlines()
        # proxy = random.choice(proxies).strip()

    def process_request(self, request, spider):
        proxy = self.get_proxy(spider.logger)
        if not proxy:
            proxy = "broken-proxy"
        spider.logger.info(f"using {proxy=}")
        request.meta['proxy'] = f"https://{proxy}"

    def spider_opened(self, spider):
        pass
        # spider.logger.info("Spider opened: %s" % spider.name)


class RemoveHtmlCommentDownloadMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_response(self, request, response, spider):
        # spider.logger.info(f'{response.headers[b"Content-Type"]=}')
        if b"text/html" in response.headers[b"Content-Type"]:
            spider.logger.debug("removed html comments")
            response = response.replace(body=response.body.replace(b"<!--", b"").replace(b"-->", b""))
        return response

    def spider_opened(self, spider):
        pass
        # spider.logger.info("Spider opened: %s" % spider.name)


class CheckCAPTCHADownloadMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_response(self, request, response, spider):
        if response.status == 302 and b"captcha" in response.headers[b"Location"]:
            spider.logger.error(f"missing {request.url} for CAPTCHA")
            raise IgnoreRequest
        return response

    def spider_opened(self, spider):
        pass
        # spider.logger.info("Spider opened: %s" % spider.name)
