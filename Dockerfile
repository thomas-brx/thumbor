ARG PYTHON_VERSION=3.9
FROM python:${PYTHON_VERSION}-bullseye AS builder-image

ARG THUMBOR_VERSION=7.4.6

# base OS packages
RUN  \
    awk '$1 ~ "^deb" { $3 = $3 "-backports"; print; exit }' /etc/apt/sources.list > /etc/apt/sources.list.d/backports.list && \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y autoremove && \
    apt-get install -y -q \
        git \
        curl \
        libjpeg-turbo-progs \
        graphicsmagick \
        libgraphicsmagick++3 \
        libgraphicsmagick++1-dev \
        libgraphicsmagick-q16-3 \
        zlib1g-dev \
        libboost-python-dev \
        libmemcached-dev \
        libcurl4-gnutls-dev \
        gnutls-dev \
        gifsicle \
        build-essential && \
    apt-get clean

RUN python3 -m venv /home/thumbor/venv
ENV PATH="/home/thumbor/venv/bin:$PATH"

ENV HOME /app
ENV SHELL bash
ENV WORKON_HOME /app
WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir wheel && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir thumbor==${THUMBOR_VERSION}


COPY patches/ .
RUN cd /home/thumbor/venv/lib/python3.9/site-packages; for patch in /app/*.diff; do patch -p1 < "$patch"; done

FROM python:${PYTHON_VERSION}-slim-bullseye AS runner-image

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
        gifsicle \
        libcairo2 \
        libcurl4-gnutls-dev \
        libjpeg-turbo-progs && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home thumbor
COPY --from=builder-image /home/thumbor/venv /home/thumbor/venv

USER thumbor

EXPOSE 8888

ENV PYTHONUNBUFFERED=1

ENV VIRTUAL_ENV=/home/thumbor/venv
ENV PATH="/home/thumbor/venv/bin:$PATH"
ENV PYTHONPATH="/home/thumbor/python-packages"
WORKDIR /home/thumbor

COPY conf/thumbor.conf.tpl /home/thumbor/thumbor.conf.tpl
COPY 404.png /data/loader/
COPY plugins/fallback_loader/ python-packages/fallback_loader/
COPY plugins/thumbor_imgix_compat/ python-packages/thumbor_imgix_compat/

COPY docker-entrypoint.sh /
CMD ["thumbor"]
ENTRYPOINT ["/docker-entrypoint.sh"]
