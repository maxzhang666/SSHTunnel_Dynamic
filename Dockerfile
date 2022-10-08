FROM python:3-slim

WORKDIR /root

COPY ./open_tunnel.py open_tunnel.py
COPY ./requirements.txt requirements.txt

RUN chmod +x open_tunnel.py

RUN pip install -r requirements.txt

CMD [ "python","-u", "open_tunnel.py" ]