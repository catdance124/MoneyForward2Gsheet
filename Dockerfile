FROM python:3.8.8-buster AS base

WORKDIR /opt/app

RUN apt update && apt install -y \
  wait-for-it

# pip install
RUN pip install --upgrade pip
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# japanese langage pack
ENV LANGUAGE ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
RUN apt-get install -y --no-install-recommends locales && \
    locale-gen ja_JP.UTF-8 && \
    apt-get install -y --no-install-recommends fonts-ipafont
ENV TZ Asia/Tokyo


FROM base AS chrome_xvfb

# chrome install
RUN wget --no-check-certificate https://dl-ssl.google.com/linux/linux_signing_key.pub
RUN apt-key add linux_signing_key.pub
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main " >> /etc/apt/sources.list'
RUN apt-get update -y
RUN apt-get install google-chrome-stable -y

# install virtual display
RUN apt-get install xvfb -y