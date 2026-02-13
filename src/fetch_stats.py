import json
import os
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()

GH_TOKEN = os.getenv("GH_TOKEN", None)


def run_query(query, variables=None):
    headers = {"Authorization": f"Bearer {GH_TOKEN}"}
    request = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            f"Query failed to run by returning code of {request.status_code}. {query}"
        )


def get_github_stats():
    query = """
    query {
        viewer {
        login
        name
        avatarUrl
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
            nodes {
            name
            stargazers {
                totalCount
            }
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                edges {
                size
                node {
                    name
                    color
                }
                }
            }
            }
        }
        contributionsCollection {
            totalCommitContributions
            totalPullRequestContributions
            totalIssueContributions
            contributionCalendar {
            totalContributions
            }
        }
        }
    }
    """

    result = run_query(query)
    data = result["data"]["viewer"]

    # processamento de dados

    total_stars = sum(
        repo["stargazers"]["totalCount"] for repo in data["repositories"]["nodes"]
    )

    language_stats = defaultdict(int)
    language_colors = {}

    for repo in data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            lang_name = edge["node"]["name"]
            size = edge["size"]
            color = edge["node"]["color"]

            language_stats[lang_name] += size
            language_colors[lang_name] = color

    total_bytes = sum(language_stats.values())
    top_languages = []

    sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]

    for lang, size in sorted_languages:
        percentage = (size / total_bytes) * 100 if total_bytes > 0 else 0
        top_languages.append(
            {"name": lang, "color": language_colors[lang], "percentage": percentage}
        )

    stats = {
        "username": data["login"],
        "name": data["name"] if data["name"] else data["login"],
        "avatar": data["avatarUrl"],
        "total_stars": total_stars,
        "total_commits": data["contributionsCollection"]["totalCommitContributions"],
        "total_prs": data["contributionsCollection"]["totalPullRequestContributions"],
        "total_issues": data["contributionsCollection"]["totalIssueContributions"],
        "total_contributions": data["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ],
        "top_languages": top_languages,
    }

    return stats


if __name__ == "__main__":
    try:
        print("Getting Github Stats...")
        stats = get_github_stats()

        print("Stats processed suceffuly:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))

        with open("stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
            print("Stats saved to stats.json")

    except Exception as e:
        print("Error fetching stats:", e)
