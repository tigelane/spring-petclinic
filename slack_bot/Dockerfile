FROM alpine:3.6

MAINTAINER Tige Phillips <tige@infogroupnw.com>

####################
# PYTHON and TOOLS #
####################
RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN apk add --no-cache bash
RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install slackclient

#################
# App install
#################
ADD pet_bot.py /usr/local/bin
