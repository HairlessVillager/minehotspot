import re
import json
from math import ceil
import time
from dataclasses import replace

import scrapy

from minehotspot.items import TiebaComment, TiebaTotalComment


class TiebaPostSpider(scrapy.Spider):
    name = "tiebapost"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, pid: int, cookies_text: str = None, *args, **kwargs):
        """
        pid:
            no: /p/8985907273
            yes: 8985907273
        """
        super(TiebaPostSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid

        # TODO: insecure data, remove this
        cookies_text = """
        XFI=343e7c10-3382-11ef-9b40-a9cc5fd15163; XFCS=3E9F076C2751C30DC50332AE8944104E7F16A02EBF81E1BD057431FF387D5DC7; XFT=dFXK3hrcb6NWmHLESz+s8J3wd+olz+jXY1zCcLFDPXY=; BIDUPSID=942C8B99F0CBA1B803D036BCDF45981A; PSTM=1692155596; BAIDUID=942C8B99F0CBA1B8DF41FAAA8136952E:SL=0:NR=10:FG=1; MCITY=-218%3A; IS_NEW_USER=4e2fab2e31d833a251600277; TIEBAUID=5c40c0e62d2efb5f13d68ffd; BDUSS=FqcnRkVHlENThwb2oyQXAzWHY2dlVpRndDenpDWDFTYkVtUGlLUUVCRFY1M3htSVFBQUFBJCQAAAAAAAAAAAEAAABJI-~ntOXD8VZpbGxhZ2VyMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANVaVWbVWlVmN3; STOKEN=fbf80c9c315856117aa2d4e1e58b9b43d866a7e8a0d8ef16b66cbefbf7411a2b; BAIDU_WISE_UID=wapp_1717132013271_460; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1715904525,1716034140,1716172038,1717132013; __bid_n=1903dd28f588208f379f79; H_WISE_SIDS=60334_60376; BAIDUID_BFESS=942C8B99F0CBA1B8DF41FAAA8136952E:SL=0:NR=10:FG=1; BDUSS_BFESS=FqcnRkVHlENThwb2oyQXAzWHY2dlVpRndDenpDWDFTYkVtUGlLUUVCRFY1M3htSVFBQUFBJCQAAAAAAAAAAAEAAABJI-~ntOXD8VZpbGxhZ2VyMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANVaVWbVWlVmN3; ZFY=Uqpg2LECCGjr16ZkdMVx41TwzMuNYGINbmInDPFwhrI:C; H_PS_PSSID=60334_60376; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; arialoadData=false; delPer=0; PSINO=6; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1718955042,1719239269,1719330276,1719381882; USER_JUMP=-1; 3891209033_FRSVideoUploadTip=1; video_bubble3891209033=1; XFI=faff0730-3381-11ef-bd5f-3798017f9a75; st_key_id=17; XFCS=2E732E0EC7EEDEFB7BB3E937D65EEB3334434D417A88E64E296FB01E7559D0B8; XFT=zSXaQLLQ0VIRLPrIiv/XCgqQX7IsvAhoh5EMF9ikAbg=; wise_device=0; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1719381978; BA_HECTOR=2hagakala4258l24800084ag3ikuss1j7nbur1u; ab_sr=1.0.1_YTRlNjliODhjNTdlMzhhZWEwZTI5ODBjMGRiOTZmYjk4MmU0ZGI4Mzk4ZTFlNjAzYTU2ZDllMDk2MDljYWMwZDllYWVkOTkzNTM2ZDQwYjA5ZWYyMzdlMTI4ZjhhYjMxODEzMWQzNGEyMzMxYzExYzhjMTM4OGRhYmRkYzlkMjA2M2RiMmViMjEzZTgyMTczYzM5ODk5Y2FkNDFjNjNlNGEyY2RhZDdiZWRlMmFlOGUwOGRkYzc5NzMwNWU5NjJl; st_data=37f026a2b3c10defe4bf95deab3bbfcb865d92a8e2dc556f02a01c8cfd430ce87c0ab1d5883c11b5d0c563234e13b01de191d4196ea5f581d4399c849419c06ea5c66a2fea21e7114f3550e4a94e8eb2bce4dee2d16137a4527a10278a48b4babdfc042517022ec80fdb67c22202f2f6bd66307cee55e500313a188ec075fb407c301dd746df97ff42bbe1b379236f86; st_sign=f7a474c8; RT="z=1&dm=baidu.com&si=2deca234-e1e6-4237-b6fc-8ac4f3b2380a&ss=lxvfku8c&sl=k&tt=8md&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=5yj3&ul=7nvn"
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def get_timestamp(self) -> int:
        return int(time.time())

    def start_requests(self):
        item = TiebaComment(None, None, None, None, None, None)
        yield scrapy.Request(
            url=f"https://tieba.baidu.com/p/{self.pid}",
            callback=self.parse_detail_pn,
            cb_kwargs=dict(item=item, pn=1),
            cookies=self.cookies,
        )

    def parse_list(self, response):
        hrefs = response.xpath(r"//a[@rel='noopener']/self::*[starts-with(@href, '/p')]/@href").getall()
        hrefs = set(hrefs)
        item = TiebaComment(None, None, None, None, None, None)
        self.logger.debug(f"{hrefs=}")
        for href in hrefs:
            yield response.follow(
                href,
                callback=self.parse_detail_pn,
                cb_kwargs=dict(item=item),
            )

    def parse_detail_pn(self, response, item: TiebaComment, pn=1):
        self.logger.info(f"parse_detail_pn(): {item=}, {pn=}")
        pages = response.xpath(r"//li[@class='l_reply_num']").re(r"共<span.*>(?P<pages>\d+)</span>页")[0]
        pages = int(pages)
        self.logger.info(f"{pages=}")
        if item.pid is None:
            item.pid = re.match(r"https://tieba.baidu.com/p/(?P<post_id>\d+)", response.url).group("post_id")
        # if item.title is None:
        #     item.title = response.xpath(r"//h3/text()").get().strip()
        texts = response.xpath(r'//div[@class="d_post_content j_d_post_content "]').re(r"<div.*> +(?P<c>.+)</div>")
        times = response.xpath(r'//div[@class="post-tail-wrap"]').re(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
        floors = response.xpath(r'//div[@class="post-tail-wrap"]').re(r"(\d+)楼")
        show_nicknames = response.xpath('//a[contains(concat(" ", normalize-space(@class), " "), " p_author_name ") and contains(concat(" ", normalize-space(@class), " "), " j_user_card ")]/text()').getall()
        uids = []
        lis_uids = response.xpath("//li[@class='d_name']")
        for lis_uid in lis_uids:
            json_data = json.loads(lis_uid.attrib["data-field"])
            uids.append(json_data["user_id"])

        for text, time_ , floor, uid, show_nickname in zip(texts, times, floors, uids, show_nicknames):
            time_ = int(time.mktime(time.strptime(time_, "%Y-%m-%d %H:%M")))
            yield replace(item, text=text, time=time_, floor=floor, uid=uid, uname=show_nickname)
        yield response.follow(
            url=(
                "https://tieba.baidu.com/p/totalComment"
                f"?t={self.get_timestamp()}&tid={item.pid}&pn={pn}&see_lz=0"
            ),
            callback=self.parse_totalComment,
            cb_kwargs=dict(item=item),
        )
        if pn+1 <= pages:
            pn += 1
            yield response.follow(
                f"https://tieba.baidu.com/p/{item.pid}/?pn={pn}",
                callback=self.parse_detail_pn,
                cb_kwargs=dict(item=item, pn=pn),
                dont_filter=True,  # TODO: remove duplication filter
            )

    def parse_totalComment(self, response, item: TiebaComment):
        j = json.loads(response.text)
        comment_list = j["data"]["comment_list"]
        if comment_list == []:
            return
        content_times = [
            (comment["content"], comment["now_time"], comment["user_id"], comment["show_nickname"])
            for id_ in comment_list.values()
            for comment in id_["comment_info"]
        ]
        self.logger.debug(f"{len(content_times)=}")
        for text, time_, user_id, show_nickname in content_times:
            yield replace(item, text=text, time=time_, uid=user_id, uname=show_nickname)  # TODO: 二级评论的floor字段

        for key in comment_list:
            pages = ceil(comment_list[key]["comment_num"] / 10)
            for pn in range(2, pages+1):
                url = (
                    f"https://tieba.baidu.com/p/comment?"
                    f"tid={item.pid}&pid={key}&pn={pn}&fid={578595}&t={self.get_timestamp()}"
                )
                yield response.follow(
                    url=url,
                    callback=self.parse_comment,
                    cb_kwargs=dict(item=item),
                    dont_filter=True,  # TODO: remove duplication filter
                )

    def parse_comment(self, response, item):
        contents = response.xpath(r"//span[@class='lzl_content_main']").re(r"<span.*?> +(?P<content>.+?) +</span>")
        times = response.xpath(r"//span[@class='lzl_time']/text()").getall()
        user_ids = []
        show_nicknames = []
        li_elements = response.xpath(r"//li[contains(@class,'lzl_single_post j_lzl_s_p')]")
        for li in li_elements:
            data_field_str = li.attrib['data-field']
            data_field_dict = json.loads(data_field_str)
            spid = data_field_dict.get('spid')
            showname = data_field_dict.get('showname')
            user_ids.append(spid)
            show_nicknames.append(showname)

        for text, time_, user_id, show_nickname in zip(contents, times, user_ids, show_nicknames):
            time_ = int(time.mktime(time.strptime(time_, "%Y-%m-%d %H:%M")))
            yield replace(item, text=text, time=time_, uid=user_id, uname = show_nickname)  # TODO: 二级评论的floor字段


class TiebaListSpider(scrapy.Spider):
    name = "tiebalist"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, topic: str, start: str, end: str, cookies_text: str = None, *args, **kwargs):
        """
        start, end:
            - (2000, 5000)
        """
        super(TiebaListSpider, self).__init__(*args, **kwargs)
        self.logger.debug(f"{start=}, {end=}, {cookies_text=}")
        self.topic = topic
        self.start = int(start)
        self.end = int(end)

        # TODO: insecure data, remove this
        cookies_text = """
        XFI=343e7c10-3382-11ef-9b40-a9cc5fd15163; XFCS=3E9F076C2751C30DC50332AE8944104E7F16A02EBF81E1BD057431FF387D5DC7; XFT=dFXK3hrcb6NWmHLESz+s8J3wd+olz+jXY1zCcLFDPXY=; BIDUPSID=942C8B99F0CBA1B803D036BCDF45981A; PSTM=1692155596; BAIDUID=942C8B99F0CBA1B8DF41FAAA8136952E:SL=0:NR=10:FG=1; MCITY=-218%3A; IS_NEW_USER=4e2fab2e31d833a251600277; TIEBAUID=5c40c0e62d2efb5f13d68ffd; BDUSS=FqcnRkVHlENThwb2oyQXAzWHY2dlVpRndDenpDWDFTYkVtUGlLUUVCRFY1M3htSVFBQUFBJCQAAAAAAAAAAAEAAABJI-~ntOXD8VZpbGxhZ2VyMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANVaVWbVWlVmN3; STOKEN=fbf80c9c315856117aa2d4e1e58b9b43d866a7e8a0d8ef16b66cbefbf7411a2b; BAIDU_WISE_UID=wapp_1717132013271_460; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1715904525,1716034140,1716172038,1717132013; __bid_n=1903dd28f588208f379f79; H_WISE_SIDS=60334_60376; BAIDUID_BFESS=942C8B99F0CBA1B8DF41FAAA8136952E:SL=0:NR=10:FG=1; BDUSS_BFESS=FqcnRkVHlENThwb2oyQXAzWHY2dlVpRndDenpDWDFTYkVtUGlLUUVCRFY1M3htSVFBQUFBJCQAAAAAAAAAAAEAAABJI-~ntOXD8VZpbGxhZ2VyMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANVaVWbVWlVmN3; ZFY=Uqpg2LECCGjr16ZkdMVx41TwzMuNYGINbmInDPFwhrI:C; H_PS_PSSID=60334_60376; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; arialoadData=false; delPer=0; PSINO=6; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1718955042,1719239269,1719330276,1719381882; USER_JUMP=-1; 3891209033_FRSVideoUploadTip=1; video_bubble3891209033=1; XFI=faff0730-3381-11ef-bd5f-3798017f9a75; st_key_id=17; XFCS=2E732E0EC7EEDEFB7BB3E937D65EEB3334434D417A88E64E296FB01E7559D0B8; XFT=zSXaQLLQ0VIRLPrIiv/XCgqQX7IsvAhoh5EMF9ikAbg=; wise_device=0; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1719381978; BA_HECTOR=2hagakala4258l24800084ag3ikuss1j7nbur1u; ab_sr=1.0.1_YTRlNjliODhjNTdlMzhhZWEwZTI5ODBjMGRiOTZmYjk4MmU0ZGI4Mzk4ZTFlNjAzYTU2ZDllMDk2MDljYWMwZDllYWVkOTkzNTM2ZDQwYjA5ZWYyMzdlMTI4ZjhhYjMxODEzMWQzNGEyMzMxYzExYzhjMTM4OGRhYmRkYzlkMjA2M2RiMmViMjEzZTgyMTczYzM5ODk5Y2FkNDFjNjNlNGEyY2RhZDdiZWRlMmFlOGUwOGRkYzc5NzMwNWU5NjJl; st_data=37f026a2b3c10defe4bf95deab3bbfcb865d92a8e2dc556f02a01c8cfd430ce87c0ab1d5883c11b5d0c563234e13b01de191d4196ea5f581d4399c849419c06ea5c66a2fea21e7114f3550e4a94e8eb2bce4dee2d16137a4527a10278a48b4babdfc042517022ec80fdb67c22202f2f6bd66307cee55e500313a188ec075fb407c301dd746df97ff42bbe1b379236f86; st_sign=f7a474c8; RT="z=1&dm=baidu.com&si=2deca234-e1e6-4237-b6fc-8ac4f3b2380a&ss=lxvfku8c&sl=k&tt=8md&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=5yj3&ul=7nvn"
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def get_timestamp(self) -> int:
        return int(time.time())

    def start_requests(self):
        r = range(self.start, self.end, 50)
        self.logger.info(f"{r=}")
        for pn in r:
            self.logger.info(f"start_from_range(): {pn=}")
            yield scrapy.Request(
                url=f"https://tieba.baidu.com/f?kw={self.topic}&ie=utf-8&pn={pn}",
                callback=self.parse_list,
                cookies=self.cookies,
            )

    def parse_list(self, response):
        li_elements = response.xpath(r"//li[contains(@class,'j_thread_list clearfix thread_item_box')]")
        pids = []
        titles = []
        totals = []
        for li in li_elements:
            total = li.xpath(r'.//span[@class="threadlist_rep_num center_text"]/text()').get()

            title = li.xpath(r'.//a[@class="j_th_tit "]/text()').get()
            href = li.xpath(r'.//a[@class="j_th_tit "]/@href').get()
            if href:
                pid = re.search(r'/p/(\d+)', href)
                if pid:
                    pid = pid.group(1)
                    pids.append(pid)
            totals.append(total)
            titles.append(title)

        for pid, title, total in zip(pids, titles, totals):
            yield TiebaTotalComment(
                pid=pid,
                title=title,
                total=total,
                time=self.get_timestamp(),
            )
