# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 임베딩 모델을 이미지에 미리 받아둔다.
# 런타임에 받으면 첫 요청이 수십 초 걸리고, USER app 권한으로는 캐시 쓰기가 막힌다.
# 다운로드 자체는 캐시 마운트(재빌드 시 재사용)로 받고, 최종 이미지에 들어가야 하는
# 결과물만 /app/.cache/huggingface로 복사한다 (캐시 마운트는 이미지 레이어에 안 남음).
ENV HF_HOME=/app/.cache/huggingface
RUN --mount=type=cache,target=/root/.cache/huggingface-dl \
    HF_HOME=/root/.cache/huggingface-dl python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')" \
    && mkdir -p /app/.cache/huggingface \
    && cp -r /root/.cache/huggingface-dl/. /app/.cache/huggingface/

# RAG 색인 단계.
# ingest.py가 필요로 하는 건 rag.py 하나뿐이라 먼저 복사한다.
# 전체 app을 여기서 복사하면 코드 한 줄만 고쳐도 캐시가 깨져 매 배포마다 재색인된다.
COPY app/__init__.py app/
COPY app/features/__init__.py app/features/
COPY app/features/chatbot/__init__.py app/features/chatbot/
COPY app/features/chatbot/rag.py app/features/chatbot/
COPY data ./data
COPY scripts ./scripts
RUN python scripts/ingest.py

# 애플리케이션 코드는 마지막에 복사해야 위 색인 레이어의 캐시가 유지된다.
COPY app ./app

# chroma_db(sqlite)는 런타임에 열 때 쓰기 권한이 필요하다.
RUN chown -R app:app /app/chroma_db /app/.cache

ENV PORT=8001

EXPOSE 8001

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8001/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
