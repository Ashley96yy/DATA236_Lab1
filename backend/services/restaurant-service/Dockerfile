FROM python:3.12-slim

WORKDIR /backend

# Install dependencies first (cached layer)
COPY services/restaurant-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module and service app
COPY shared/ ./shared/
COPY services/restaurant-service/app/ ./app/

ENV PYTHONPATH=/backend

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
