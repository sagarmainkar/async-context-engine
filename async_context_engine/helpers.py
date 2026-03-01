def has_pending_results(state: dict) -> bool:
    """Check if the state has pending results in the results_buffer."""
    return bool(state.get("results_buffer"))
