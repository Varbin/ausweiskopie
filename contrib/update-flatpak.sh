#!/bin/bash
set -euo pipefail

version="$(git describe --tags --abbrev=0)"

outdir="./flathub"
outrepo="https://github.com/varbin/in.varb.Ausweiskopie"
manifest="in.varb.Ausweiskopie.yaml"

toolsdir="./tools"
toolsrepo="https://github.com/flatpak/flatpak-builder-tools"
toolscommit="aac65cf44cd4e008594a9d9ac1db08e2025067a6"



if ! flatpak --help > /dev/null; then
  sudo apt install --yes flatpak
fi

flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak remove -y --user --noninteractive org.flathub.flatpak-external-data-checker || true
flatpak install -y --noninteractive --user --or-update --from https://dl.flathub.org/repo/appstream/org.flathub.flatpak-external-data-checker.flatpakref
flatpak install -y --noninteractive --user flathub org.flatpak.Builder

if [ -d "$outdir" ]; then
  rm -rf "$outdir"
fi
if [ -d "$toolsdir" ]; then
  rm -rf "$toolsdir"
fi

git clone "$toolsrepo" "$toolsdir"
cd tools
git checkout "$toolscommit"
cd ..

git clone "$outrepo" "$outdir"
cd "$outdir"
git config --local user.name "github-actions"
git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local commit.gpgsign false

python3 -m pip install requirements-parser
python3 "../$toolsdir/pip/flatpak-pip-generator" -r requirements.txt --ignore-errors
git commit python3-requirements.json -m "Update requirements for $version"
flatpak run --filesystem="$(pwd)" org.flathub.flatpak-external-data-checker --edit-only "$(pwd)/$manifest"
git commit -m "Update external data for $version" "$manifest" --allow-empty
sed -i -E "s/(tag: )(v.+)/\1$version/g" in.varb.Ausweiskopie.yaml
git commit -m "Update tag for metadata to $version" "$manifest" --allow-empty
flatpak run org.flatpak.Builder --force-clean --sandbox --user --install --install-deps-from=flathub --ccache --mirror-screenshots-url=https://dl.flathub.org/media/ --repo=repo builddir "$manifest"
