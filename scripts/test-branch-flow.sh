#!/bin/sh
set -eu

validator="./scripts/validate-branch-flow.sh"

expect_pass() {
    "${validator}" "$1" "$2" >/dev/null
}

expect_fail() {
    if "${validator}" "$1" "$2" >/dev/null 2>&1; then
        echo "Expected rejection: $2 -> $1" >&2
        exit 1
    fi
}

expect_pass develop feature/rbac
expect_pass develop fix/healthcheck
expect_pass develop dependabot/npm_and_yarn/frontend/update
expect_pass main develop
expect_fail main feature/rbac
expect_fail develop experimental/rbac
expect_fail release feature/rbac

echo "Branch flow tests passed."
