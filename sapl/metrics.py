from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST


def health_registry(check_results: dict) -> bytes:
    """
    check_results: {"app": True/False, "db": True/False, ...}
    """
    reg = CollectorRegistry()
    g = Gauge("app_health", "1 if healthy, 0 if unhealthy", ["component"], registry=reg)
    for comp, ok in check_results.items():
        g.labels(component=comp).set(1 if ok else 0)
    return generate_latest(reg)
