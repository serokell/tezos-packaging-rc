#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

bot_name="CI bot"
branch="update-binaries-list-$BUILDKITE_TAG"

git config --local user.email "hi@serokell.io"
git config --local user.name "$bot_name"
git remote remove auth-origin 2> /dev/null || :
git remote add auth-origin "https://oath2:$GITHUB_PUSH_TOKEN@github.com:serokell/tezos-packaging.git"
git fetch
git checkout -B "$branch"

python3 package/scripts/update-binaries-list.py

git commit -m "Updated binaries for $BUILDKITE_TAG release"
git push --set-upstream auth-origin "$our_branch"
# gh pr create -B master -t "Update list of binaries for $BUILDKITE_TAG"
# branch="$(git branch)"
# echo $branch
# diff="$(git diff)"
# echo $diff