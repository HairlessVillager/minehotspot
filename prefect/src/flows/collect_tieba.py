from random import seed, randint

from prefect import (
    flow,
    task,
    get_run_logger,
)
from sqlalchemy.orm import Session

from ..tasks.scrapyd import (
    schedule_crawl_job,
    get_job_result,
)
from ..tasks.orm import (
    engine,
    query_lifelines,
    store_tieba_total,
    store_tieba_comment,
)
from ..models.tieba import (
    TiebaPost,
    TiebaComment,
    TiebaTotal,
)


def is_end_of_line(lifeline: list[tuple[int, int]], now: int = None) -> bool:
    """Check if the post is at the end of line (EOL) by the lifeline.

    Parameter
    ---------
    lifeline: list[tuple[int, int]]
        A list of (timestamp, total), ordered by timestamp on ascending order.
    now: int = None
        The timestamp that check based on.
        Leave None to automatically use the current time.

    Return
    ------
    bool:
        True if the post is EOL.
    """
    logger = get_run_logger()
    return False  # FIXME: test code, remove this


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

    logger = get_run_logger()
    start, end = page_range
    list_jobid = schedule_crawl_job("tiebalist_fake", {"topic": topic, "start": start, "end": end})
    total = get_job_result(list_jobid)

    with Session(engine) as session:
        store_tieba_total(session, total, revive=False)

        # collect end-of-life posts
        lifelines = query_lifelines(session, False)
        eol_pids = [pid for pid, lifeline in lifelines.items() if is_end_of_line(lifeline)]
        eol_pids = [8985907273]  # FIXME: test code, remove this
        logger.debug(f"{eol_pids=}")
        post_jobids = []
        for pid in eol_pids:
            jobid = schedule_crawl_job("tiebapost_fake", {"pid": pid})
            post_jobids.append(jobid)
        for jobid in post_jobids:
            comment = get_job_result(jobid)
            store_tieba_comment(session, comment)
