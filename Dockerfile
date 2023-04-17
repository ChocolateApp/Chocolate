FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y ffmpeg && apt-get install -y unrar && apt-get install -y git

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /chocolate

CMD ["python", "/chocolate/app.py"]