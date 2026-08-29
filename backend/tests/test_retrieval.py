from app.main import chunk_text, score


def test_chunk_text_preserves_page():
    chunks = chunk_text("Machine learning learns patterns from training data. " * 30, 3, chunk_size=120)
    assert len(chunks) > 1
    assert all(chunk["page"] == 3 for chunk in chunks)


def test_score_ranks_related_text_higher():
    related = score("what is overfitting", "Overfitting occurs when a model memorizes training data.")
    unrelated = score("what is overfitting", "Photosynthesis uses light energy in plants.")
    assert related > unrelated
