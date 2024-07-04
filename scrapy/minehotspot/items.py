# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass


@dataclass
class TiebaComment:
    pid: int
    title: str
    text: str
    floor: int
    time: str  # format: "%Y-%m-%d %H:%M", e.g. "2024-05-15 10:42"
    uid: str  # TODO: unknown format


@dataclass
class TiebaTotalComment:
    pid: str
    title: str
    time: str  # format: "%Y-%m-%d %H:%M", e.g. "2024-05-15 10:42"
    total: int
@dataclass
class ZhihuQuestion:
    id: int          # 问题id
    title: str       # 问题标题
    des: str         # 问题描述
@dataclass
class ZhihuAnswer:
    id: int              # 用户id
    user: str            # 用户名
    reply_text: str      # 回答文本
    praise_num: int      # 点赞数
    comment_num: int     # 评论数