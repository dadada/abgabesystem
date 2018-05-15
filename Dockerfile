FROM alpine:latest

WORKDIR /app

ADD tubs_checks.xml .
ADD requirements.txt .

ENV JPLAG_VERSION=2.11.9-SNAPSHOT

RUN apk add --no-cache openjdk8 python3 curl git
RUN curl -sL https://github.com/jplag/jplag/releases/download/v${JPLAG_VERSION}/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar -o jplag.jar
RUN pip3 install -r requirements.txt