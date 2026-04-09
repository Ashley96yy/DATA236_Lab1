FROM python:3.12-slim

WORKDIR /backend

# Install dependencies first (cached layer)
COPY services/review-api-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module and service app
COPY shared/ ./shared/
COPY services/review-api-service/app/ ./app/

ENV PYTHONPATH=/backend

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
