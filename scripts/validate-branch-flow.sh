#!/bin/sh
set -eu

base_branch="${1:-}"
head_branch="${2:-}"

if [ -z "${base_branch}" ] || [ -z "${head_branch}" ]; then
    echo "Usage: validate-branch-flow.sh BASE_BRANCH HEAD_BRANCH" >&2
    exit 2
fi

case "${base_branch}" in
    main)
        if [ "${head_branch}" != "develop" ]; then
            echo "Pull requests to main must originate from develop." >&2
            exit 1
        fi
        ;;
    develop)
        case "${head_branch}" in
            feature/* | fix/* | docs/* | chore/* | hotfix/* | dependabot/* | main)
                ;;
            *)
                echo "Branch ${head_branch} does not follow the integration naming policy." >&2
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Pull requests must target develop or main." >&2
        exit 1
        ;;
esac

echo "Branch flow accepted: ${head_branch} -> ${base_branch}"
