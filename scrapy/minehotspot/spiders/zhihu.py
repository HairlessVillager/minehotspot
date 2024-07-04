import json

import scrapy
from minehotspot.items import ZhihuQuestion,ZhihuAnswer

class ZhiHuQuestionSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]

    def __init__(self,pid:int, cookies_text:str=None, *args, **kwargs):
        super(ZhiHuQuestionSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            # 可以添加更多你需要的请求头
        }

        cookies_text = """
            _zap=a7336e54-5999-40eb-bb4d-6e251f130c08; d_c0=AeDQXacOsRePTnt4xdjNi0tzzjuqEw7R4lI=|1699799101; YD00517437729195%3AWM_TID=74ItawCnrnVARVFVQRKFn%2BEeqJ67rjY0; YD00517437729195%3AWM_NI=Q95lMZfJ7kQLnMIfISc4whvaCBEQtRPgIOYnkqXUr5%2FIkxV9CbWSDqNvj9%2BghS8SA5vzh4IEeSs8CQLctoV3moJW5v8YVkPNIV4tjLNvU3Hn2yts78cVG2ooS5TxdUUWTGY%3D; YD00517437729195%3AWM_NIKE=9ca17ae2e6ffcda170e2e6eeb1eb3390bdc0d4b86f8e968fa6c84e868f9fb1c43ae98999bbbb4498978697ae2af0fea7c3b92a93e7fb8dd052a696f98cd448ae938787cc59a1ecb989f56b819e8bb2f75a94b987b0dc66a9af98b6f13fed97a599d53381be99b4c77b8eaaa6daaa6dac8df8b4c43fb6a6a8d5cc4fa78dbdd9c25b90bdbc90d539afb186b8b87efc879a8cd3468b8afc95e9488eaa9bd4cb66f2a7bc94b634a18a89d3ee6591eb9c99e75f97899ca8dc37e2a3; _xsrf=XLxgydsLJp1tMLx2y2lt5A7yMfvJ8R4x; __zse_ck=001_14J9vR1aLO5CbIG2MiTi2mHxVzdEgKw+Tyc=5bYyqsAI2kMSQhHstTu1u1So3E6jA8KSGI8kGEb7v8Bbi5TDNsryHEpyMQWXs18ZIDMIiS236=rW3Z2K9mGL=YwyI7FK; q_c1=a11a3513a3964feb99c5b2f22f15ca74|1719886104000|1719886104000; z_c0=2|1:0|10:1719886174|4:z_c0|80:MS4xMGxWOFBRQUFBQUFtQUFBQVlBSlZUVldpYVdmQktnVVRpZUdCOUpsb29BRGRNa3dYUWU4OHVBPT0=|a379b2d704443f350d9d9eb400b0f2a5972f3208ae7f184859e5b6cd8f7fb956; ff_supports_webp=1; tst=r; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1719974069,1719976164,1719977742,1719990622; SESSIONID=3Q2FPamK23GACddDdkhMjWotj5F72zLzvs1rROJ3TQi; JOID=W1kQAUrFOa9gW5dWc87ZNxD1kudo_myaJQP-Pz__AuwmG_s6M5fDLw1bm1V3l3m28muTej6kaFLd2xAOnKbpH4Q=; osd=Vl8WBUrIP6lkW5pQdcrZOhbzludl-GqeJQ74OTv_D-ogH_s3NZHHLwBdnVF3mn-w9muefDigaF_b3RQOkaDvG4Q=; BAIDU_SSP_lcr=https://cn.bing.com/; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1719991893; unlock_ticket=AAAT1x9gfxUmAAAAYAJVTWAFhWZHgDdzfjcdMmL0SVfMNfoQj3oSBg==; KLBRSID=b33d76655747159914ef8c32323d16fd|1719992155|1719990620; BEC=d892da65acb7e34c89a3073e8fa2254f
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://www.zhihu.com/question/{self.pid}",
            callback=self.parse_question,
            cookies=self.cookies,
            headers=self.headers
        )

    def parse_question(self,response):
        # 在起始脚本里面解析数据
        script_text = response.xpath('//script[@id="js-initialData"]/text()').get()
        json_data = json.loads(script_text.strip().replace('console.log(\'', '').replace('\');', ''))
        self.logger.debug(script_text)

        #问题的解析
        item_q=ZhihuQuestion()
        item_q["id"] = json_data["initialState"]["entities"]["questions"][f'{self.pid}']["id"]
        item_q["title"] = json_data["initialState"]["entities"]["questions"][f'{self.pid}']["title"]
        item_q["des"] = json_data["initialState"]["entities"]["questions"][f'{self.pid}']["detail"]
        yield item_q

        #初始加载的5条回答
        item_a=ZhihuAnswer()
        for answer in json_data["initialState"]["entities"]["answers"]:
            item_a["id"] =  answer
            item_a["user"] = json_data["initialState"]["entities"]["answers"][answer]["author"]["name"]
            item_a["reply_text"] = json_data["initialState"]["entities"]["answers"][answer]["content"]
            item_a["praise_num"] = json_data["initialState"]["entities"]["answers"][answer]["voteupCount"]
            item_a["comment_num"] = json_data["initialState"]["entities"]["answers"][answer]["commentCount"]
            yield item_a

        #处理后面的评论，动态加载的
        next = json_data["initialState"]["question"]["answers"][f'{self.pid}']["next"]
        self.logger.debug(f'下一个链接地址:{next}')
        yield scrapy.Request(
            url=next,
            callback=self.parse_answer,
            dont_filter=True,  # TODO: remove duplication filter
            headers=self.headers,
            cookies=self.cookies
        )


    def parse_answer(self,response):
        json_data = json.loads(response.text)
        print(json_data)
        # 处理评论
        item_a = ZhihuAnswer()
        for answer in json_data["data"]:
            item_a["id"] = answer["target"]["author"]["id"]
            item_a["user"] = answer["target"]["author"]["name"]
            item_a["reply_text"] = answer["target"]["content"]
            item_a["praise_num"] = answer["target"]["voteup_count"]
            item_a["comment_num"] = answer["target"]["comment_count"]
            yield item_a

        print(json_data["paging"]["is_end"])
        if not json_data["paging"]["is_end"]:
            next = json_data["paging"]["next"]
            yield scrapy.Request(
                url=next,
                callback=self.parse_answer,
                dont_filter=True,  # TODO: remove duplication filter
                headers=self.headers,
                cookies=self.cookies
            )


