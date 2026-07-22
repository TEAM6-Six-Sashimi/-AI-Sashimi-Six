"""RAG 색인 스크립트 (1회 실행).

자격증 CSV / NCS CSV / 핏격 안내 PDF를 임베딩해 ChromaDB 3개 컬렉션에 저장한다.
학습 자료 02(CSV 색인) + 03_pdf_chunk(PDF 청킹) 방식.

실행: python scripts/ingest.py
"""
import csv
import sys
from pathlib import Path

from pypdf import PdfReader

# app 패키지 import를 위해 루트 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.features.chatbot.intent_classifier import INTENTS_COLLECTION  # noqa: E402
from app.features.chatbot.rag import DATA_DIR, get_collection  # noqa: E402

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _to_meta(row: dict, keys: list[str]) -> dict:
    """지정 컬럼만 metadata로 추출한다(빈 값은 빈 문자열로)."""
    return {k: (row.get(k) or "") for k in keys}


def index_csv(csv_path: Path, collection_name: str, meta_keys: list[str]) -> None:
    """content 컬럼을 임베딩해 색인한다. id=document_id."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("content") or "").strip()]

    documents = [r["content"] for r in rows]
    ids = [r["document_id"] for r in rows]
    metadatas = [_to_meta(r, meta_keys) for r in rows]

    collection = get_collection(collection_name)
    # 대량이면 배치로 나눠 upsert (Chroma 배치 상한 회피)
    batch = 500
    for i in range(0, len(documents), batch):
        collection.upsert(
            documents=documents[i:i + batch],
            ids=ids[i:i + batch],
            metadatas=metadatas[i:i + batch],
        )
    print(f"[{collection_name}] 색인 완료: {collection.count()}개")


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def index_pdf(pdf_path: Path, collection_name: str) -> None:
    """PDF를 페이지별로 추출 → 청킹 → 색인. metadata={source, page}."""
    reader = PdfReader(str(pdf_path))
    documents, metadatas, ids = [], [], []
    for page_num, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        for i, chunk in enumerate(_chunk_text(text)):
            documents.append(chunk)
            metadatas.append({"source": "핏격 AI 기능 안내", "page": page_num})
            ids.append(f"p{page_num}_c{i}")

    collection = get_collection(collection_name)
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[{collection_name}] 색인 완료: {collection.count()}개 청크")


def index_intents(csv_path: Path) -> None:
    """의도 분류용 예시 질문을 색인한다. 질문 문장 자체를 임베딩해 유사도로 의도를 찾는다."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("example_question") or "").strip()]

    collection = get_collection(INTENTS_COLLECTION)
    collection.upsert(
        documents=[r["example_question"] for r in rows],
        ids=[f"intent_{r['id']}" for r in rows],
        metadatas=[
            {
                "label": r["label"],
                "stage_name": r["stage_name"],
                "example": r["example_question"],
            }
            for r in rows
        ],
    )
    print(f"[{INTENTS_COLLECTION}] 색인 완료: {collection.count()}개")


if __name__ == "__main__":
    print("색인 시작 (임베딩 모델 로드에 시간이 걸릴 수 있습니다)...")

    index_csv(DATA_DIR / "certifications.csv", "certifications", ["종목명", "항목"])
    index_csv(DATA_DIR / "ncs_jobs.csv", "ncs_jobs", ["분류", "능력단위 명"])
    index_pdf(DATA_DIR / "fitgyeok_ai_guide.pdf", "fitgyeok_ai")
    index_intents(DATA_DIR / "intents.csv")

    print("전체 색인 완료 ✅")
