from drainloader.plugin import BasePlugin
from drainloader.plugins.pixeldrain import PixelDrain

PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    "pixeldrain.com": PixelDrain,
}

# Domains that support subdomains
SUBDOMAIN_SUPPORTED: set[str] = set()


def get_plugin_class(domain: str) -> type[BasePlugin] | None:
    """
    Resolve domain to plugin class.
    """
    domain = domain.lower().strip()

    # Exact match
    if domain in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[domain]

    # Partial match fallback
    for registered_domain, plugin_class in PLUGIN_REGISTRY.items():
        if registered_domain in domain:
            return plugin_class

    return None
