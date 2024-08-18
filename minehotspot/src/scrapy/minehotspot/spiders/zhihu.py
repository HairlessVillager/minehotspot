import hashlib
import json
from dataclasses import replace
from math import ceil

import execjs
import scrapy
from minehotspot.items import ZhihuAnswer, ZhihuPin


class ZhiHuAnswerSpider(scrapy.Spider):
    name = "zhihuanswer"
    allowed_domains = ["www.zhihu.com"]

    def __init__(self, pid: int, cookies_text: str = None, *args, **kwargs):
        super(ZhiHuAnswerSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid
        self.headers = {
            "X-Zse-93": "101_3_3.0",
            "X-Zse-96": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            # 可以添加更多你需要的请求头
        }
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        with open(r"spiders/script.js", "r", encoding="utf-8") as f:
            self.ctx1 = execjs.compile(f.read())
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://www.zhihu.com/question/{self.pid}",
            callback=self.parse_question,
            cookies=self.cookies,
            headers=self.headers,
        )

    def parse_question(self, response):
        # 在起始脚本里面解析数据
        script_text = response.xpath('//script[@id="js-initialData"]/text()').get()
        json_data = json.loads(
            script_text.strip().replace("console.log('", "").replace("');", "")
        )

        # 初始加载的5条回答
        item_a = ZhihuAnswer(None, None, None, None, None)
        for answer in json_data["initialState"]["entities"]["answers"]:
            id = answer
            user = json_data["initialState"]["entities"]["answers"][answer]["author"][
                "name"
            ]
            reply_text = json_data["initialState"]["entities"]["answers"][answer][
                "content"
            ]
            praise_num = json_data["initialState"]["entities"]["answers"][answer][
                "voteupCount"
            ]
            comment_num = json_data["initialState"]["entities"]["answers"][answer][
                "commentCount"
            ]
            url_token = json_data["initialState"]["entities"]["answers"][answer][
                "author"
            ]["urlToken"]
            yield replace(
                item_a,
                id=id,
                user=user,
                reply_text=reply_text,
                praise_num=praise_num,
                comment_num=comment_num,
            )

        # 处理后面的评论，动态加载的
        next = json_data["initialState"]["question"]["answers"][f"{self.pid}"]["next"]
        self.logger.debug(f"{next=}")
        yield scrapy.Request(
            url=next,
            callback=self.parse_answer,
            dont_filter=True,  # TODO: remove duplication filter
            headers=self.headers,
            cookies=self.cookies,
        )

    # 处理回答
    def parse_answer(self, response):
        if response.status == 200:
            json_data = json.loads(response.text)
            # 处理评论
            item_a = ZhihuAnswer(None, None, None, None, None)

            for answer in json_data["data"]:
                id = answer["target"]["author"]["id"]
                user = answer["target"]["author"]["name"]
                reply_text = answer["target"]["excerpt"]
                praise_num = answer["target"]["voteup_count"]
                comment_num = answer["target"]["comment_count"]

                yield replace(
                    item_a,
                    id=id,
                    user=user,
                    reply_text=reply_text,
                    praise_num=praise_num,
                    comment_num=comment_num,
                )

            if not json_data["paging"]["is_end"]:
                next = json_data["paging"]["next"]
                yield scrapy.Request(
                    url=next,
                    callback=self.parse_answer,
                    dont_filter=True,  # TODO: remove duplication filter
                    headers=self.headers,
                    cookies=self.cookies,
                )
        else:
            self.logger.error(f"failed to parse answers: {response.status=}")


class ZhiHuPeopleAnswerSpider(scrapy.Spider):
    name = "zhihupeopleanswer"
    allowed_domains = ["www.zhihu.com"]

    def __init__(self, url_token: str, cookies_text: str = None, *args, **kwargs):
        super(ZhiHuPeopleAnswerSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{url_token=}, {cookies_text=}")
        self.url_token = url_token
        self.headers = {
            "X-Zse-93": "101_3_3.0",
            "X-Zse-96": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            # 可以添加更多你需要的请求头
        }
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        with open(r"spiders/script.js", "r", encoding="utf-8") as f:
            self.ctx1 = execjs.compile(f.read())
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://www.zhihu.com/people/{self.url_token}",
            callback=self.parse_people_answers,
            cookies=self.cookies,
            headers=self.headers,
        )

    def parse_people_answers(self, response):
        answer_num = float(
            response.xpath(r"//*[@id='ProfileMain']/div[1]/ul/li[2]/a/span/text()")
            .get()
            .replace(",", "")
        )
        url_pre = response.url
        answer_pages = ceil(answer_num / 20)
        url_token = self.url_token
        print(f"answer_pages: {answer_pages}")

        # 个人的id与name
        json_data_author = json.loads(
            response.xpath("//script[@id='js-initialData']/text()").get()
        )
        id = json_data_author["initialState"]["entities"]["users"][url_token]["id"]
        user = json_data_author["initialState"]["entities"]["users"][url_token]["name"]

        item_answer = ZhihuAnswer(
            id=id, user=user, reply_text=None, praise_num=None, comment_num=None
        )
        for i in range(1, answer_pages + 1):
            # 破解x-zse-96
            api = f"/api/v4/members/{url_token}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cpaid_info%2Creaction_instruction%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.vessay_info%3Bdata%5B*%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics%3Bdata%5B*%5D.author.vip_info%3Bdata%5B*%5D.question.has_publishing_draft%2Crelationship&offset={(i-1)*20}&limit=20&sort_by=created"
            d_c0 = self.cookies["d_c0"]
            x_zse_93 = "101_3_3.0"
            f = "+".join([x_zse_93, api, d_c0])
            fmds = hashlib.new("md5", f.encode()).hexdigest()
            self.ctx1.call(
                "setLurl", f"https://www.zhihu.com/people/{url_token}/answers?page={i}"
            )
            x_zse_96 = self.ctx1.call("get_x_zse_96", fmds)
            x_zse_96 = "2.0_" + x_zse_96
            self.logger.debug(f"x-zse-96参数:{x_zse_96}")

            # 开始爬取
            self.headers["X-Zse-96"] = x_zse_96
            url = f"https://www.zhihu.com/api/v4/members/{url_token}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cpaid_info%2Creaction_instruction%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.vessay_info%3Bdata%5B*%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics%3Bdata%5B*%5D.author.vip_info%3Bdata%5B*%5D.question.has_publishing_draft%2Crelationship&offset={(i - 1) * 20}&limit=20&sort_by=created"
            yield scrapy.Request(
                url=url,
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_people_answer,
                cb_kwargs={"item": item_answer},
            )

    def parse_people_answer(self, response, item: ZhihuAnswer):
        if response.status == 200:
            self.logger.debug("回答json数据解析成功")
            j = json.loads(response.text)
            for data in j["data"]:
                reply_text = data["excerpt"]
                praise_num = data["voteup_count"]
                comment_num = data["comment_count"]
                yield replace(
                    item,
                    reply_text=reply_text,
                    praise_num=praise_num,
                    comment_num=comment_num,
                )

        else:
            self.logger.error(f"failed to parse prople answer: {response.status=}")


class ZhiHuPeoplePinSpider(scrapy.Spider):
    name = "zhihupeoplepin"
    allowed_domains = ["www.zhihu.com"]

    def __init__(self, url_token: str, cookies_text: str = None, *args, **kwargs):
        super(ZhiHuPeoplePinSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{url_token=}, {cookies_text=}")
        self.url_token = url_token
        self.headers = {
            "X-Zse-93": "101_3_3.0",
            "X-Zse-96": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            # 可以添加更多你需要的请求头
        }
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        with open(r"spiders/script.js", "r", encoding="utf-8") as f:
            self.ctx1 = execjs.compile(f.read())
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://www.zhihu.com/people/{self.url_token}",
            callback=self.parse_people_pins,
            cookies=self.cookies,
            headers=self.headers,
        )

    def parse_people_pins(self, response):
        pin_num = float(
            response.xpath(r"//*[@id='ProfileMain']/div[1]/ul/li[7]/a/span/text()")
            .get()
            .replace(",", "")
        )
        url_pre = response.url
        pin_pages = ceil(pin_num / 20)
        url_token = self.url_token
        print(f"pin_pages: {pin_pages}")

        # 个人的id与name
        json_data_author = json.loads(
            response.xpath("//script[@id='js-initialData']/text()").get()
        )
        id = json_data_author["initialState"]["entities"]["users"][url_token]["id"]
        user = json_data_author["initialState"]["entities"]["users"][url_token]["name"]

        item_pin = ZhihuPin(
            id=id, user=user, title=None, content=None, like_num=None, comment_num=None
        )
        for i in range(1, pin_pages + 1):
            # 破解x-zse-96
            api = f"/api/v4/v2/pins/{url_token}/moments?offset={(i-1)*20}&limit=20&includes=data%5B*%5D.upvoted_followees%2Cadmin_closed_comment"
            d_c0 = self.cookies["d_c0"]
            x_zse_93 = "101_3_3.0"
            f = "+".join([x_zse_93, api, d_c0])
            fmds = hashlib.new("md5", f.encode()).hexdigest()
            self.ctx1.call(
                "setLurl", f"https://www.zhihu.com/people/{url_token}/pins?page={i}"
            )
            x_zse_96 = self.ctx1.call("get_x_zse_96", fmds)
            x_zse_96 = "2.0_" + x_zse_96
            self.logger.debug(f"x-zse-96参数:{x_zse_96}")

            # 开始爬取
            self.headers["X-Zse-96"] = x_zse_96
            url = f"https://www.zhihu.com/api/v4/v2/pins/{url_token}/moments?offset={(i-1)*20}&limit=20&includes=data%5B*%5D.upvoted_followees%2Cadmin_closed_comment"
            yield scrapy.Request(
                url=url,
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_people_pin,
                cb_kwargs={"item": item_pin},
            )

    def parse_people_pin(self, response, item: ZhihuPin):
        if response.status == 200:
            self.logger.debug("successed to parse people pin")
            j = json.loads(response.text)
            for data in j["data"]:
                title = data["content"][0]["title"]
                content = data["content"][0]["content"]
                like_num = data["like_count"]
                comment_num = data["comment_count"]
                yield replace(
                    item,
                    title=title,
                    content=content,
                    like_num=like_num,
                    comment_num=comment_num,
                )
        else:
            self.logger.error("failed to parse people pin")
