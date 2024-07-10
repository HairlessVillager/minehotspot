from random import seed, randint
from datetime import datetime, timedelta
from os import getenv

from prefect import (
    flow,
    task,
    get_run_logger,
)
from prefect.variables import Variable
from sqlalchemy.orm import Session

from ..tasks.scrapyd import (
    schedule_crawl_job,
    get_job_result,
)
from ..tasks.orm import (
    get_engine,
    query_lifelines,
    store_tieba_total,
    store_tieba_comment,
)
from ..models.tieba import (
    TiebaPost,
    TiebaComment,
    TiebaTotal,
)


def is_end_of_line(lifeline: list[tuple[int, int]], now: datetime = None) -> bool:
    """Check if the post is at the end of line (EOL) by the lifeline.

    Parameter
    ---------
    lifeline: list[tuple[int, int]]
        A list of (timestamp, total), ordered by timestamp on ascending order.
    now: datetime.datetime = None
        The timestamp that check based on.
        Leave None to automatically use the current time.

    Return
    ------
    bool:
        True if the post is EOL.
    """
    logger = get_run_logger()
    if now is None:
        now = datetime.now()
    last_comment_time = datetime.fromtimestamp(lifeline[-1][1])
    if now - last_comment_time > timedelta(days=1):  # FIXME: bad implementation
        return True
    else:
        return False


@flow
def collect_tieba(topic: str, page_range: tuple = (0, 200)):
    """Collect data from tieba.baidu.com.

    ParameteTiebaBaser
    ---------
    topic: str
        The tieba's name, e.g. "galgame", "孙笑川".
    page_range: tuple = (0, 200)
        The page number range of posts, format: (start, end).
        The page number could be found on the bottom.
    """
    use_fake_data = bool(int(getenv("USE_FAKE_DATA")))

    logger = get_run_logger()
    start, end = page_range
    cookies_text = Variable.get("cookies_text").value
    if cookies_text is None:
        raise ValueError(
            "cookies_text is empty, set it on Prefect WebUI (may http://localhost:4200/)"
        )
    list_jobid = schedule_crawl_job(
        "tiebalist" if not use_fake_data else "tiebalist_fake",
        {
            "topic": topic,
            "start": start,
            "end": end,
            "cookies_text": cookies_text,
        },
    )
    total = get_job_result(list_jobid, interval=3, retry=40)

    engine = get_engine()
    with Session(engine) as session:
        store_tieba_total(session, total, revive=False)

        # collect end-of-life posts
        lifelines = query_lifelines(session, False)
        eol_pids = (
            [pid for pid, lifeline in lifelines.items() if is_end_of_line(lifeline)]
            if not use_fake_data
            else [8985907273]
        )
        logger.debug(f"{eol_pids=}")
        post_jobids = []
        for pid in eol_pids:
            jobid = schedule_crawl_job(
                "tiebapost" if not use_fake_data else "tiebapost_fake",
                {"pid": pid, "cookies_text": cookies_text},
            )
            post_jobids.append(jobid)
        for jobid in post_jobids:
            comment = get_job_result(jobid, interval=10, retry=60)
            store_tieba_comment(session, comment, kill=True)
