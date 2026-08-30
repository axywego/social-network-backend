FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p app/static/avatars app/static/posts app/static/private_storage/chat_images

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
