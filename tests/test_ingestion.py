from corebot_ai.ingestion.pipeline import smart_chunk


def test_smart_chunk_overlap() -> None:
    text = "a" * 100
    chunks = smart_chunk(text, chunk_size=30, overlap=10)
    assert len(chunks) == 5
    assert chunks[0] == "a" * 30
    assert len(chunks[-1]) == 20
