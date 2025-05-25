from sentence_transformers import CrossEncoder

# Load the cross-encoder model once globally
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_with_crossencoder(query, candidates, top_k=3):
    """
    Rerank product or recipe candidates using a CrossEncoder model.

    Args:
        query (str): User input query.
        candidates (list[dict]): List of candidate metadata dicts. Each must have a "chunk_text" field.
        top_k (int): Number of top results to return.

    Returns:
        list of tuples: (score, candidate_dict)
    """
    # Filter candidates with valid text
    valid_candidates = [c for c in candidates if isinstance(c.get("chunk_text"), str) and c["chunk_text"].strip()]
    
    if not valid_candidates:
        return []

    # Prepare input for the reranker
    pairs = [(query, c["chunk_text"]) for c in valid_candidates]
    scores = reranker.predict(pairs)

    # Attach scores and sort
    scored = sorted(zip(scores, valid_candidates), key=lambda x: x[0], reverse=True)

    return scored[:top_k]
