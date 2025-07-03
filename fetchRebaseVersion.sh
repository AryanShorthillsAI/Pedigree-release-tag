#!/bin/bash
 
# --- Configuration ---
# List of repositories to check
REPOS=(
    "PedigreeAll/Pedigree-Vision-BE"
    "PedigreeAll/PedigreeVisionUI"
    "PedigreeAll/DigitreeModels"
)
 
# --- Script Logic ---
 
# Function to fetch the latest release info and construct asset URLs
get_latest_release_info() {
    local repo=$1
 
    # IMPORTANT: Use a GITHUB_TOKEN environment variable for security
    local GITHUB_TOKEN="${GITHUB_TOKEN}"
 
    # Check if curl and jq are installed
    if ! command -v curl &> /dev/null; then echo "Error: curl is not installed." >&2; echo "ERROR"; return; fi
    if ! command -v jq &> /dev/null; then echo "Error: jq is not installed." >&2; echo "ERROR"; return; fi
 
    # Fetch the latest release information
    local release_json
    release_json=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$repo/releases/latest")
 
    # Check for API errors
    if echo "$release_json" | jq -e '.message' > /dev/null; then
        echo "Error fetching release for $repo: $(echo $release_json | jq -r .message)" >&2
        echo "ERROR"
        return
    fi
 
    # Extract release name and tag name
    local release_name
    release_name=$(echo "$release_json" | jq -r '.name')
    local tag_name
    tag_name=$(echo "$release_json" | jq -r '.tag_name')
 
    if [[ -z "$release_name" ]]; then echo "No release name found for $repo" >&2; echo "ERROR"; return; fi
    if [[ -z "$tag_name" ]]; then echo "No tag name found for $repo" >&2; echo "ERROR"; return; fi
 
    # Construct the asset URLs based on the tag
    local zip_url="https://github.com/${repo}/archive/refs/tags/${tag_name}.zip"
    local tar_url="https://github.com/${repo}/archive/refs/tags/${tag_name}.tar.gz"
 
    # Format the output
    local formatted_assets=""
    formatted_assets+="\n      - ${zip_url}"
    formatted_assets+="\n      - ${tar_url}"
 
    echo -e "tag: $tag_name, release: $release_name, assets:$formatted_assets"
}
 
# --- Main Script ---
 
echo "Fetching latest release information..."
latest_output=""
for repo in "${REPOS[@]}"; do
    info=$(get_latest_release_info "$repo")
    if [[ "$info" == "ERROR" ]]; then
        exit 1
    fi
    latest_output+="$repo:\n  $info\n"
done
 
echo "Copying Content in version.txt"
printf "$latest_output" > version.txt