import logging  # noqa: TID251


class AuditFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # with structlog, record.msg is an event dict, so discard anything that comes
        # from elsewhere
        if not isinstance(record.msg, dict):
            return False
        return record.msg.get("audit", False)
