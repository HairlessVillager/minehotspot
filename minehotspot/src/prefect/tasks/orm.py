from os import getenv
from datetime import datetime

from prefect import task, get_run_logger
from sqlalchemy import create_engine, select

from ..models.tieba import TiebaBase, TiebaPost, TiebaComment, TiebaTotal


def get_engine():
    engine = create_engine(
        getenv("DATABASE_CONNECTION_URL"),
        echo=True,
    )  # echo will be duplicated with logs
    base = TiebaBase
    base.metadata.create_all(engine)  # idempotent
    return engine


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
    logger.info(f"received {len(rows)} rows")
    logger.debug(f"{rows[:10]=}")
    for row in rows:
        # pid, title, topic, time, total
        post = session.get(TiebaPost, row["pid"])
        if post is None:
            post = TiebaPost(
                pid=row["pid"],
                topic=row["topic"],
                title=row["title"],
            )
        if revive:
            post.died = False
        session.merge(post)
        total = TiebaTotal(
            pid=row["pid"],
            total=row["total"],
            time=datetime.fromtimestamp(int(row["time"])),
        )
        session.add(total)
    session.commit()
    logger.info("commit successfully")


@task
def store_tieba_comment(session, rows: list[dict]):
    """Store the Comment rows into database.

    Parameter
    ---------
    rows: list[dict]
        The comment data rows. See items.TiebaComment for details.
    """
    logger = get_run_logger()
    logger.info(f"received {len(rows)} rows")
    logger.debug(f"{rows[:10]=}")
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
    session.commit()
    logger.info("commit successfully")


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
    logger.info(f"received {len(totals)} TiebaTotal data")
    logger.debug(f"{totals[:10]=}")
    lifelines = {}
    for total in totals:
        lifeline = lifelines.get(total.pid, [])
        lifeline.append((total.time, total.total))
        lifelines[total.pid] = lifeline
    for pid in lifelines:
        lifelines[pid].sort(key=lambda x: x[0])
    logger.info(f"return {len(lifelines)=} lifelines")
    logger.debug(f"{list(lifelines.items())[:10]=}")
    return lifelines
