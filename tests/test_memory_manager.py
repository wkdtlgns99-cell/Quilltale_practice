"""
Tests for MemoryManager, QdrantVectorStore, and JinaEmbedder.
"""
from src.memory.memory_manager import MemoryManager
from src.memory.qdrant_store import QdrantVectorStore
from src.memory.embeddings import JinaEmbedder, BGEM3Embedder, get_default_embedder


def test_bge_m3_embedder_dimension():
    embedder = BGEM3Embedder()
    vec = embedder.embed_query("단검을 집어든다")
    assert len(vec) == 1024
    
    passages = embedder.embed_passages(["기억 1", "기억 2"])
    assert len(passages) == 2
    assert len(passages[0]) == 1024
    assert len(passages[1]) == 1024


def test_default_embedder_in_memory_manager():
    store = QdrantVectorStore(in_memory=True)
    mm = MemoryManager(vector_store=store)  # Uses get_default_embedder()
    assert isinstance(mm.embedder, BGEM3Embedder)

    session_id = "test_sess_bge_01"
    ok = mm.record_turn_memory(
        session_id=session_id,
        turn=1,
        action="고대 마법 서적을 펼쳐 비문을 읽는다",
        narration="고대 룬 문자가 은은한 푸른빛을 발산합니다.",
        location_id="library",
        significance=5,
        emotional_tone="mystic",
    )
    assert ok

    context = mm.retrieve_context(
        session_id=session_id,
        current_action="비문의 뜻을 해석한다",
        current_location="library",
        top_k=2,
    )
    assert "관련 과거 사건" in context
    assert "고대 마법 서적" in context


def test_memory_manager_record_and_retrieve():
    store = QdrantVectorStore(in_memory=True)
    embedder = JinaEmbedder()
    mm = MemoryManager(vector_store=store, embedder=embedder)

    session_id = "test_sess_01"

    # Record turn with high significance (anchor)
    ok = mm.record_turn_memory(
        session_id=session_id,
        turn=1,
        action="선술집 주인을 위협하여 정보를 캐냈다",
        narration="마르타는 잔뜩 겁을 먹고 뒤로 물러섰습니다.",
        location_id="tavern",
        npc_ids=["barkeep"],
        significance=4,
        emotional_tone="fearful",
    )
    assert ok

    # Retrieve context
    context = mm.retrieve_context(
        session_id=session_id,
        current_action="마르타에게 다시 다가가 말을 건다",
        current_location="tavern",
        current_npcs=["barkeep"],
        top_k=2,
    )

    assert "관련 과거 사건" in context
    assert "선술집 주인을 위협" in context
    assert "영구 보존된 핵심 사건" in context
