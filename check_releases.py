import os
import requests
import json
from packaging.version import parse as parse_version

REPOS = [
    "PedigreeAll/Pedigree-Vision-BE",
    "PedigreeAll/PedigreeVisionUI",
    "PedigreeAll/DigitreeModels",
]

GITHUB_API_BASE = "https://api.github.com/repos/"
OUTPUT_DIR = "output"

def get_github_data(url, github_token):
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_commit_sha_for_tag(repo, tag_name, github_token):
    """Resolve annotated or lightweight tag to actual commit SHA"""
    try:
        ref_data = get_github_data(f"{GITHUB_API_BASE}{repo}/git/ref/tags/{tag_name}", github_token)
        obj = ref_data.get('object', {})
        if obj.get('type') == "commit":
            return obj.get('sha')
        elif obj.get('type') == "tag":
            tag_data = get_github_data(obj.get('url'), github_token)
            return tag_data.get('object', {}).get('sha')
    except Exception as e:
        print(f"  Warning: Could not resolve commit SHA for tag {tag_name}. Error: {e}")
    return "unknown"

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for repo in REPOS:
        repo_name_only = repo.split('/')[1]
        print(f"--- Processing Repository: {repo} ---")

        latest_release_info = {}
        latest_tag_info = {}

        try:
            # Get LATEST FORMAL RELEASE
            release_data = get_github_data(f"{GITHUB_API_BASE}{repo}/releases/latest", github_token)
            if release_data:
                release_tag = release_data['tag_name']
                commit_sha = get_commit_sha_for_tag(repo, release_tag, github_token)
                latest_release_info = {
                    "release_name": release_data.get('name') or release_tag,
                    "tag_name": release_tag,
                    "commit_sha": commit_sha,
                    "published_at": release_data.get('published_at'),
                    "release_notes": release_data.get('body')
                }
                print(f"  Latest Release: '{latest_release_info['release_name']}' (Commit: {commit_sha})")
            else:
                print("  No formal releases found.")

            # Get LATEST TAG BY SEMANTIC VERSION
            tags_data = get_github_data(f"{GITHUB_API_BASE}{repo}/tags", github_token)
            highest_version = parse_version("0.0.0")
            latest_tag_obj = None

            for tag in tags_data:
                version_str = tag.get('name', '0.0.0').lstrip('v').lstrip('.')
                current_version = parse_version(version_str)
                if current_version > highest_version:
                    highest_version = current_version
                    latest_tag_obj = tag

            if latest_tag_obj:
                tag_name = latest_tag_obj['name']
                tag_commit_sha = get_commit_sha_for_tag(repo, tag_name, github_token)
                latest_tag_info = {
                    "tag_name": tag_name,
                    "commit_sha": tag_commit_sha
                }
                print(f"  Latest Tag:     '{tag_name}' (Commit: {tag_commit_sha})")
            else:
                print("  No valid semantic version tags found.")

            # Combine
            combined_data = {
                "repository": repo,
                "latest_release": latest_release_info,
                "latest_tag": latest_tag_info
            }

            version_tag = latest_release_info.get("tag_name", "latest").replace(".", "_")
            versioned_filename = f"{version_tag}.json"
            versioned_html = f"{version_tag}.html"

            repo_output_dir = os.path.join(OUTPUT_DIR, repo_name_only)
            os.makedirs(repo_output_dir, exist_ok=True)

            # Write JSON
            json_filepath = os.path.join(repo_output_dir, versioned_filename)
            with open(json_filepath, 'w') as f:
                json.dump(combined_data, f, indent=4)
            print(f"  Generated: {json_filepath}")

            # Write HTML
            html_content = f"""
            <!DOCTYPE html><html lang="en">
            <head><title>Latest Info for {repo}</title><style>body{{font-family:sans-serif;margin:40px;}}h2{{border-bottom:1px solid #ccc;}}code{{background:#f4f4f4;padding:2px 6px;}}</style></head>
            <body>
                <h1>Status Report for <code>{repo}</code></h1>
                <h2>Latest Formal Release</h2>
                {'<ul>' + '<li><strong>Release Name:</strong> <code>' + latest_release_info.get('release_name', 'N/A') + '</code></li>' + '<li><strong>Tag:</strong> <code>' + latest_release_info.get('tag_name', 'N/A') + '</code></li>' + '<li><strong>Commit SHA:</strong> <code>' + latest_release_info.get('commit_sha', 'N/A') + '</code></li>' + '</ul>' if latest_release_info else '<p>No formal release found.</p>'}
                
                <h2>Latest Tag by Version</h2>
                {'<ul>' + '<li><strong>Tag:</strong> <code>' + latest_tag_info.get('tag_name', 'N/A') + '</code></li>' + '<li><strong>Commit SHA:</strong> <code>' + latest_tag_info.get('commit_sha', 'N/A') + '</code></li>' + '</ul>' if latest_tag_info else '<p>No valid semantic version tag found.</p>'}
            </body></html>
            """

            html_filepath = os.path.join(repo_output_dir, versioned_html)
            with open(html_filepath, 'w') as f:
                f.write(html_content)
            print(f"  Generated: {html_filepath}")

        except Exception as e:
            print(f"An unexpected error occurred for {repo}: {e}")

if __name__ == "__main__":
    main()
