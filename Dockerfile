FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY job_market ./job_market
COPY data ./data
RUN pip install --no-cache-dir -e '.[dashboard]'

EXPOSE 8501
CMD ["streamlit", "run", "job_market/dashboard/main.py", "--server.address=0.0.0.0"]
