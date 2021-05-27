#!/bin/bash
exec celery flower --app openforms --workdir src
