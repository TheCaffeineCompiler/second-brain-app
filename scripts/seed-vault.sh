#!/bin/sh
# Create the bare stand-in for GitHub and seed it with the fixture Vault.
# Never re-seeds an existing repository — initialisation is not destructive (ADR-0023).
set -e

if [ -d /srv/vault.git ]; then
  echo "vault already initialised, leaving it alone"
  exit 0
fi

git init --bare -q -b main /srv/vault.git
git clone -q /srv/vault.git /tmp/staging
cp -R /seed/. /tmp/staging/
cd /tmp/staging
git add -A
git -c user.email=dev@local -c user.name=dev commit -qm "chore: seed fixture vault"
git push -q origin main
echo "seeded $(git rev-list --count HEAD) commit into /srv/vault.git"
