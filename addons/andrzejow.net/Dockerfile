ARG BUILD_FROM=python:3.11-alpine
FROM $BUILD_FROM

RUN apk add --no-cache bash jq curl

WORKDIR /app

# Kopiowanie plików aplikacji z modułu
COPY app.py /app/app.py
COPY youtube_service.py /app/youtube_service.py
COPY config.json /app/config.json
COPY templates /app/templates
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8080

CMD [ "/run.sh" ]
