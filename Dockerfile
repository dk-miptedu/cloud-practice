FROM --platform=linux/amd64 python:3.8

RUN apt-get update -y \
    && apt-get install -y wget gnupg1 --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update -y \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
      --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY summary_bot/requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app

RUN pip install -r requirements.txt

RUN playwright install firefox chromium
#firefox
RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
    && mkdir -p /home/pptruser/Downloads \
    && chown -R pptruser:pptruser /home/pptruser


RUN pip install lxml_html_clean
RUN pip install pyppeteer==1.0.2
RUN pip install --upgrade pyee

RUN playwright install-deps  
RUN chown -R pptruser:pptruser /opt/app  
#COPY .env .    

COPY . /opt/app

USER root 

ARG FROM_DOCKER=1
ARG BOT_TOKEN

ENV BOT_TOKEN=$BOT_TOKEN
ENV MODEL_NAME='sshleifer/distilbart-cnn-12-6' 
#'facebook/bart-large-cnn'

ENV FROM_DOCKER=$FROM_DOCKER
ENV LOG_LEVEL=DEBUG


CMD ["python3", "summary_bot/bot.py"]
