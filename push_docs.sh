#!/bin/bash
# https://stackoverflow.com/questions/26224526/how-to-push-a-git-ignored-folder-to-a-subtree-branch

if [[ "$(git status)" == *"nothing to commit, working tree clean"* ]]
then
    sed -i "/site/d" ./.gitignore
    git add .
    git commit -m "Edit .gitignore to publish"
    git push origin `git subtree split --prefix site/ master`:gh-pages
    git reset HEAD~
    git checkout .gitignore
else
    echo "Need clean working directory to publish"
fi
