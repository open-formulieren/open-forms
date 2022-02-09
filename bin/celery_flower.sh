#!/bin/bash
exec celery --app openforms --workdir src flower
