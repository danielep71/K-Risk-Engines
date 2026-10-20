#!/usr/bin/env python3
"""Propose source-attributed portfolio updates. Never infer validation or execute source code."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'K-Risk-Engines-portfolio'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pages(path):
    result = []
    for page in range(1, 101):
        batch = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise ValueError('Pagination exceeded safe limit')


def plain(text):
    # Preserve link labels, sentences and caveats; render as escaped text, never source HTML.
    text = re.sub(r'\[([^\]]+)\]\([^\n]+?\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('**', '').replace('`', '')
    return ' '.join(text.split())


def status_excerpt(readme, selector):
    if selector == 'important':
        matches = re.findall(r'^> \[!IMPORTANT\]\n((?:>[^\n]*(?:\n|$))+)', readme, re.M)
        if len(matches) != 1:
            raise ValueError('Expected exactly one IMPORTANT status block')
        text = re.sub(r'^> ?', '', matches[0], flags=re.M)
    elif selector == 'status':
        matches = re.findall(r'^## [^\n]*\bStatus\s*\n(.*?)(?=^## |\Z)', readme, re.M | re.S)
        if len(matches) != 1:
            raise ValueError('Expected exactly one Status section')
        # Include the whole section so the draft-decay / missing Excel caveats cannot be lost.
        text = matches[0]
    elif selector == 'current':
        matches = re.findall(r'^\*\*Current status:[^\n]+', readme, re.M)
        if len(matches) != 1:
            raise ValueError('Expected exactly one Current status paragraph')
        text = matches[0]
    else:
        raise ValueError('Unknown selector')
    value = plain(text)
    if not 20 <= len(value) <= 6000:
        raise ValueError('Status excerpt length is unsafe; review source selector')
    return value


def file_at(repo, path, ref):
    data = api(f'repos/{repo}/contents/{urllib.parse.quote(path)}?ref={ref}')
    if data.get('encoding') != 'base64':
        raise ValueError('Expected a readable source file: ' + path)
    return base64.b64decode(data['content']).decode('utf-8')


def collect(project, old=None):
    repo = project['repo']
    meta = api('repos/' + repo)
    if meta['private']:
        raise ValueError('Portfolio sources must be public')
    repo = meta['full_name']
    branch = urllib.parse.quote(meta['default_branch'], safe='')
    head = api(f'repos/{repo}/commits/{branch}')['sha']
    sources = []
    readme = None
    for path in ['README.md'] + project['evidence']:
        content = file_at(repo, path, head)
        if path == 'README.md':
            readme = content
        sources.append({'path': path, 'sha256': hashlib.sha256(content.encode()).hexdigest(),
                        'url': f'https://github.com/{repo}/blob/{head}/{path}'})
    releases = [r for r in pages(f'repos/{repo}/releases') if not r['draft'] and not r['prerelease']]
    release = max(releases, key=lambda r: r['published_at']) if releases else None
    milestones = [{key: m[key] for key in ('number', 'title', 'state', 'open_issues', 'closed_issues', 'closed_at', 'html_url')}
                  for m in pages(f'repos/{repo}/milestones?state=all')]
    data = {'id': project['id'], 'repo': repo, 'status': status_excerpt(readme, project['selector']),
            'release': ({'tag': release['tag_name'], 'url': release['html_url'],
                         'published_at': release['published_at'],
                         'notes_sha256': hashlib.sha256((release['body'] or '').encode()).hexdigest()}
                        if release else None),
            'milestones': sorted(milestones, key=lambda m: m['number']), 'sources': sources}
    # A commit elsewhere in the source repository must not create a daily timestamp-only PR.
    def meaningful(item):
        item = json.loads(json.dumps(item))
        for source in item['sources']:
            source.pop('url', None)
        return item
    print('Collected ' + repo, flush=True)
    return old if old and meaningful(data) == meaningful(old) else data


def replace_block(text, key, value):
    start, end = f'<!-- portfolio:{key}:start -->', f'<!-- portfolio:{key}:end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Missing or duplicate generated markers: ' + key)
    before, rest = text.split(start)
    _, after = rest.split(end)
    return before + start + '\n' + value + '\n' + end + after


def markdown(text):
    return html.escape(text).replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;')


def latest_closed(milestones):
    closed = [m for m in milestones if m['state'] == 'closed' and m['closed_at']]
    return max(closed, key=lambda m: (m['closed_at'], m['number'])) if closed else None


def render(projects, snapshot, readme, website):
    rows = ['| Project | Purpose | Project-reported status | Last closed milestone |', '| --- | --- | --- | --- |']
    for p, data in zip(projects, snapshot):
        release = ('Latest published release: ' + data['release']['tag']) if data['release'] else 'No published stable release'
        url = 'https://github.com/' + data['repo']
        # Details retain the complete source status, including qualifications, without oversized cards.
        status = data['status']
        summary = re.split(r'(?<=[.!?])\s+', status, maxsplit=1)[0]
        source = data['sources'][0]['url']
        milestone = latest_closed(data['milestones'])
        milestone_md = (f"[{markdown(milestone['title'])}]({milestone['html_url']}) ({milestone['closed_at'][:10]})" if milestone else 'None recorded')
        rows.append(f"| [{p['name']}]({url}) | {p['purpose']} | {markdown(summary)} {markdown(release)}. [Full status and caveats](docs/PORTFOLIO_STATUS.md#{p['id']}) | {milestone_md} |")
        block = ('<p class="evidence"><strong>Project-reported status.</strong> ' + html.escape(summary) +
                 '</p><p class="asof">' + html.escape(release) +
                 '.</p><details><summary>Full status and limitations</summary><p>' +
                 html.escape(status) + '</p><p><a href="' + html.escape(source, quote=True) +
                 '">Read the source README ↗</a></p></details>')
        if milestone:
            block += ('<p class="asof">Last closed milestone: <a href="' + html.escape(milestone['html_url'], quote=True) + '">' +
                      html.escape(milestone['title']) + '</a> (' + milestone['closed_at'][:10] + ').</p>')
        else:
            block += '<p class="asof">Last closed milestone: none recorded.</p>'
        website = replace_block(website, p['id'], block)
    readme = replace_block(readme, 'table', '\n'.join(rows))
    report = ['# Portfolio status evidence', '',
              'Proposed automatically from public project sources; reviewed on merge. Release availability and milestone progress do not establish model validity.', '']
    for p, data in zip(projects, snapshot):
        report += [f'<a id="{p["id"]}"></a>', f'## {p["name"]}', '', markdown(data['status']), '',
                   '### Sources', '']
        report += [f'- [{s["path"]}]({s["url"]}) — content SHA-256 `{s["sha256"]}`' for s in data['sources']]
        if data['release']:
            r = data['release']
            report += [f'- Published release: [{markdown(r["tag"])}]({r["url"]}) ({r["published_at"]})']
        else:
            report += ['- No published stable release (drafts and prereleases excluded).']
        report += ['', '### Milestones (tracking only)', '']
        report += [f'- [{markdown(m["title"])}]({m["html_url"]}): {m["state"]}; {m["closed_issues"]} closed / {m["open_issues"]} open issues.' for m in data['milestones']] or ['- No milestones.']
        report += ['']
    return readme, website, '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--body-file', type=Path, required=True)
    parser.add_argument('--render-only', action='store_true', help='Render the stored snapshot without network access')
    args = parser.parse_args()
    projects = json.loads((ROOT / '.github/portfolio.json').read_text())['projects']
    snapshot_file = ROOT / 'docs/portfolio-state.json'
    old = json.loads(snapshot_file.read_text()) if snapshot_file.exists() else []
    by_id = {p['id']: p for p in old}
    # Collect every source before touching outputs. Any missing source / API error aborts the run.
    if args.render_only:
        if [p['id'] for p in projects] != [p['id'] for p in old]:
            raise ValueError('Stored snapshot does not match configured projects')
        snapshot = old
    else:
        with ThreadPoolExecutor(max_workers=4) as pool:
            snapshot = list(pool.map(lambda p: collect(p, by_id.get(p['id'])), projects))
    readme, website, report = render(projects, snapshot, (ROOT / 'README.md').read_text(), (ROOT / 'index.html').read_text())
    outputs = {'README.md': readme, 'index.html': website, 'docs/PORTFOLIO_STATUS.md': report,
               'docs/portfolio-state.json': json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n'}
    for path, content in outputs.items():
        (ROOT / path).write_text(content, encoding='utf-8')
    changed = [p['id'] for p in snapshot if p != by_id.get(p['id'])]
    body = ['Refresh the hub from explicit project documentation and release/milestone records.', '',
            'Changed source records: ' + (', '.join(changed) or 'none since the previous proposal') + '.', '',
            'Review the diff in `docs/PORTFOLIO_STATUS.md` for status wording, limitations and pinned evidence links.',
            'No engine files are changed. Milestone completion and CI are not treated as validation. No automatic merge.', '',
            'The refresh workflow runs its own HTML and external-link checks; downstream PR CI may require maintainer approval.', '']
    body += [f'- {p["name"]}: {data["sources"][0]["url"]}' for p, data in zip(projects, snapshot)]
    args.body_file.write_text('\n'.join(body) + '\n', encoding='utf-8')
    print(('Rendered stored snapshot' if args.render_only else 'Collected all configured repositories') + '; changed records: ' + ', '.join(changed))


if __name__ == '__main__':
    main()
