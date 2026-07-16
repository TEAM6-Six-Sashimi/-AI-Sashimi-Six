FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=8001

EXPOSE 8001

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8001/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
