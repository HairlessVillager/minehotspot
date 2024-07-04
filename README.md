README.md

# MineHotspot

## Deploy

1. Run MySQL Docker container: `docker run -d --name mysql -e MYSQL_DATABASE=MINEHOTSPOT_DB -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 mysql:latest`

## Useful Commands

- cd scrapy
- python setup.py bdist_egg
- curl http://localhost:6800/addversion.json -F project=minehotspot -F version=1.0 -F egg=@dist/minehotspot-1.0-py3.11.egg
- docker build -t minehotspot .
- docker run -d --name minehotspot -p 4200:4200 minehotspot
