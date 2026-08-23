def get_empty_state_message(keyword):
    """Return a helpful message when no recommendations are found."""
    if keyword:
        return (
            f'No eco-friendly recommendations found for "{keyword}". '
            "Try a different keyword or category."
        )

    return (
        "No eco-friendly recommendations found. "
        "Try selecting a category or searching for something else."
    )


def format_results(results, keyword):
    """Format recommendations or return an empty-state message."""
    if not results:
        return {
            "status": "empty",
            "message": get_empty_state_message(keyword),
            "suggestions": [
                "Try a different keyword",
                "Choose another category",
                "Check nearby options",
            ],
        }

    return {
        "status": "success",
        "results": results,
    }
