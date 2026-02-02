import structlog

__all__ = ["audit_logger"]

audit_logger = structlog.stdlib.get_logger("openforms_audit")
