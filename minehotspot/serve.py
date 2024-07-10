import os
import subprocess

import requests

from src.prefect.flows.collect_tieba import collect_tieba


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
    # FIXME: remove comment in production environment
    # NOTE: The bash is not work in Windows.
    # - in Windows, comment this and run `python setup.py bdist_egg` manually.
    # - in Linux, no comment
    # -----------
    # bdist_egg()
    deploy_spiders()
    collect_tieba("galgame")
