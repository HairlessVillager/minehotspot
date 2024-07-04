cd $DOCKER_HOME/scrapy && scrapyd &
prefect server start &
cd $DOCKER_HOME/prefect && python run.py
