def has_pending_results(state: dict) -> bool:
    """Return True if the graph state contains unprocessed task results.

    Use this in your classifier/router to detect when the poller has
    injected results that need to be presented to the user.
    """
    return bool(state.get("results_buffer"))
