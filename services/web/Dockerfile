# pull official base image
FROM python:3.13-slim-bookworm

# set work directory
WORKDIR /usr/local/bin

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system depenedencies
RUN apt update && apt install -y netcat-traditional dos2unix

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/local/bin/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/local/bin/

# Make sure /usr/local/bin/entrypoint.sh is executable and dos2unix
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh

ENV FLASK_APP=project/__init__.py

# run entrypoint.sh
ENV FLASK_APP=project.wsgi
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
