def compute_risk (
    no_review: bool,
    ci_unclean: bool,
    sensitive_path: bool,
    large_unreviewed: bool,
    direct_to_main: bool,
) -> str:
    score = 0
    if no_review: 
        score += 1
    if ci_unclean: 
        score += 1
    if sensitive_path: 
        score += 1
    if large_unreviewed: 
        score += 1
    if direct_to_main: 
        score += 1
    if score == 0: 
        return "low"
    if score == 1: 
        return "medium"
    if score == 2: 
        return "high"
    if score >= 3: 
        return "critical"
    