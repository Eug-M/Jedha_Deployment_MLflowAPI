FROM continuumio/miniconda3

WORKDIR /home/app

COPY . /home/app

RUN pip install pandas plotly streamlit numpy datetime openpyxl --prefer-binary

EXPOSE 4000
CMD streamlit run --server.port 4000 --server.address "0.0.0.0" /home/app/app.py
