import json
import time

import requests
from prefect import task, get_run_logger


@task
def schedule_crawl_job(spider: str, spider_kwargs: dict):
    """Schedule a crawl job on scrapyd.

    Parameter
    ---------
    spider: str
        The name of spider.
    spider_kwargs: dict
        The arguments of spider.

    Return
    ------
    str:
        The jobid.

    See
    ---
        https://scrapyd.readthedocs.io/en/latest/api.html#schedule-json
    """
    logger = get_run_logger()
    logger.info(f"run spider '{spider}' with args {spider_kwargs}")
    try:
        response = requests.post(
            "http://localhost:6800/schedule.json",
            params={"project": "minehotspot", "spider": spider} | spider_kwargs
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(
            "connection failed, try to start up "
            "scrapyd or check scrapyd status"
        )
        raise e
    assert response.status_code == 200
    result = json.loads(response.text)
    if result["status"] != "ok":
        msg = f"crawl job schedule failed with status={result['status']}"
        logger.error(msg)
        raise ValueError(msg)
    logger.info(f"return with jobid={result['jobid']}")
    return result["jobid"]


def _try_get_job_result(jobid: str) -> list:
    logger = get_run_logger()
    jobs_response = requests.get("http://localhost:6800/listjobs.json?project=minehotspot")
    assert jobs_response.status_code == 200
    jobs = json.loads(jobs_response.text)
    for finished_job in jobs["finished"]:
        if jobid == finished_job["id"]:
            logger.debug(f"job status: {finished_job}")
            items_url = finished_job["items_url"]
            items_response = requests.get(f"http://localhost:6800{items_url}")
            assert items_response.status_code == 200
            items_response.encoding = items_response.apparent_encoding
            lines = items_response.text.splitlines()
            logger.debug(f"response's {lines[:10]=!r}")
            return [json.loads(line) for line in lines]
    return None


@task
def get_job_result(jobid: str, interval: int = 3, retry: int = 10):
    """Get the crawl job result on scrapyd.

    Parameter
    ---------
    jobid: str
        The jobid.
    interval: int = 3
        The seconds the task will sleep when result not ready.
    retry: int = 10
        The query times.

    Return
    ------
    list[dict]:
        The result.
    """
    logger = get_run_logger()
    cnt = 0
    while True:
        result = _try_get_job_result(jobid=jobid)
        if result is not None:
            logger.info(f"result ready with {len(result)} lines")
            return result
        else:
            cnt += 1
            if cnt > retry:
                msg = f"reach max retry times (={retry}), but the result is still not ready"
                logger.error(msg)
                raise ValueError(msg)
            logger.info(f"result not ready, wait {interval} seconds ({cnt}/{retry})...")
            time.sleep(interval)
