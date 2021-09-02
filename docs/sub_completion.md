# Submission completion flow

```
POST /api/v1/submissions/:uuid/_complete
```

* Enter submission completion flow
    * On transaction commit
        * Build celery task chain
        * Start celery task chain
        * Store AsyncResult ID in DB
    * Generate HMAC link to check status (submission UUID + time expiry)
    * Respond with status link

* Poll status check link (`GET /api/v1/submissions/:sid/:token/status`)
    * Check task ID
    * Get AsyncResult and check `status|ready()`
    * Ready?
        No:
            report not ready
            poll again
        Yes:
            Error?
                Yes:
                    * include error message
                    * return to step 1 (later: specific step?) or message to retry?
                No:
                    * include PDF download link
                    * include confirmation page content
                    * include payment URL
