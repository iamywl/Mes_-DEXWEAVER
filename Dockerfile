FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary kubernetes pydantic psutil
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY api_modules/ /app/api_modules/
COPY app.py /app/
ENV PYTHONPATH=/app
CMD ["python", "app.py"]
