#!/bin/bash

# --- Configuration ---
# List of repositories to check
REPOS=(
    "PedigreeAll/Pedigree-Vision-BE"
    "PedigreeAll/PedigreeVisionUI"
)

# --- Script Logic ---

# Check if gh CLI is installed
if ! command -v gh &> /dev/null
then
    echo "gh CLI could not be found. Please install it: https://cli.github.com/"
    exit 1
fi

# Function to fetch the latest tag for a repo
get_latest_tag() {
    local repo=$1
    local latest_tag=""

    # Fetch all tags and filter for vX.Y.Z format, then sort and get the latest
    local all_tags
    all_tags=$(gh api repos/"$repo"/tags --jq '.[].name' 2>/dev/null)

    if [[ -n "$all_tags" ]]; then
        latest_tag=$(echo "$all_tags" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1)
    fi

    if [[ -z "$latest_tag" ]]; then
        echo "No vX.Y.Z tags found for $repo" >&2
        echo "ERROR"
    else
        echo "$latest_tag"
    fi
}

# Fetch latest tags for all repos
echo "Fetching latest tags..."
latest_tags_output=""
for repo in "${REPOS[@]}"; do
    tag=$(get_latest_tag "$repo")
    if [[ "$tag" == "ERROR" ]]; then
        exit 1
    fi
    latest_tags_output+="$repo: $tag\n"
done

echo "Copying Content in version.txt"
printf "$latest_tags_output" > version.txt
