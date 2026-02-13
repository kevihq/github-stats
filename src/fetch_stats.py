import json
import os
import sys
import base64
from collections import defaultdict
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

GH_TOKEN = os.getenv("GH_TOKEN")


class GitHubAPIError(Exception):
    """Custom exception for GitHub API failures."""

    pass


def image_to_base64(url: str) -> str:
    """Downloads an image and converts it to base64 string."""
    if not url:
        return ""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        encoded = base64.b64encode(response.content).decode("utf-8")
        content_type = response.headers.get("content-type", "image/png")
        return f"data:{content_type};base64,{encoded}"
    except Exception as e:
        print(f"⚠️ Failed to convert avatar to base64: {e}")
        return url  # Fallback to original URL if conversion fails


def execute_graphql_query(
    query: str, variables: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    if not GH_TOKEN:
        raise GitHubAPIError("GH_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()

        payload = response.json()
        if "errors" in payload:
            raise GitHubAPIError(f"GraphQL Error: {payload['errors']}")

        return payload

    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Connection failed: {e}")


def fetch_user_metrics() -> Dict[str, Any]:
    query = """
    query {
      viewer {
        login
        name
        avatarUrl
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
          nodes {
            name
            stargazers { totalCount }
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          contributionCalendar { totalContributions }
        }
      }
    }
    """

    response = execute_graphql_query(query)
    viewer = response["data"]["viewer"]
    repos = viewer["repositories"]["nodes"]
    contributions = viewer["contributionsCollection"]

    # Aggregate statistics
    total_stars = sum(repo["stargazers"]["totalCount"] for repo in repos)

    # Calculate language distribution by byte size
    lang_bytes = defaultdict(int)
    lang_colors = {}

    for repo in repos:
        for edge in repo["languages"]["edges"]:
            node = edge["node"]
            lang_bytes[node["name"]] += edge["size"]
            lang_colors[node["name"]] = node["color"]

    total_bytes = sum(lang_bytes.values())

    # Format top 5 languages
    top_languages = []
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]

    for name, size in sorted_langs:
        percent = (size / total_bytes * 100) if total_bytes > 0 else 0
        top_languages.append(
            {
                "name": name,
                "color": lang_colors.get(name, "#ccc"),
                "percentage": percent,
            }
        )

    # Convert avatar to base64 for self-contained SVG
    avatar_b64 = image_to_base64(viewer["avatarUrl"])

    return {
        "username": viewer["login"],
        "name": viewer["name"] or viewer["login"],
        "avatar": avatar_b64,
        "total_stars": total_stars,
        "total_commits": contributions["totalCommitContributions"],
        "total_prs": contributions["totalPullRequestContributions"],
        "total_issues": contributions["totalIssueContributions"],
        "total_contributions": contributions["contributionCalendar"][
            "totalContributions"
        ],
        "top_languages": top_languages,
    }


def main():
    try:
        print("Fetching GitHub metrics...")
        stats = fetch_user_metrics()

        output_path = "stats.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"Metrics saved to {output_path}")

    except GitHubAPIError as e:
        print(f"API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
