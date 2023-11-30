#################################################################
# cd ./backend_service
# docker build . -t ashishgoyal2310/backend-image:latest
# docker run --name backend_cont -d -p 30080:5000 ashishgoyal2310/backend-image:latest
# docker run --name redis_cont -d redis
# docker run --name celery_cont --link redis_cont:redis_cont -e REDIS_HOST="redis_cont" --entrypoint "celery" ashishgoyal2310/backend-image:latest -A main worker --concurrency 5 --loglevel INFO
#
################################################################

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim

# RUN apt-get update
# RUN apt-get install -y python3-dev default-libmysqlclient-dev
# RUN apt-get install -y build-essential
# RUN apt-get install -y vim

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
WORKDIR /app
COPY requirements.txt /app

RUN python -m pip install -r requirements.txt
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

ENV DEBUG True

COPY . /app

ENTRYPOINT [ "python", "main.py" ]
# CMD python manage.py migrate; python manage.py runserver 0.0.0.0:8000
