# Lightweight Python base image matching the training Python version
FROM python:3.11-slim

# libgomp provides the OpenMP runtime needed by XGBoost and scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the serialized model
COPY app.py superkart_model.joblib ./

# The API listens on port 7860
EXPOSE 7860

# Serve the Flask app with gunicorn (production-grade WSGI server)
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:7860", "app:superkart_api"]
