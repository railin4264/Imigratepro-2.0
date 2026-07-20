FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directories the app writes to at runtime (generated PDFs, client uploads)
# -- created and owned by the non-root user up front, since a volume mount
# or first write as `app` would otherwise fail against root-owned paths.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p generated_forms uploaded_documents \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
