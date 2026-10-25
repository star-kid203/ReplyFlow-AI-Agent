FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install dependencies at build time
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ app/
COPY run.py .
COPY input_examples/ input_examples/
COPY output_examples/ output_examples/

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["python", "run.py"]