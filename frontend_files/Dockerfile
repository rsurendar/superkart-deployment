FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Backend address on the shared Docker network (can be overridden with -e BACKEND_URL=...)
ENV BACKEND_URL=http://backend:7860

# Streamlit listens on port 8501
EXPOSE 8501

# XSRF protection is disabled because the Codespaces port-forwarding proxy otherwise blocks file uploads (HTTP 403)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
