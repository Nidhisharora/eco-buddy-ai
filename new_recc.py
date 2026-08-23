def get_recommendations(items, keyword):
    """Return recommendations matching the keyword."""
    if not keyword:
        return []

    keyword = keyword.lower().strip()

    return [
        item for item in items
        if keyword in item.get("name", "").lower()
        or keyword in item.get("category", "").lower()
    ]
