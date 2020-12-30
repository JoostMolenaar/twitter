FROM alpine:3.12 AS build
RUN apk add python3
ENV PYTHONUSERBASE=/app

RUN python3 -m ensurepip

ENV PIP_PROGRESS_BAR=off \
    PIP_NO_WARN_SCRIPT_LOCATION=no \
    PIP_NO_CACHE_DIR=no \
    PIP_DISABLE_PIP_VERSION_CHECK=no \
    PIP_NO_INDEX=yes \
    PIP_FIND_LINKS=/var/lib/python

ARG ROBOT_ZOO_VERSION
RUN python3 -m pip install --user "robot_zoo==$ROBOT_ZOO_VERSION"

FROM alpine:3.12
RUN apk add python3
ENV PYTHONUSERBASE=/app

RUN apk add libcap
WORKDIR /app
CMD python3 -m robot_zoo
RUN apk add tzdata
ENV TZ=Europe/Amsterdam
USER 999:999
ENV TZ=Europe/Amsterdam
COPY --from=build /app /app
