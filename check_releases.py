import os
import requests
from packaging.version import parse as parse_version

REPOS = [
    "PedigreeAll/Pedigree-Vision-BE",
    "PedigreeAll/PedigreeVisionUI",
    "PedigreeAll/DigitreeModels",
]

GITHUB_API_BASE = "https://api.github.com/repos/"

def get_github_data(url, github_token):
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

def get_commit_sha_for_tag(repo, tag_name, github_token):
    try:
        ref_data = get_github_data(f"{GITHUB_API_BASE}{repo}/git/ref/tags/{tag_name}", github_token)
        object_type = ref_data['object']['type']
        object_sha = ref_data['object']['sha']

        if object_type == "commit":
            return object_sha
        elif object_type == "tag":
            tag_data = get_github_data(f"{GITHUB_API_BASE}{repo}/git/tags/{object_sha}", github_token)
            return tag_data['object']['sha']
    except requests.exceptions.RequestException as e:
        return "Could not resolve commit SHA"
    except KeyError:
        return "Could not resolve commit SHA"
    return "Could not resolve commit SHA"

def format_repo_info_md(repo, latest_version_tag_info, latest_release_info):
    output = f"## Repository: `{repo}`\n\n"
    output += "### Latest Tag (by version number)\n"
    if latest_version_tag_info:
        output += f"* **Tag:** `{latest_version_tag_info['tag']}`\n"
        output += f"* **Commit:** `{latest_version_tag_info['commit']}`\n"
        output += "* **Assets:**\n"
        output += f"  * [Zip](https://github.com/{repo}/archive/refs/tags/{latest_version_tag_info['tag']}.zip)\n"
        output += f"  * [Tar.gz](https://github.com/{repo}/archive/refs/tags/{latest_version_tag_info['tag']}.tar.gz)\n"
    else:
        output += "* No valid semantic version tag found.\n"

    output += "\n### Latest Release (by date)\n"
    if latest_release_info:
        release_name = latest_release_info['name'].replace('Release ', '')
        output += f"* **Release:** `{release_name}`\n"
        output += f"* **Tag:** `{latest_release_info['tag']}`\n"
        output += f"* **Commit:** `{latest_release_info['commit']}`\n"
        output += "* **Assets:**\n"
        output += f"  * [Zip](https://github.com/{repo}/archive/refs/tags/{latest_release_info['tag']}.zip)\n"
        output += f"  * [Tar.gz](https://github.com/{repo}/archive/refs/tags/{latest_release_info['tag']}.tar.gz)\n"
    else:
        output += "* No release found.\n"
    output += "\n"
    return output

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        exit(1)

    full_report = "# Release and Tag Report\n\n"

    for repo in REPOS:
        print(f"Processing {repo}...")
        latest_version_tag_info = None
        latest_release_info = None

        try:
            # --- Get Latest Tag (by version) ---
            tags_data = get_github_data(f"{GITHUB_API_BASE}{repo}/tags", github_token)
            valid_tags = []
            for tag in tags_data:
                try:
                    # Normalize tag name for parsing (remove 'v' or 'v.')
                    normalized_tag = tag['name'].lstrip('v').lstrip('.')
                    parsed_version = parse_version(normalized_tag)
                    valid_tags.append((parsed_version, tag['name'])) # Store original tag name
                except Exception as e:
                    continue

            if valid_tags:
                latest_version_tag_name = sorted(valid_tags, key=lambda x: x[0])[-1][1]
                commit_sha = get_commit_sha_for_tag(repo, latest_version_tag_name, github_token)
                latest_version_tag_info = {
                    "tag": latest_version_tag_name,
                    "commit": commit_sha
                }

            # --- Get Latest Release (by date) ---
            release_data = get_github_data(f"{GITHUB_API_BASE}{repo}/releases/latest", github_token)
            if release_data and 'tag_name' in release_data:
                commit_sha = get_commit_sha_for_tag(repo, release_data['tag_name'], github_token)
                latest_release_info = {
                    "name": release_data['name'],
                    "tag": release_data['tag_name'],
                    "commit": commit_sha
                }

        except requests.exceptions.RequestException as e:
            print(f"Error processing {repo}: {e}")
            # Continue to next repo even if one fails
            full_report += f"## Repository: `{repo}`\n\n"
            full_report += "### Error: Could not fetch data for this repository.\n\n"
            full_report += "--------------------------------------------------\n\n"
            continue
        except Exception as e:
            print(f"An unexpected error occurred for {repo}: {e}")
            full_report += f"## Repository: `{repo}`\n\n"
            full_report += "### Error: An unexpected error occurred.\n\n"
            full_report += "--------------------------------------------------\n\n"
            continue

        full_report += "--------------------------------------------------\n"
        full_report += format_repo_info_md(repo, latest_version_tag_info, latest_release_info)
        full_report += "==================================================\n\n"

    # Save the report
    with open("latest_report.md", "w") as f:
        f.write(full_report)
    print("Report generated: latest_report.md")

if __name__ == "__main__":
    main()
