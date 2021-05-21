#!/bin/bash
exec celery flower --app bptl --workdir src
