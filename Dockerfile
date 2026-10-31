FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && pip install -r requirements.txt
ENV FLASK_APP=backend/app.py
EXPOSE 5000
CMD ["python","backend/app.py"]
