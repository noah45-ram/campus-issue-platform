import re

DEMO_DOCUMENTS = [
    {
        "id": "KB-WAT-001",
        "title": "Water Leak & Conservation Guidelines",
        "content": (
            "Report any leaking taps, running cisterns, or broken pipelines immediately. "
            "Where safe to do so, place a container beneath minor drips to capture water for non-potable uses. "
            "Ensure taps are turned off completely after use to prevent water wastage."
        ),
        "category": "water",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-ELE-002",
        "title": "Electrical Equipment & Campus Safety Protocol",
        "content": (
            "Never tamper with electrical switchboards, exposed cables, or malfunctioning fixtures. "
            "Keep water and moist materials strictly away from all electrical installations. "
            "In case of sparks or burning odor, keep distance and notify emergency facilities staff at once."
        ),
        "category": "energy",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-WAS-003",
        "title": "General Campus Waste Segregation Guide",
        "content": (
            "Sort campus waste at source: use green bins for biodegradable wet waste and blue bins for clean recyclables. "
            "Do not overload waste bins beyond capacity; report overflowing disposal points to custodial services."
        ),
        "category": "waste",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-FOO-004",
        "title": "Dining Hall & Food Waste Management",
        "content": (
            "Minimize food wastage by serving measured portions in hostel mess and cafeterias. "
            "Dispose of unconsumed organic food remains strictly into marked compost collection receptacles."
        ),
        "category": "food",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-PAP-005",
        "title": "Paper Conservation & Recycling Practices",
        "content": (
            "Promote double-sided printing and digital submissions across academic blocks. "
            "Place unsoiled exam booklets, cardboard, and white sheets in designated dry paper recycling bins."
        ),
        "category": "paper",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-EWA-006",
        "title": "Electronic Waste (E-Waste) Safe Handling",
        "content": (
            "Disused batteries, charging cables, electronic parts, and damaged accessories must never be mixed with normal trash. "
            "Deposit electronic scrap into designated e-waste drop-off bins located in the IT and department lobbies."
        ),
        "category": "e_waste",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-REP-007",
        "title": "Standard Campus Issue Reporting Procedure",
        "content": (
            "When logging a campus facility or sustainability issue, supply an exact location (hostel, block, floor). "
            "Check existing campus alerts to verify if the issue has already been registered."
        ),
        "category": "general",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
    {
        "id": "KB-EMG-008",
        "title": "Campus Hazard & Emergency Reporting Protocol",
        "content": (
            "For fires, gas leaks, falling debris, or electrical emergencies, vacate the hazard zone immediately. "
            "Contact the 24/7 campus security control room or maintenance helpline before attempting any other action."
        ),
        "category": "general",
        "source": "GreenCampus Sentinel Demo Knowledge Base",
    },
]

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "it", "this", "that", "near", "from", "with", "there",
    "here", "has", "have", "had", "been", "be", "by", "some", "any", "please",
    "reporting", "report", "issue", "campus"
}


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def search_knowledge(query: str, category: str | None = None) -> list[dict]:
    """
    Search the local demo knowledge base using deterministic keyword matching.

    Returns the top matching demo documents. Does NOT claim to represent official university policy.
    """
    if not query:
        return []

    q_tokens = _tokenize(query)
    cat_norm = (category or "").strip().lower()

    scored_docs = []

    for doc in DEMO_DOCUMENTS:
        doc_cat = doc["category"].lower()
        doc_tokens = _tokenize(doc["title"] + " " + doc["content"])

        overlap = len(q_tokens.intersection(doc_tokens))
        
        # Category affinity bonus
        cat_bonus = 0
        if cat_norm and (doc_cat == cat_norm or doc_cat == "general"):
            cat_bonus = 2

        score = overlap * 3 + cat_bonus

        # Require at least some token overlap or exact category match if score > 0
        if score > 0 and overlap > 0:
            scored_docs.append((score, doc))

    # Sort descending by score
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    # Return top 2 matching documents
    return [doc for _, doc in scored_docs[:2]]
