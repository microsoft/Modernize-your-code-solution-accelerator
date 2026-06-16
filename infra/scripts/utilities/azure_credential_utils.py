"""Shared Azure credential helpers for infra scripts."""

from azure.identity import DefaultAzureCredential


def get_default_credential() -> DefaultAzureCredential:
    """Return a credential that works for local dev and CI."""
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)
