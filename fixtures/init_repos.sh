#!/bin/bash
set -euo pipefail

BASE=/opt/app-root/data/

git config --global user.name "ConfigMaster"
git config --global user.email "configmaster@dev"

function init_repo() {
  REPO="$BASE/$1"
  REMOTE="$BASE/remotes/$1"
  echo ">>> Initializing repo $1"
  if [[ -d "$REPO" ]]; then
    echo "$REPO already exists"
    return
  fi

  # Fake remote
  mkdir -p "$REMOTE"
  cd "$REMOTE"
  git init --bare

  # Repository
  mkdir "$REPO"
  cd "$REPO"
  git init
  git commit --allow-empty -m "Init commit"
  git remote add origin "$REMOTE"
  git push -u origin master
}

init_repo network-configs
init_repo secure-network-configs
