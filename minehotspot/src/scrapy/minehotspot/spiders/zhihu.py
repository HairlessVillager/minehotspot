import hashlib
import json
from dataclasses import replace
from math import ceil

import execjs
import requests
import scrapy
from minehotspot.items import ZhihuQuestion, ZhihuAnswer, ZhihuPin

class ZhiHuQuestionSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]

    def __init__(self, pid: int, cookies_text: str = None, *args, **kwargs):
        super(ZhiHuQuestionSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid
        self.headers = {
            'X-Zse-93': '101_3_3.0',
            'X-Zse-96': '',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            # 可以添加更多你需要的请求头
        }
        cookies_text = """
        _zap=219c07c1-f5f7-4ea9-9e56-0968f949cdcd; d_c0=AQBSaJgk5hiPTs3SaGhseVYL8t7skrpEWxs=|1720541492; __snaker__id=ifWc7mfWd3M1kab8; captcha_ticket_v2=2|1:0|10:1720541502|17:captcha_ticket_v2|728:eyJ2YWxpZGF0ZSI6IkNOMzFfblFXbWxvdzBCVW9HRHlsa19fME40OEFxZ3JzOWFSVnMwd2dNSlJqRkdaUVFHVVJzWElLbXdiQ19NMjVwRGRINHhja212XzlBVTAyMTRVU0lLRWtoUS4wZEhQckFQeWRfR2NlZ0g2YUtNUnFlRDBBMVFDNVdpaXhJanlkKmFXaS40blFOa1doSmJkUWx0ck56UDhXMGxIVnBYUTNNSWk4VXVqM2cqMGJsdHpJSEJtVV9teEtmd1EqSWQqKjlTanVPMHFsNHo2ZWp0amJWMHpITUd1U2Njb3o2KnZweW9nVDFiRUp6cWt4elR1eWNSb3daRldPY1V2cHlOUTI4SExSb0dDT1kxMmlFdDlnTnZudVhMTGJtbHN6RmJaamhhODVsdXd4R3MyS25yS0hTS2lOeVFuemFkVDNMOWM0QypjbTlzWS5mWS5xSC51TUFNaUlmck90dyo2TUFNUFg1VE1mU0tTNm13NkloZzYzUDB2VEd6T212S0hJZC54ZlM5MTJ4dHE4eGp3U20wSGt2bGJMbm5GWTZWX2NocXpWOTAzNGswVUxCRGVWNHBFdnAqZ18xbEZ3aXdjKmlfam9uajhFOHFReVVTektBOHJ6MjBqQWtVczYuNjBiellyMVlzUVBTQkQ2bFRCSE1IWUtWb3g0VVZvSGdjWVRfbHFyZzVVUmxpb0ZUOVg3N192X2lfMSJ9|fef14ba89958bfc0780f1c8f47995925497d06b5f11a4e94284851898bd6b14a; z_c0=2|1:0|10:1720541520|4:z_c0|92:Mi4xTjJQUFFRQUFBQUFCQUZKb21DVG1HQ1lBQUFCZ0FsVk5VSzk2WndDWUZMNjhqSVAxMms0a3J5RlhQNWdvTGFiLU9B|92c7fa59edf6e27390fd57fd0699f25d31ec33ca72afb2df916c41db85af018e; q_c1=b7eeeeeef80d487db51b62c6ed30e426|1720541520000|1720541520000; __zse_ck=001_CjwbAUUe31Ige4Vs2UZGKyg14t1EuCOi1dwE+yjFAPK2PCRARc1g1Ck5QjcDdw=myqKFbM+odh4GuHqrl38kOVWrezR6U+v=kG/aQ4pUAZc7+ZObQGkI=h9+PWpte4Ev; _xsrf=bIRHdmI55xWyEmsxKGBinRNBKfB7KemK; gdxidpyhxdE=97H%2Bx%2Fky8kgkWxOnSqv9VB3OdqJaG9MBP9bk4YkhUOlmzB%2BngjHaKu5uVrPJi3IsVtJlipixGg%2BWX4vN8hfi%2Fvca8A4S1YXw7583v8Q6HoDOGEcoe9rPhA6%2B8Zu2rSpSrI9dAw2vki0QL5YIzxbwM2Qmf3pNGZaEdnf1eO0Tksg4Oa3D%3A1720545727407; tst=r; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1720619343,1720626802,1720660835,1720676321; HMACCOUNT=47A108C0894DBC65; SESSIONID=OKanRPPuxLFeVBfQYjOVjPDtANvYdIHcvJVdYfINTRx; JOID=VlwcAUnSGUtb2j0kNNXv179JH8QhnV8hNY5teUqsVQA1jHlCaDtwzzvcMCI_bnzuI6m8H_HnU3051AlhuTE52fs=; osd=W1wVCkPfGUJQ0DAkPd7l2r9AFM4snVYqP4NtcEGmWAA8h3NPaDJ7xTbcOSk1Y3znKKOxH_jsWXA53QJrtDEw0vE=; BAIDU_SSP_lcr=https://cn.bing.com/; BEC=b0eab4e8c2499716509071e260d20835; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1720676344    
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        with open(r'spiders/script.js', 'r', encoding='utf-8') as f:
            self.ctx1 = execjs.compile(f.read())
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://www.zhihu.com/question/{self.pid}",
            callback=self.parse_question,
            cookies=self.cookies,
            headers=self.headers
        )

    def parse_question(self, response):
        # 在起始脚本里面解析数据
        script_text = response.xpath('//script[@id="js-initialData"]/text()').get()
        json_data = json.loads(script_text.strip().replace('console.log(\'', '').replace('\');', ''))

        # 问题的解析
        item_q = ZhihuQuestion(None,None,None)
        id= json_data["initialState"]["entities"]["questions"][f'{self.pid}']["id"]
        title = json_data["initialState"]["entities"]["questions"][f'{self.pid}']["title"]
        des= json_data["initialState"]["entities"]["questions"][f'{self.pid}']["detail"]
        yield replace(item_q,id=id,title=title,des=des)

        # 初始加载的5条回答
        item_a = ZhihuAnswer(None,None,None,None,None)
        for answer in json_data["initialState"]["entities"]["answers"]:
            id = answer
            user = json_data["initialState"]["entities"]["answers"][answer]["author"]["name"]
            reply_text = json_data["initialState"]["entities"]["answers"][answer]["content"]
            praise_num = json_data["initialState"]["entities"]["answers"][answer]["voteupCount"]
            comment_num= json_data["initialState"]["entities"]["answers"][answer]["commentCount"]
            url_token = json_data["initialState"]["entities"]["answers"][answer]["author"]["urlToken"]
            # 处理这个人的所有回答和想法
            if url_token!="":
                yield scrapy.Request(
                    url=f'https://www.zhihu.com/people/{url_token}',
                    callback=self.parse_people_answers_and_pins,
                    headers=self.headers,
                    cookies=self.cookies,
                    meta={
                        'url_token': url_token,


                    }
                )
            yield replace(item_a,id=id,user=user,reply_text=reply_text,praise_num=praise_num,comment_num=comment_num)

        # 处理后面的评论，动态加载的
        next = json_data["initialState"]["question"]["answers"][f'{self.pid}']["next"]
        self.logger.debug(f'下一个链接地址:{next}')
        yield scrapy.Request(
            url=next,
            callback=self.parse_answer,
            dont_filter=True,  # TODO: remove duplication filter
            headers=self.headers,
            cookies=self.cookies
         )

    # 处理回答
    def parse_answer(self, response):
        if response.status == 200:
            json_data = json.loads(response.text)
            # 处理评论
            item_a = ZhihuAnswer(None,None,None,None,None)

            for answer in json_data["data"]:
                id = answer["target"]["author"]["id"]
                user = answer["target"]["author"]["name"]
                reply_text = answer["target"]["excerpt"]
                praise_num = answer["target"]["voteup_count"]
                comment_num = answer["target"]["comment_count"]
                url_token = answer["target"]["author"]["url_token"]
                # 处理这个人的所有回答和想法
                if url_token!="":
                    yield scrapy.Request(
                        url=f'https://www.zhihu.com/people/{url_token}',
                        callback=self.parse_people_answers_and_pins,
                        dont_filter=True,  # TODO: remove duplication filter
                        headers=self.headers,
                        cookies=self.cookies,
                        meta={
                            'url_token': url_token,
                        }
                    )

                yield replace(item_a,id=id,user=user,reply_text=reply_text,praise_num=praise_num,comment_num=comment_num)


            if not json_data["paging"]["is_end"]:
                next = json_data["paging"]["next"]
                yield scrapy.Request(
                    url=next,
                    callback=self.parse_answer,
                    dont_filter=True,  # TODO: remove duplication filter
                    headers=self.headers,
                    cookies=self.cookies
                )
        else:
            self.logger.debug(f"Answer list返回错误：{response.status}")

    # 个人主页的问题和想法
    def parse_people_answers_and_pins(self, response):
        answer_num = float(response.xpath(r"//*[@id='ProfileMain']/div[1]/ul/li[2]/a/span/text()").get().replace(",", ""))
        pin_num = float(response.xpath(r"//*[@id='ProfileMain']/div[1]/ul/li[7]/a/span/text()").get().replace(",", ""))
        url_pre = response.url
        answer_pages = ceil(answer_num / 20)
        pin_pages = ceil(pin_num / 20)
        url_token = response.meta.get("url_token")
        print(f'answer_pages: {answer_pages}, pin_pages: {pin_pages}')

        # 个人的id与name
        json_data_author = json.loads(response.xpath("//script[@id='js-initialData']/text()").get())
        id = json_data_author["initialState"]["entities"]["users"][url_token]["id"]
        user = json_data_author["initialState"]["entities"]["users"][url_token]["name"]

        item_answer = ZhihuAnswer(id=id, user=user,reply_text=None,praise_num=None,comment_num=None)
        for i in range(1, answer_pages + 1):
            # 破解x-zse-96
            api = f"/api/v4/members/{url_token}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cpaid_info%2Creaction_instruction%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.vessay_info%3Bdata%5B*%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics%3Bdata%5B*%5D.author.vip_info%3Bdata%5B*%5D.question.has_publishing_draft%2Crelationship&offset={(i-1)*20}&limit=20&sort_by=created"
            d_c0=self.cookies["d_c0"]
            x_zse_93 = "101_3_3.0"
            f = "+".join([x_zse_93, api, d_c0])
            fmds = hashlib.new("md5", f.encode()).hexdigest()
            self.ctx1.call("setLurl", f'https://www.zhihu.com/people/{url_token}/answers?page={i}')
            x_zse_96 = self.ctx1.call("get_x_zse_96", fmds)
            x_zse_96 = "2.0_" + x_zse_96
            self.logger.debug(f"x-zse-96参数:{x_zse_96}")

            # 开始爬取
            self.headers['X-Zse-96'] = x_zse_96
            url = f'https://www.zhihu.com/api/v4/members/{url_token}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cpaid_info%2Creaction_instruction%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.vessay_info%3Bdata%5B*%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics%3Bdata%5B*%5D.author.vip_info%3Bdata%5B*%5D.question.has_publishing_draft%2Crelationship&offset={(i - 1) * 20}&limit=20&sort_by=created'
            yield scrapy.Request(
                url=url,
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_people_answer,
                cb_kwargs={"item":item_answer}
            )

        item_pin = ZhihuPin(id=id, user=user,title=None,content=None,like_num=None,comment_num=None)
        for i in range(1, pin_pages + 1):
            # 破解x-zse-96
            api =f'/api/v4/v2/pins/{url_token}/moments?offset={(i-1)*20}&limit=20&includes=data%5B*%5D.upvoted_followees%2Cadmin_closed_comment'
            d_c0=self.cookies["d_c0"]
            x_zse_93 = "101_3_3.0"
            f = "+".join([x_zse_93, api, d_c0])
            fmds = hashlib.new("md5", f.encode()).hexdigest()
            self.ctx1.call("setLurl", f'https://www.zhihu.com/people/{url_token}/pins?page={i}')
            x_zse_96 = self.ctx1.call("get_x_zse_96", fmds)
            x_zse_96 = "2.0_" + x_zse_96
            self.logger.debug(f"x-zse-96参数:{x_zse_96}")

            # 开始爬取
            self.headers['X-Zse-96'] = x_zse_96
            url = f'https://www.zhihu.com/api/v4/v2/pins/{url_token}/moments?offset={(i-1)*20}&limit=20&includes=data%5B*%5D.upvoted_followees%2Cadmin_closed_comment'
            yield scrapy.Request(
                url=url,
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_people_pin,
                cb_kwargs={"item":item_pin}
            )



    # 个人主页问题
    def parse_people_answer(self, response,item:ZhihuAnswer):
        if response.status==200:
            self.logger.debug("回答json数据解析成功")
            j=json.loads(response.text)
            for data in j['data']:
                reply_text=data["excerpt"]
                praise_num=data["voteup_count"]
                comment_num=data["comment_count"]
                yield replace(item,reply_text=reply_text,praise_num=praise_num,comment_num=comment_num)

        else:
            self.logger.debug("知乎个人主页问题请求失败")





    # 个人主页想法第一页
    def parse_people_pin(self, response,item:ZhihuPin):
        if response.status == 200:
            self.logger.debug("想法数据解析成功")
            j = json.loads(response.text)
            for data in j['data']:
                title = data['content'][0]['title']
                content = data['content'][0]['content']
                like_num = data["like_count"]
                comment_num = data["comment_count"]
                yield replace(item, title=title, content=content, like_num=like_num, comment_num=comment_num)

        else:
            self.logger.debug("知乎个人主页想法请求失败")
