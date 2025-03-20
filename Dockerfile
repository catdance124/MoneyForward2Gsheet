FROM python:3.8.8-buster

WORKDIR /opt/app

# chromium install
RUN apt-get update -y && apt-get install -y \
    chromium chromium-driver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver
ENV PATH=$PATH:/usr/bin


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

# install virtual display
RUN apt-get install xvfb -y

# same user inside and outside
ARG UID
ARG GID
ARG UNAME

ENV UID ${UID}
ENV GID ${GID}
ENV UNAME ${UNAME}

RUN groupadd -g ${GID} ${UNAME}
RUN useradd -u ${UID} -g ${UNAME} -m ${UNAME}
