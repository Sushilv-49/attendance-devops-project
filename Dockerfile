FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV DB_PATH=/data/attendance.db

EXPOSE 5000

CMD ["python","app.py"]