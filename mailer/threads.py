"""Thread operations for Gmail."""

from googleapiclient.discovery import Resource

from mailer.types import GmailThread, ThreadID


def list_threads(
    service: Resource, max_results: int = 10, query: str | None = None
) -> list[GmailThread]:
    """List email threads.

    Args:
        service: Authenticated Gmail API service
        max_results: Maximum number of threads to return
        query: Gmail query string for filtering

    Returns:
        List of thread objects
    """
    # TODO: Implement thread listing
    raise NotImplementedError("Thread listing not yet implemented")


def get_thread(service: Resource, thread_id: str) -> GmailThread:
    """Get a specific thread by ID.

    Args:
        service: Authenticated Gmail API service
        thread_id: ID of the thread to retrieve

    Returns:
        Thread object with all messages
    """
    # TODO: Implement get thread
    raise NotImplementedError("Get thread not yet implemented")
