#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

# This script signs all commits in the current 'BUILDKITE_BRANCH'

set -e

git fetch --all
# We call this script only after a commit was pushed to the given branch, so it's safe to switch to it
git switch "$BUILDKITE_BRANCH"

# Try to sign and push signed commits, retry in case of collision
while : ; do
    git fetch --all
    git reset --hard origin/"$BUILDKITE_BRANCH"
    echo "$BUILDKITE_BRANCH $BUILDKITE_PIPELINE_DEFAULT_BRANCH"
    git cherry -v "origin/$BUILDKITE_PIPELINE_DEFAULT_BRANCH" "$BUILDKITE_BRANCH"
    # git rebase --exec 'git commit --amend --no-edit -n --gpg-sign="tezos-packaging@serokell.io"' master || git rebase --abort; exit 1
    # This should fail in case we're trying to overwrite some new commits
    ! git push --force-with-lease || break
done
