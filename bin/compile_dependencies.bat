@echo off

for /F "tokens=1" %%i in ('git rev-parse --show-toplevel') do set toplevel=%%i

cd %toplevel%

REM we are echo'ing the Linux variant here, simply because we have more Linux users
set CUSTOM_COMPILE_COMMAND="./bin/compile_dependencies.sh"

REM Base deps
pip-compile^
    --no-emit-index-url^
    %*^
    requirements/base.in

REM Dependencies for testing
pip-compile^
    --no-emit-index-url^
    --output-file requirements/ci.txt^
    %*^
    requirements/test-tools.in

REM Dev depedencies - exact same set as CI + some extra tooling
pip-compile^
    --no-emit-index-url^
    --output-file requirements/dev.txt^
    %*^
    requirements/dev.in
