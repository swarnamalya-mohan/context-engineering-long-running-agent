"""Useful decision output even when the current policy has no finalists."""
from collections import Counter


def decision_report(state: dict, limit: int = 5) -> str:
    records = [{**record, 'full_name': record.get('full_name', name)}
               for name, record in {**state.get('candidates', {}), **state.get('rejected', {})}.items()]
    counts = Counter(r.get('status', 'unknown') for r in records)
    eligible = [r for r in records if r.get('status') == 'evaluated' and r.get('analysis')]
    reviewed = [r for r in records if r.get('analysis')]
    lines = [f"Policy stage: {' + '.join(state.get('policy', {}).get('applied_changes', [])) or 'base'}",
             f"Discovered: {len(records)} | Reviewed: {len(reviewed)} | Verified eligible: {len(eligible)}",
             'Statuses: ' + (', '.join(f'{key}={value}' for key, value in sorted(counts.items())) or 'none')]
    if eligible:
        lines.append('\nVerified shortlist under this policy:')
        for r in sorted(eligible, key=lambda r: r.get('score') or 0, reverse=True)[:limit]:
            lines.append(f"- {r['full_name']} — score={r.get('score')}; license={r.get('license')}")
    else:
        lines.append('\nNo verified candidates satisfy the current policy.')
    blocked = [r for r in reviewed if r.get('status') == 'rejected']
    if blocked:
        lines.append('\nHighest-scoring reviewed candidates that remain ineligible (scores do not override requirements):')
        for r in sorted(blocked, key=lambda r: r.get('score') or 0, reverse=True)[:limit]:
            lines.append(f"- {r['full_name']} — score={r.get('score')}; " + '; '.join(r.get('rejection_reasons', [])))
    pending = [r for r in records if r.get('status') in {'screened', 'discovered', 'review_failed', 'stale', 'reopened'}]
    if pending:
        lines.append('\nNot verified under the current policy:')
        for r in pending[:limit]:
            lines.append(f"- {r['full_name']} — {r.get('status')}" +
                         (f"; {r['review_error']}" if r.get('review_error') else ''))
        if len(pending) > limit:
            lines.append(f"- {len(pending) - limit} more await review.")
    if not records:
        lines.append('Discovery returned no repositories; check queries and GitHub access.')
    return '\n'.join(lines)
