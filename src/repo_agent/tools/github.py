from __future__ import annotations

from typing import Any

import requests


class GitHubTool:
    API = "https://api.github.com"

    def __init__(self, token: str | None = None, max_readme_chars: int = 30000):
        self.max_readme_chars = max_readme_chars
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "long-running-context-engineering-demo"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.get(url, timeout=30, **kwargs)
        if response.status_code == 403:
            reset = response.headers.get("X-RateLimit-Reset")
            raise RuntimeError(f"GitHub API denied/rate-limited the request. reset={reset}; set GITHUB_TOKEN for a reliable conference demo.")
        response.raise_for_status()
        return response

    def search_alternatives(self, product: str, target: int) -> list[dict[str, Any]]:
        if target <= 0:
            return []
        # Search product metadata first; README mentions often return directories.
        queries = ['"API client" in:name,description stars:>20',
                   '"REST client" in:name,description stars:>20',
                   'topic:api-client stars:>20',
                   f'"{product} alternative" in:name,description']
        found: dict[str, dict[str, Any]] = {}
        for query in queries:
            response = self._get(f"{self.API}/search/repositories", params={
                "q": query, "sort": "stars", "order": "desc",
                "per_page": min(100, max(30, target))})
            for item in response.json().get("items", []):
                if candidate_relevance(item) > 0:
                    found[item["full_name"]] = item
        ranked = sorted(found.values(), key=lambda item: (
            candidate_relevance(item), item.get("stargazers_count", 0)), reverse=True)
        return ranked[:target]

    def read_readme(self, full_name: str) -> str:
        owner, repo = full_name.split("/", 1)
        headers = dict(self.session.headers)
        headers["Accept"] = "application/vnd.github.raw+json"
        response = self._get(f"{self.API}/repos/{owner}/{repo}/readme", headers=headers)
        return response.text[: self.max_readme_chars]

    def releases(self, full_name: str, n: int = 3) -> list[dict[str, Any]]:
        response = self._get(f"{self.API}/repos/{full_name}/releases", params={"per_page": n})
        return [{"tag_name": release.get("tag_name"), "published_at": release.get("published_at"), "name": release.get("name")} for release in response.json()[:n]]


    def file_map(self, full_name: str) -> list[str]:
        metadata = self._get(f"{self.API}/repos/{full_name}").json()
        branch = metadata["default_branch"]
        tree = self._get(f"{self.API}/repos/{full_name}/git/trees/{branch}",
                         params={"recursive": "1"}).json()
        return [item["path"] for item in tree.get("tree", [])
                if item.get("type") == "blob"]

    def read_file(self, full_name: str, path: str) -> str:
        headers = dict(self.session.headers)
        headers["Accept"] = "application/vnd.github.raw+json"
        response = self._get(f"{self.API}/repos/{full_name}/contents/{path}", headers=headers)
        return response.text[:self.max_readme_chars]


def candidate_relevance(item: dict[str, Any]) -> int:
    """Heuristic discovery filter, not proof of feature support."""
    name = item.get("full_name", "").lower()
    description = (item.get("description") or "").lower()
    text = name + " " + description
    if item.get("archived") or any(term in text for term in (
        "awesome", "curated list", "resource list", "collection of resources",
        "sample code", "code samples", "100-days", "free-resource")):
        return 0
    phrases = ("api client", "rest client", "postman alternative", "alternative to postman",
               "api testing", "api development", "http client", "api platform")
    score = sum(3 for phrase in phrases if phrase in text)
    topics = set(item.get("topics") or [])
    score += 2 * len(topics & {"api-client", "rest-client", "api-testing", "http-client"})
    return score
