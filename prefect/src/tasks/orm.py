from functools import wraps
from datetime import datetime

from prefect import task, get_run_logger
from sqlalchemy import create_engine, select

from ..models.tieba import TiebaBase, TiebaPost, TiebaComment, TiebaTotal


engine = create_engine("sqlite:///db.sqlite3", echo=False)  # echo will be duplicated with logs
base = TiebaBase
base.metadata.create_all(engine)  # idempotent


def get_or_create_post(session, row):
    post = session.get(TiebaPost, row["pid"])
    if post is None:
        post = TiebaPost(
            pid=row["pid"],
            topic=row["topic"],
            title=row["title"],
        )
    return post


def info_session(session, *, only_new=False):
    logger = get_run_logger()
    logger.info(f"{len(session.new)} entities will be added")
    if not only_new:
        logger.info(f"{len(session.dirty)} entities will be modified")
        logger.info(f"{len(session.deleted)} entities will be deleted")


@task
def store_tieba_total(session, rows: list[dict], revive: bool):
    """Store the Total rows into database.

    Parameter
    ---------
    rows: list[dict]
        The Total data rows. See items.TiebaTotalComment for details.
    revive: bool
        If True, the relatived posts will revive (set died=False).
    """
    logger = get_run_logger()
    for row in rows:
        # pid, title, topic, time, total
        logger.debug(f"{row=!r}")
        post = get_or_create_post(session, row)
        if revive:
            post.died = False
        session.merge(post)
        logger.debug(f"merged {post!r}")
        total = TiebaTotal(
            pid=row["pid"],
            total=row["total"],
            time=datetime.fromtimestamp(int(row["time"])),
        )
        session.add(total)
        logger.debug(f"added {total!r}")
    info_session(session, only_new=True)
    session.commit()


@task
def store_tieba_comment(session, rows: list[dict]):
    """Store the Comment rows into database.

    Parameter
    ---------
    rows: list[dict]
        The comment data rows. See items.TiebaComment for details.
    """
    logger = get_run_logger()
    for row in rows:
        # pid, text, floor, time, uid
        assert session.get(TiebaPost, row["pid"])
        comment = TiebaComment(
            pid=row["pid"],
            uid=row["uid"],
            uname=row["uname"],
            text=row["text"],
            floor=row["floor"],
            time=datetime.fromtimestamp(int(row["time"])),
        )
        session.add(comment)
        logger.debug(f"added {comment!r}")
    info_session(session, only_new=True)
    session.commit()


@task
def query_lifelines(session, include_died: bool) -> dict[int, tuple[int, int]]:
    """Query all total rows from database.

    Parameter
    ---------
    include_died: bool
        If false, the died post data will not be included.

    Return
    ------
    dict[int, tuple[int, int]]
        A mapper which map pid to lifeline. See is_end_of_line() for details.
    """
    logger = get_run_logger()
    stmt = select(TiebaTotal).join(TiebaTotal.post)
    if not include_died:
        stmt = stmt.filter(TiebaPost.died == False)  # noqa
    totals = session.scalars(stmt).all()
    logger.debug(f"{len(totals)=}")
    lifelines = {}
    for total in totals:
        lifeline = lifelines.get(total.pid, [])
        lifeline.append((total.time, total.total))
        lifelines[total.pid] = lifeline
    for pid in lifelines:
        lifelines[pid].sort(key=lambda x: x[0])
    logger.debug(f"{lifelines=}")
    logger.debug(f"{len(lifelines[8985907273])=}")
    return lifelines
