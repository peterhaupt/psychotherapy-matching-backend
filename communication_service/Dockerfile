FROM python:3.11-slim

WORKDIR /app

# Copy shared directory first
COPY shared ./shared

# Copy service-specific files
COPY communication_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY communication_service .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Set environment variables (removed FLASK_ENV)
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py

EXPOSE 8004

CMD ["python", "app.py"]