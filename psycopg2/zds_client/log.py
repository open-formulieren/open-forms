from datetime import datetime


class Log:
    _entries = []
    max_entries = 100

    @classmethod
    def add(
        cls,
        service: str,
        url: str,
        method: str,
        request_headers: dict,
        request_data: dict,
        response_status: int,
        response_headers: dict,
        response_data: dict,
        params: dict = None,
    ):
        # Definitly not thread-safe
        if len(cls._entries) >= cls.max_entries:
            cls._entries.pop(0)

        entry = {
            "timestamp": datetime.now(),
            "service": service,
            "request": {
                "url": url,
                "method": method,
                "headers": request_headers,
                "data": request_data,
                "params": params,
            },
            "response": {
                "status": response_status,
                "headers": response_headers,
                "data": response_data,
            },
        }

        cls._entries.append(entry)

    @classmethod
    def clear(cls):
        cls._entries = []

    @classmethod
    def entries(cls):
        return cls._entries
