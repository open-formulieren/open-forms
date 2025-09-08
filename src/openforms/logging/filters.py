import logging  # noqa: TID251


class AuditFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # extra kwargs passed via structlog eventually end up as log record attributes
        return getattr(record, "audit", False)
