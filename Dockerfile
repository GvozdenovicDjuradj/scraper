FROM python:3.9-slim-buster
RUN mkdir /app
RUN mkdir /app/output
COPY main.py /app/
COPY requirements.txt /app/
WORKDIR /app/
RUN pip3 install -r requirements.txt
CMD [ "python3" , "main.py"]