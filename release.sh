#!/bin/bash

set -e

BRANCH="production-release"

git fetch origin && \
git fetch origin -t && \
git checkout -b "$BRANCH" origin/main && \

echo "Fetched origin, created release-branch."

NEW_TAG_D="-1"
NEW_TAG=$NEW_TAG_D

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    exit 1
fi

for cmd in "$@"
do
	case $cmd in
		"--major")
			echo "Incrementing Major Version"
      NEW_TAG=$(sh ./semver.sh -v major)
			;;
		"--minor")
			echo "Incrementing Minor Version"
      NEW_TAG=$(sh ./semver.sh -v minor)
			;;
		"--patch")
			echo "Incrementing Patch Version"
      NEW_TAG=$(sh ./semver.sh -v patch)
			;;
        *)
            echo "No version specified"
            ;;
	esac
done

if [ $NEW_TAG == $NEW_TAG_D ]; then
exit 1
fi

echo "New tag $NEW_TAG"
echo "Pushing tag to origin"

git tag "$NEW_TAG" && \
git push origin "$NEW_TAG" && \

echo "Pushing tag to origin" && \
git branch -m "$BRANCH" && \

echo "Pushing $BRANCH" && \
git push origin --follow-tags "$BRANCH" && \

echo "Don't forget to merge to master and Approve the deploy to the production environment!"

exit 0
