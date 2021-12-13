#!/bin/bash
#
# Workaround for installing xmlsec with pinned lmxl version.
# See https://github.com/mehcode/python-xmlsec/issues/198 for more information

# extract the pinned lxml version
LXML=$(grep lxml -r requirements/base.txt)

# ensure this version is installed before xmlsec is attempted to install
pip install "$LXML"

# export the include path for the xmlsec build
SITE_PACKAGES=$(python -c 'import site; print(site.getsitepackages()[0])')

export C_INCLUDE_PATH="$SITE_PACKAGES/lxml/includes"
