#!/bin/bash

# --- Configuration ---
# List of repositories to check
REPOS=(
    "PedigreeAll/Pedigree-Vision-BE"
    "PedigreeAll/PedigreeVisionUI"
)

# --- Script Logic ---

# Function to fetch the latest tag for a repo using curl and jq
get_latest_tag() {
    local repo=$1
    local latest_tag=""

    # Fetch all tags using curl and parse with jq
    # IMPORTANT: Replace YOUR_GITHUB_TOKEN with your actual Personal Access Token
    # You can generate a PAT at https://github.com/settings/tokens
    # Make sure it has at least 'public_repo' scope if checking public repos,
    # or 'repo' scope for private repos.
    local GITHUB_TOKEN="${GITHUB_TOKEN}" # Consider using environment variables for security

    # Check if curl and jq are installed
    if ! command -v curl &> /dev/null; then
        echo "Error: curl is not installed. Please install it." >&2
        echo "ERROR"
        return
    fi
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is not installed. Please install it." >&2
        echo "ERROR"
        return
    fi

    all_tags=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$repo/tags" | jq -r '.[].name')

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

# Find the latest existing tag file (R1.txt, R2.txt, etc.)
latest_file=$(ls -v R*.txt 2>/dev/null | tail -n 1)

# If no tag file exists, create R1.txt
if [ -z "$latest_file" ]; then
    echo "No existing tag file found. Creating R1.txt..."
    printf "$latest_tags_output" > R1.txt
    echo "R1.txt created with the latest tags."
    exit 0
fi

# Compare with the latest existing file
echo "Comparing with latest file: $latest_file"

# Write current latest tags to a temporary file for robust comparison
temp_file=$(mktemp)
printf "%b" "$latest_tags_output" > "$temp_file"

# Compare using diff -q
if diff -q "$temp_file" "$latest_file" >/dev/null; then
    echo "No new tags found. Everything is up-to-date."
    rm "$temp_file" # Clean up temporary file
    exit 0
else
    echo "New tags found. Creating a new tag file."
    # Determine the next file number
    file_number=$(echo "$latest_file" | sed -e 's/R//' -e 's/.txt//')
    next_file_number=$((file_number + 1))
    new_file="R${next_file_number}.txt"

    printf "%b" "$latest_tags_output" > "$new_file"
    echo "$new_file created with the new tags."
    rm "$temp_file" # Clean up temporary file
fi