#!/bin/bash
# https://stackoverflow.com/questions/26224526/how-to-push-a-git-ignored-folder-to-a-subtree-branch

STATUS="$(git status)"

if [[ $STATUS == *"nothing to commit, working directory clean"* ]]
then
    sed -i "" 'site/' ./.gitignore
    git add .
    git commit -m "Edit .gitignore to publish"
    git push origin `git subtree split --prefix gh-pages master`:gh-pages --force
    git reset HEAD~
    git checkout .gitignore
else
    echo "Need clean working directory to publish"
fi
