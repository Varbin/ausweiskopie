#!/bin/bash
set -euo pipefail

version="$(git describe --tags --abbrev=0)"

outdir="./flathub"
outpush="git@github.com:varbin/in.varb.Ausweiskopie.git"

if [ -v FLATPAK_UPDATE_KEY ]; then
  mkdir -p ~/.ssh ; true
  echo "$FLATPAK_UPDATE_KEY" >> ~/.ssh/id_flatpak
  chmod 600 ~/.ssh/id_flatpak
  export GIT_SSH_COMMAND='ssh -i ~/.ssh/id_flatpak -o IdentitiesOnly=yes'
fi

cd "$outdir"

git checkout -b "update/$version"
git remote set-url --push origin "$outpush"
git push origin "update/$version"