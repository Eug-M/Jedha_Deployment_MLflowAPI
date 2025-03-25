FROM continuumio/miniconda3

RUN apt-get update -y 
RUN apt-get install nano curl -y

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY ./src .

CMD fastapi run app.py --port $DEFAULT_PORT