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
        queries = [f'"{product} alternative" in:readme', '"API client" in:name,description stars:>50', '"REST client" in:name,description stars:>50', 'topic:api-client stars:>20']
        found: dict[str, dict[str, Any]] = {}
        for query in queries:
            for page in range(1, 4):
                if len(found) >= target:
                    break
                response = self._get(f"{self.API}/search/repositories", params={"q": query, "sort": "stars", "order": "desc", "per_page": min(100, target), "page": page})
                items = response.json().get("items", [])
                if not items:
                    break
                for item in items:
                    found[item["full_name"]] = item
                    if len(found) >= target:
                        break
        return list(found.values())[:target]

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
