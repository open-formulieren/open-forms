import os

ELASTIC_APM = {
    "SERVICE_NAME": "openforms",
    "SECRET_TOKEN": os.getenv("ELASTIC_APM_SECRET_TOKEN", "default"),
    "SERVER_URL": os.getenv("ELASTIC_APM_SERVER_URL", "http://example.com"),
}
