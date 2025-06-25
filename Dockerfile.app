FROM python:3.13-slim

WORKDIR /app
# USER root

COPY docker-setup.sh .
RUN chmod +x docker-setup.sh && ./docker-setup.sh && rm docker-setup.sh

COPY src/ .