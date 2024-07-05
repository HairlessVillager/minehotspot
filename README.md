README.md

# MineHotspot

## Quick Start

1. Install Docker Desktop
2. Run it
3. git clone xxx
4. cd minehotspot
5. docker-compose build
6. docker-compose up

## Useful Commands

- cd scrapy
- python setup.py bdist_egg
- curl http://localhost:6800/addversion.json -F project=minehotspot -F version=1.0 -F egg=@dist/minehotspot-1.0-py3.11.egg
- docker build -t minehotspot .
- docker run -d --name minehotspot -p 4200:4200 minehotspot
