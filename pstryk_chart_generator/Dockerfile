ARG BUILD_FROM=python:3.11-alpine
FROM $BUILD_FROM

# Install necessary fonts and build dependencies for matplotlib/pandas
RUN apk add --no-cache \
    bash \
    jq \
    curl \
    freetype-dev \
    libpng-dev \
    openblas-dev \
    g++ \
    font-terminus \
    font-inconsolata \
    font-dejavu \
    && pip3 install --no-cache-dir \
    matplotlib \
    requests \
    pytz \
    pandas \
    aiohttp \
    apscheduler

COPY run.sh /
COPY generator.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
