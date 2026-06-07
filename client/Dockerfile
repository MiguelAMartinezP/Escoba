FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install kivy
RUN pip install websockets

CMD ["python", "main.py"]