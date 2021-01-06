FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY ./app /app
RUN apt-get update && apt-get install -y pngquant
RUN pip3 install -r /app/requirements.txt
WORKDIR /app
