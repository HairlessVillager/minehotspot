import os
import time
import subprocess

import requests
from prefect.variables import Variable

from src.prefect.flows.collect_tieba import collect_tieba


def check_prefect(seconds):
    print(f"sleep {seconds}s for prefect server start...")
    time.sleep(seconds)
    print("wake up")

    try:
        resp = requests.get(os.getenv("PREFECT_API_URL"))
    except requests.exceptions.ConnectionError as e:
        print(f"{e!r}")
        print("check if PREFECT_API_HOST=='0.0.0.0'")
        exit(-1)


def bdist_egg():
    # python src/scrapy/setup.py bdist_egg
    result = subprocess.run("bash bdist_egg.sh".split(), capture_output=True, text=True)
    print("result.stdout:")
    print(result.stdout)
    print("result.stderr:")
    print(result.stderr)
    print(f"{result.returncode=}")

    if result.returncode != 0:
        exit(result.returncode)


def deploy_spiders():
    # curl http://scrapyd:6800/addversion.json -F project=minehotspot -F version=1.0 -F egg=@dist/minehotspot-1.0-py3.11.egg
    url = f'{os.getenv("SCRAPYD_URL", "http://localhost:6800")}/addversion.json'
    project_name = "minehotspot"
    version = "1.0"
    egg_file_path = "src/scrapy/dist/minehotspot-1.0-py3.11.egg"

    with open(egg_file_path, "rb") as f:
        egg_data = f.read()

    files = {
        "egg": ("minehotspot-1.0-py3.11.egg", egg_data, "application/octet-stream"),
    }
    data = {
        "project": project_name,
        "version": version,
    }

    response = requests.post(url, files=files, data=data)

    print(f"{response.text=}")

    if response.status_code != 200:
        print(f"{response.status_code=}")
        exit(-1)


if __name__ == "__main__":
    seconds = int(os.getenv("WAIT_PREFECT_SECONDS"))
    check_prefect(seconds)

    Variable.set(name="cookies_text", value=os.getenv("COOKIES_TEXT"))
    # NOTE: The bash is not work in Windows.
    # - in Windows, comment this and run `python setup.py bdist_egg` manually.
    # -----------
    if int(os.getenv("DOCKER")):
        bdist_egg()
    else:
        pass  # please run `python setup.py bdist_egg` manually
    deploy_spiders()
    collect_tieba("galgame")
