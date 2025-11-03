class DomainConflict(Exception):
    """Raised when an operation violates a domain invariant.

    Example: attempting to modify a transaction that belongs to a transfer.
    """
    pass

