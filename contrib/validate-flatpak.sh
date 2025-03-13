#!/bin/bash
set -euo pipefail

version="$(python -m setuptools_scm --strip-dev)"

if grep "$version" ./contrib/in.varb.Ausweiskopie.desktop; then
  echo "All good, there seems to be a changelog!"
else
  echo "No changelog for this version yet!" >> /dev/stderr
  exit 1
fi