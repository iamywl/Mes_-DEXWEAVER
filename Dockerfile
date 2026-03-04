FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir fastapi uvicorn psycopg2-binary pydantic psutil bcrypt PyJWT kubernetes alembic && \
    pip install --no-cache-dir numpy scikit-learn xgboost shap ortools || true && \
    pip install --no-cache-dir prophet || true

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY api_modules/ /app/api_modules/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY app.py /app/

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
