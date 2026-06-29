from collections import Counter
from typing import List, Tuple

def get_majority_vote_and_confidence(predictions: List[str]) -> Tuple[str, float]:
    """
    Computes majority vote and agreement ratio (confidence).
    
    Args:
        predictions: A list of N predictions from the LLM for the same input.
        
    Returns:
        A tuple of (majority_technique, confidence_score)
        where confidence_score is in the range [1/N, 1.0].
    """
    if not predictions:
        return "", 0.0
        
    counts = Counter(predictions)
    majority_technique, majority_count = counts.most_common(1)[0]
    confidence = majority_count / len(predictions)
    
    return majority_technique, confidence

def test_scorer():
    # Example test cases
    preds_high = ["T1059", "T1059", "T1059", "T1059", "T1059"] # 1.0
    preds_med  = ["T1059", "T1059", "T1059", "T1105", "T1105"] # 0.6
    preds_low  = ["T1059", "T1105", "T1105", "T1046", "T1046"] # 0.4 (T1105 or T1046)

    print(get_majority_vote_and_confidence(preds_high))
    print(get_majority_vote_and_confidence(preds_med))
    print(get_majority_vote_and_confidence(preds_low))

if __name__ == "__main__":
    test_scorer()
