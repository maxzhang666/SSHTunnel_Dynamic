FROM python:3-slim

WORKDIR /root

COPY ./open_tunnel.py open_tunnel.py
COPY ./requirements.txt requirements.txt

RUN apt-get update && apt-get install -y curl

RUN chmod +x open_tunnel.py

RUN pip install -r requirements.txt

HEALTHCHECK --interval=1m --timeout=3s --retries=3 --start-period=1m CMD curl -x socks5h://127.0.0.1:10080 -fs https://www.icanhazip.com || exit 1

CMD [ "python","-u", "open_tunnel.py" ]
