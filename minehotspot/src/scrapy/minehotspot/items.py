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
@dataclass
class ZhihuQuestion:
    id:str                # 问题id
    title:str             # 问题标题
    des:str               # 问题描述
@dataclass
class ZhihuAnswer:
    id:int                  # 用户id
    user:str                # 用户名
    reply_text:str          # 回答文本
    praise_num:int          # 点赞数
    comment_num:int         # 评论数
@dataclass
class ZhihuPin:
    id:int                # 用户id
    user:str              # 用户名
    title:str             #想法标题
    content:str           #想法内容
    like_num:int          #喜欢数
    comment_num:int       #评论数