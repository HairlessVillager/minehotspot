import re
import json
from math import ceil
import time

import scrapy

from ..items import TiebaTotalComment,TiebaComment



class TiebaPostSpider(scrapy.Spider):
    name = "tiebapost"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, pid: str, cookies_text: str = None):
        """
        pid:
            no: /p/8985907273
            yes: 8985907273
        """
        self.logger.debug(f"{pid=}, {cookies_text=}")
        self.pid = pid

        # TODO: insecure data, remove this

        #  处理cookies以字典的形式处理
        cookies_text = """
            BIDUPSID=CDA1F3C01124B13535263674E29C9852; PSTM=1699769466; BAIDUID=993F177B1AC04E12B8B89A7A8FF54691:FG=1; H_WISE_SIDS=39996_40041; H_WISE_SIDS_BFESS=39996_40041; BAIDUID_BFESS=993F177B1AC04E12B8B89A7A8FF54691:FG=1; __bid_n=18e84dea3d64384ab8121f; BAIDU_WISE_UID=wapp_1716306674304_754; BDUSS=F5emp-T3pYb2RrbGdCNE5wZ0luVld5dGZTblMySTFHVn42Sm54b296UVJzSUJtSVFBQUFBJCQAAAAAAQAAAAEAAAAADjRry9XDzm1hcnJpYWdlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEjWWYRI1lmdD; BDUSS_BFESS=F5emp-T3pYb2RrbGdCNE5wZ0luVld5dGZTblMySTFHVn42Sm54b296UVJzSUJtSVFBQUFBJCQAAAAAAQAAAAEAAAAADjRry9XDzm1hcnJpYWdlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEjWWYRI1lmdD; STOKEN=9b34ff73712e36ad26604dd3351b016ab7e7b7872a4bc1fe9c49bb90d28daaff; ZFY=Nqggs0oYBFbs7lwmHXMrhr8sDBquyaDBSKKinlvwh4Q:C; arialoadData=false; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1719797472; BDRCVFR[-BxzrOzUsTb]=mk3SLVN4HKm; H_PS_PSSID=60340; USER_JUMP=-1; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1719625067,1719794510,1719796412,1719802981; 6093540864_FRSVideoUploadTip=1; video_bubble6093540864=1; st_key_id=17; XFT=JCMmpM7sgAn+Ehr6Y0qZanakus0enEl18LXweFxp4rA=; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1719804250; XFI=61f296c0-3759-11ef-9ad1-ff11484a5e6b; BA_HECTOR=2g8l202ka5800ga401208k0g01cti11j848ar1v; st_data=9a7aa8718c2a6fcccbfef9c7fd901886a78884d92f9f54eb3943f9613e1c93266cf61fa6e1c6c0cd16d8dcee8ad03e42484020b4925be310ebb769bcce99c2e28df2cf1fde08400c96f8a5fbaa9504ed1db79c889be1df07364392bc24850d0a21d330ed9265546388cd359ca5eb84f0ed19edcf49dcc111176a5ed0f0e7d14d5be023eb0a0e2b87ee7194bf24275f0dc667a3b999e1e0c45ae38d82daeda505; st_sign=5c3f6d5c; XFCS=19069C65BA5C008AE0D11764D35A446B44DDBAAF52DEF45C6A7854BF8B173CED; ab_sr=1.0.1_YWU4Yjg3NTI3MTQxNDBiZGQzMzljMTEyOWQxZDE4ZDEyZmRiMWE2YTRiNmFiZmUwYjg3ZWY0OThkOWVkNGUyMjM3Y2I5MGExNDEyYThmODhhNDdiMjFmNjk3ZGM2NTkzNTQ5ZTA1OThlOGVjZGZmYTQ0YWUxMGEzMjc5NDgxMjI2OTAzNDExMDk0N2I2MDUyODJhMmU3ZTQxY2FjMWJmN2NhNjM0OTBlZTlhZTBkODIxMzYxMTJmZTY4NGVmYTZiOWFmMjgxNTU0YzgxMjMyNmQ2NGNiNzFlMjhlNTYzMmQ=; RT="z=1&dm=baidu.com&si=d7cf139a-b518-4d9a-bbd7-13f780cdccfa&ss=ly28omhk&sl=2l&tt=3aq3&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=7g0h5&nu=kwb28ey&cl=5yjmh&ul=7gc7n"
        """
        self.cookies = {}
        for item in cookies_text.strip().split(";"):
            k, _, v = item.partition("=")
            k = k.strip()
            v = v.strip()
            self.cookies[k] = v
        self.logger.debug(f"{self.cookies=}")

    def get_timestamp(self) -> int:
        # 获取时间戳
        return int(time.time())

    # 开始爬虫的函数
    def start_requests(self):
        item = TiebaComment()
        yield scrapy.Request(
            url=f"https://tieba.baidu.com/p/{self.pid}",
            callback=self.parse_detail_pn,
            cb_kwargs=dict(item=item, pn=1),
            cookies=self.cookies,
        )

    # 获取爬虫urls
    def parse_list(self, response):
        except_hrefs = {
            # "/p/8251345629",  # 【2023版吧务工作楼】警告//咨询//举报//建议处
            # "/p/7527868317",  # 【Galgame吧】吧规与导航
        }
        hrefs = response.xpath(r"//a[@rel='noopener']/self::*[starts-with(@href, '/p')]/@href").getall()
        hrefs = set(hrefs)
        item = TiebaComment()
        self.logger.debug(f"{hrefs=}")
        for href in hrefs - except_hrefs:
            yield response.follow(
                href,
                callback=self.parse_detail_pn,
                cb_kwargs=dict(item=item),
            )

    #解析页面
    def parse_detail_pn(self, response, item: TiebaComment, pn=1):
        self.logger.info(f"parse_detail_pn(): {item=}, {pn=}")
        pages = response.xpath(r"//li[@class='l_reply_num']").re(r"共<span.*>(?P<pages>\d+)</span>页")[0]
        pages = int(pages)
        self.logger.info(f"{pages=}")
        if "pid" not in item:
            #从url中捕捉pid
            item["pid"] = re.match(r"https://tieba.baidu.com/p/(?P<post_id>\d+)", response.url).group("post_id")
        if "title" not in item:
            #从response中获取title
            item["title"] = response.xpath(r"//h3/text()").get().strip()
        #获取帖子文本 //*[@id="post_content_150141271183"]
        texts = response.xpath(r'//div[@class="d_post_content j_d_post_content "]').re(r"<div.*> +(?P<c>.+)</div>")
        #获取帖子回复时间
        times = response.xpath(r'//div[@class="post-tail-wrap"]').re(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

        # 似乎这部分代码是多余的

        # for text, time_ in zip(texts, times):
        #     copy = item.copy()
        #     copy["text"] = text
        #     copy["time"] = int(time.mktime(time.strptime(time_, "%Y-%m-%d %H:%M")))
        #     print(copy)
        #     yield copy
        yield response.follow(
            url=f"https://tieba.baidu.com/p/totalComment?t={self.get_timestamp()}&tid={item['pid']}&pn={pn}&see_lz=0",
            callback=self.parse_totalComment,
            cb_kwargs=dict(item=item),
        )

        if pn+1 <= pages:
            pn += 1
            yield response.follow(
                f"https://tieba.baidu.com/p/{item['pid']}/?pn={pn}",
                callback=self.parse_detail_pn,
                cb_kwargs=dict(item=item, pn=pn),
                dont_filter=True,  # TODO: remove duplication filter
            )

    def parse_totalComment(self, response, item: TiebaComment):
        print("执行了parse_totalComment")
        j = json.loads(response.text)
        comment_list = j["data"]["comment_list"]
        if comment_list == []:
            return
        content_times = [
            (comment["content"], comment["now_time"],comment["user_id"],comment["show_nickname"])
            for id_ in comment_list.values()
            for comment in id_["comment_info"]
        ]
        self.logger.debug(f"{len(content_times)=}")
        for text, time_,user_id,show_nickname in content_times:
            copy = item.copy()
            copy["text"] = text
            copy["time"] = time_
            copy["uid"]=f"uid:{user_id}  昵称:{show_nickname}"
            yield copy

        ## 猜测二级评论10条一页
        for key in comment_list:
            pages = ceil(comment_list[key]["comment_num"] / 10)
            for pn in range(2, pages+1):
                url = (
                    f"https://tieba.baidu.com/p/comment?"
                    f"tid={item['pid']}&pid={key}&pn={pn}&fid={578595}&t={self.get_timestamp()}"
                )
                yield response.follow(
                    url=url,
                    callback=self.parse_comment,
                    cb_kwargs=dict(item=item),
                    dont_filter=True,  # TODO: remove duplication filter
                )

    def parse_comment(self, response, item):
        #print("执行了parse_comment")
        contents = response.xpath(r"//span[@class='lzl_content_main']").re(r"<span.*?> +(?P<content>.+?) +</span>")
        times = response.xpath(r"//span[@class='lzl_time']/text()").getall()
        user_ids=[]
        show_nicknames=[]
        #print("contents长度:"+str(len(contents))+"  times长度"+str(len(times))) ## 调试语句
        li_elements = response.xpath(r"//li[contains(@class,'lzl_single_post j_lzl_s_p')]")
        #print("li_elements长度:"+str(len(li_elements)))
        for li in li_elements:
            # 提取data-field属性的值
            data_field_str = li.attrib['data-field']
            # 将JSON格式的字符串转换为Python字典
            data_field_dict = json.loads(data_field_str)
            # 提取spid和showname
            spid = data_field_dict.get('spid')
            showname = data_field_dict.get('showname')
            user_ids.append(spid)
            show_nicknames.append(showname)

        for text, time_, user_id, show_nickname in zip(contents, times, user_ids, show_nicknames):
            copy = item.copy()
            copy["text"] = text
            copy["time"] = int(time.mktime(time.strptime(time_, "%Y-%m-%d %H:%M")))
            copy["uid"] = f"uid:{user_id}  昵称:{show_nickname}"
            print(copy)
            #yield copy


class TiebaListSpider(scrapy.Spider):
    name = "tiebalist"
    allowed_domains = ["tieba.baidu.com"]

    def __init__(self, start: str, end: str, cookies_text: str = None):
        """
        start, end:
            - (2000, 5000)
        """
        self.logger.debug(f"{start=}, {end=}, {cookies_text=}")
        self.start = int(start)
        self.end = int(end)

        # TODO: insecure data, remove this
        cookies_text = """
        BIDUPSID=CDA1F3C01124B13535263674E29C9852; PSTM=1699769466; BAIDUID=993F177B1AC04E12B8B89A7A8FF54691:FG=1; H_WISE_SIDS=39996_40041; H_WISE_SIDS_BFESS=39996_40041; BAIDUID_BFESS=993F177B1AC04E12B8B89A7A8FF54691:FG=1; __bid_n=18e84dea3d64384ab8121f; BAIDU_WISE_UID=wapp_1716306674304_754; BDUSS=F5emp-T3pYb2RrbGdCNE5wZ0luVld5dGZTblMySTFHVn42Sm54b296UVJzSUJtSVFBQUFBJCQAAAAAAQAAAAEAAAAADjRry9XDzm1hcnJpYWdlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEjWWYRI1lmdD; BDUSS_BFESS=F5emp-T3pYb2RrbGdCNE5wZ0luVld5dGZTblMySTFHVn42Sm54b296UVJzSUJtSVFBQUFBJCQAAAAAAQAAAAEAAAAADjRry9XDzm1hcnJpYWdlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEjWWYRI1lmdD; STOKEN=9b34ff73712e36ad26604dd3351b016ab7e7b7872a4bc1fe9c49bb90d28daaff; ZFY=Nqggs0oYBFbs7lwmHXMrhr8sDBquyaDBSKKinlvwh4Q:C; arialoadData=false; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1719797472; BDRCVFR[-BxzrOzUsTb]=mk3SLVN4HKm; H_PS_PSSID=60340; USER_JUMP=-1; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1719625067,1719794510,1719796412,1719802981; 6093540864_FRSVideoUploadTip=1; video_bubble6093540864=1; st_key_id=17; XFT=JCMmpM7sgAn+Ehr6Y0qZanakus0enEl18LXweFxp4rA=; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1719804250; XFI=61f296c0-3759-11ef-9ad1-ff11484a5e6b; BA_HECTOR=2g8l202ka5800ga401208k0g01cti11j848ar1v; st_data=9a7aa8718c2a6fcccbfef9c7fd901886a78884d92f9f54eb3943f9613e1c93266cf61fa6e1c6c0cd16d8dcee8ad03e42484020b4925be310ebb769bcce99c2e28df2cf1fde08400c96f8a5fbaa9504ed1db79c889be1df07364392bc24850d0a21d330ed9265546388cd359ca5eb84f0ed19edcf49dcc111176a5ed0f0e7d14d5be023eb0a0e2b87ee7194bf24275f0dc667a3b999e1e0c45ae38d82daeda505; st_sign=5c3f6d5c; XFCS=19069C65BA5C008AE0D11764D35A446B44DDBAAF52DEF45C6A7854BF8B173CED; ab_sr=1.0.1_YWU4Yjg3NTI3MTQxNDBiZGQzMzljMTEyOWQxZDE4ZDEyZmRiMWE2YTRiNmFiZmUwYjg3ZWY0OThkOWVkNGUyMjM3Y2I5MGExNDEyYThmODhhNDdiMjFmNjk3ZGM2NTkzNTQ5ZTA1OThlOGVjZGZmYTQ0YWUxMGEzMjc5NDgxMjI2OTAzNDExMDk0N2I2MDUyODJhMmU3ZTQxY2FjMWJmN2NhNjM0OTBlZTlhZTBkODIxMzYxMTJmZTY4NGVmYTZiOWFmMjgxNTU0YzgxMjMyNmQ2NGNiNzFlMjhlNTYzMmQ=; RT="z=1&dm=baidu.com&si=d7cf139a-b518-4d9a-bbd7-13f780cdccfa&ss=ly28omhk&sl=2l&tt=3aq3&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=7g0h5&nu=kwb28ey&cl=5yjmh&ul=7gc7n"
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
                url=f"https://tieba.baidu.com/f?kw=galgame&ie=utf-8&pn={pn}",
                callback=self.parse_list,
                cookies=self.cookies,
            )

    def parse_list(self, response):
        li_elements = response.xpath(r"//li[contains(@class,'j_thread_list clearfix thread_item_box')]")
        print("数量："+str(len(li_elements)))
        pids=[]
        titles = []
        totals = []
        for li in li_elements:
            total = li.xpath(r'.//span[@class="threadlist_rep_num center_text"]/text()').get()

            title = li.xpath(r'.//a[@class="j_th_tit "]/text()').get()
            print(f"空   {title}")
            href = li.xpath(r'.//a[@class="j_th_tit "]/@href').get()
            if href:
                # 使用正则表达式提取href中第二个/后面的数字部分
                pid = re.search(r'/p/(\d+)', href)  # 假设/p/后面紧跟着数字
                if pid:
                    pid= pid.group(1)  # 提取第一个括号内的内容
                    pids.append(pid)  # 添加到post_ids列表中
                    print(f"total:{total} title:{title} pid:{pid}")
            totals.append(total)
            titles.append(title)


        for pid, title, total in zip(pids, titles, totals):
            yield TiebaTotalComment(
                pid=pid,
                title=title,
                total=total,
                time=self.get_timestamp(),
            )
