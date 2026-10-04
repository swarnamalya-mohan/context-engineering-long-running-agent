from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.pretty import Pretty

from repo_agent.config import Settings
from repo_agent.graph import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--thread-id", default="conference-demo")
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()
    console = Console(); settings = Settings.from_env(); graph = build_graph(settings=settings, repo_root=Path(args.repo_root)); config = {"configurable": {"thread_id": args.thread_id}}
    if args.stream:
        for update in graph.stream({}, config=config, stream_mode="updates"):
            console.rule("LangGraph update"); console.print(Pretty(update, max_depth=3))
        result = graph.get_state(config).values
    else:
        result = graph.invoke({}, config=config)
    console.rule("Final recommendation"); console.print(result.get("final_recommendation", "")); console.rule("Metrics"); console.print(Pretty(result.get("metrics", {})))


if __name__ == "__main__":
    main()
