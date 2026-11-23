FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY frontend/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend

EXPOSE 8501

CMD ["streamlit", "run", "frontend/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]