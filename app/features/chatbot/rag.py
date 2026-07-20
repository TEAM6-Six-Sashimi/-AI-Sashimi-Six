"""RAG(검색) 모듈 — 학습 자료 02(순수) 방식.

ChromaDB + SentenceTransformer 임베딩으로, 분류 결과의 ragSourceType에 해당하는
컬렉션에서 사용자 질문과 유사한 청크를 검색한다.
"""
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# fast-api/ 루트 기준 경로 (실행 위치와 무관하게 동작)
_ROOT = Path(__file__).resolve().parents[3]
CHROMA_PATH = str(_ROOT / "chroma_db")
DATA_DIR = _ROOT / "data"

MODEL_NAME = "jhgan/ko-sroberta-multitask"  # 한글 문장 임베딩 모델
SIMILARITY_THRESHOLD = 0.35                 # 이 미만이면 관련 없는 청크로 판단해 버린다

# 분류 결과의 ragSourceType → ChromaDB 컬렉션 이름
COLLECTION_BY_SOURCE = {
    "CERTIFICATE": "certifications",  # 국가기술자격 시험정보
    "JOB_NCS": "ncs_jobs",            # NCS 직무 정보
    "FITGYEOK_AI": "fitgyeok_ai",     # 핏격 AI 기능 안내
    # "COURSE": 강의 데이터 없음(추천 미지원) → 검색 안 함
}


@lru_cache(maxsize=1)
def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=CHROMA_PATH)


@lru_cache(maxsize=1)
def _embedding_fn():
    # 모델을 한 번만 로드해 재사용 (매 요청마다 로드하면 느리다)
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)


@lru_cache(maxsize=8)
def get_collection(name: str):
    return _client().get_or_create_collection(
        name=name,
        embedding_function=_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def _query(collection, query: str, top_k: int, where: dict | None = None) -> list[dict]:
    """컬렉션에서 검색하고 유사도 임계값을 넘는 청크만 돌려준다."""
    results = collection.query(query_texts=[query], n_results=top_k, where=where)

    chunks: list[dict] = []
    for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
    ):
        similarity = 1 - dist
        if similarity >= SIMILARITY_THRESHOLD:
            chunks.append({"content": doc, "metadata": meta or {}, "similarity": similarity})
    return chunks


def _certificate_name_filter(rag_keywords: list[str] | None) -> dict | None:
    """분류가 뽑은 ragKeywords 중 실제 자격증 종목명과 정확히 일치하는 게 있으면 필터를 만든다.

    자격증 청크는 '시행처·관련학과·검정방법' 같은 공통 문구가 길어, 의미 검색만으로는
    이름이 비슷한 다른 종목(예: 정보처리기사 ↔ 정보관리기술사)이 섞인다.
    종목명으로 먼저 좁히면 이 문제가 사라진다.
    """
    if not rag_keywords:
        return None

    known_names = _certificate_names()
    for keyword in rag_keywords:
        name = keyword.strip()
        if name in known_names:
            return {"종목명": name}
    return None


@lru_cache(maxsize=1)
def _certificate_names() -> frozenset[str]:
    """색인된 자격증 종목명 집합 (필터 키워드가 실제 종목명인지 확인용)."""
    collection = get_collection(COLLECTION_BY_SOURCE["CERTIFICATE"])
    metadatas = collection.get(include=["metadatas"])["metadatas"]
    return frozenset(
        m["종목명"] for m in metadatas if m and m.get("종목명")
    )


def warmup() -> None:
    """임베딩 모델과 컬렉션을 미리 메모리에 올린다.

    모델(약 440MB) 로딩이 첫 요청 때 일어나면 30초를 넘겨 Spring 타임아웃에 걸린다.
    서버 기동 직후 미리 불러두면 첫 사용자도 정상 응답을 받는다.
    """
    for collection_name in COLLECTION_BY_SOURCE.values():
        get_collection(collection_name)
    _certificate_names()


def retrieve(
        rag_source_type: str,
        query: str,
        top_k: int = 3,
        rag_keywords: list[str] | None = None,
) -> list[dict]:
    """ragSourceType에 해당하는 컬렉션에서 query와 유사한 청크 top_k개를 검색한다.

    자격증(CERTIFICATE)은 ragKeywords에 실제 종목명이 있으면 그 종목으로 먼저 좁혀 검색하고,
    결과가 없으면 필터 없이 재검색한다(하이브리드).

    반환: [{content, metadata, similarity}, ...] (유사도 임계값 이상만)
    대상 컬렉션이 없거나(NONE 등) 결과가 없으면 빈 리스트.
    """
    collection_name = COLLECTION_BY_SOURCE.get(rag_source_type)
    if not collection_name or not query.strip():
        return []

    collection = get_collection(collection_name)

    if rag_source_type == "CERTIFICATE":
        where = _certificate_name_filter(rag_keywords)
        if where:
            chunks = _query(collection, query, top_k, where=where)
            if chunks:  # 종목명으로 좁혀서 찾았으면 그대로 사용
                return chunks
            # 해당 종목에 유사한 청크가 없으면 필터 없이 폴백

    return _query(collection, query, top_k)


def format_rag_context(chunks: list[dict]) -> str:
    """검색된 청크들을 답변 프롬프트의 [RAG 참고 정보]에 넣을 텍스트 블록으로 만든다."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        # 메타데이터 중 출처를 짧게 표시 (종목명/분류/page 등 있는 것만)
        source_hint = " ".join(
            str(v) for k, v in meta.items()
            if k in ("종목명", "분류", "능력단위 명", "source", "page") and v
        )
        header = f"[자료 {i}]" + (f" ({source_hint})" if source_hint else "")
        blocks.append(f"{header}\n{chunk['content']}")
    return "\n\n".join(blocks)
