#!/bin/bash
set -e

BLUE='\033[0;34m'
NC='\033[0m' # No Color

migrated_root=$HOME/tmp/conan/recipes

# Remove untracked files in recipes/
git clean -xfd recipes/

git checkout mass-migration

# Copy recipes to $migrated_root
rm -rf "$migrated_root"
mkdir -p "$migrated_root"
cp recipes -rf "$migrated_root/.."

git branch -D master || true
git checkout -b master
git reset --hard upstream/master
for recipe_dir in recipes/*; do
    recipe=$(basename $recipe_dir)
    echo
    echo -e "${BLUE}Migrating $recipe${NC}"
    git switch master
    git branch -D "migrate/$recipe" || true
    git checkout -b "migrate/$recipe"
    rm -rf "$recipe_dir"
    cp -r "$migrated_root/$recipe" "$recipe_dir"
    git add "$recipe_dir" || true
    if test -n "$(git status --porcelain --untracked-files=no)"; then
        git commit -m "$recipe: migrate to Conan v2"
    else
        git branch -D "migrate/$recipe" || true
    fi
done

git switch mass-migration
