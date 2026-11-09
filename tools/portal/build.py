"""Stage a disposable portal, build both engines and preserve the static baseline.

No network, source execution, status inference or production deployment.
"""
from __future__ import annotations

import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build'
CONTENT = BUILD / 'portal-content'
DOMAINS = {'CCR': ('ccr', 'CCR_framework.svg'),
           'Market Risk': ('market-risk', 'Market_risk_framework.png'),
           'IRRBB': ('irrbb', 'IRRBB_framework.png'),
           'Liquidity': ('liquidity', 'Liquidity_framework.png')}
TOPICS = {'status': 'Status', 'release': 'Release', 'milestones': 'Milestones',
          'methodology': 'Methodology', 'validation': 'Validation',
          'excel-evidence': 'Excel evidence', 'limitations': 'Limitations'}


def write(path: str, text: str) -> None:
    target = CONTENT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text + '\n', encoding='utf-8')


def safe(value: str) -> str:
    # Quote upstream metadata as text: it must never inject HTML or Markdown links.
    return html.escape(value).replace('[', '&#91;').replace(']', '&#93;').replace('|', '&#124;')


def source_link(source: dict[str, str], record: dict[str, object]) -> str:
    return f"https://github.com/{record['repo']}/blob/{record['revision']}/{source['path']}"


def engine(project: dict, snapshot: dict, record: dict) -> None:
    pid = project['id']
    repo = 'https://github.com/' + project['repo']
    name = project['repo'].split('/')[1]
    prefix = f'engines/{pid}/'
    intro = (f'# {name}\n\n{safe(project["purpose"])}\n\n'
             f'[Source repository]({repo}) · [Live releases]({repo}/releases) · '
             f'[Live milestones]({repo}/milestones)\n\n'
             'This is a documentation gateway, not a validation certificate. '
             'Search covers gateway pages and the reviewed hub snapshot; linked engine documents '
             'remain in their source repository and are not indexed here.\n\n')
    write(prefix + 'index.md', intro + '\n'.join(f'- [{title}]({topic}.md)' for topic, title in TOPICS.items()))
    for topic, title in TOPICS.items():
        content = f'# {name}: {title}\n\n[Engine overview](index.md)\n\n'
        if topic == 'status':
            content += (f'{safe(snapshot["status"])}\n\n'
                        'Quoted from the committed portfolio snapshot, which may lag the live repository. '
                        'References to “this repository” belong to the engine.\n\n')
            content += '\n'.join(f'- [Captured source: {s["path"]}]({s["url"]})' for s in snapshot['sources'])
        elif topic == 'release':
            release = snapshot['release']
            content += (f'Captured release: [{safe(release["tag"])}]({release["url"]}). '
                        f'Published: {release["published_at"]}.\n\n' if release else
                        'No published release was recorded in this snapshot.\n\n')
            content += f'[Check current releases]({repo}/releases). Availability is not evidence of validation.'
        elif topic == 'milestones':
            content += f'[Current milestones]({repo}/milestones)\n\n'
            for m in snapshot['milestones']:
                label = safe(m['title'])
                link = f'[{label}]({m["html_url"]})' if m.get('html_url') else label
                content += f'- {link}: {m["state"]}; {m["open_issues"]} open, {m["closed_issues"]} closed issues (snapshot).\n'
            content += '\nIssue counts do not establish delivery or model validity.'
        else:
            source = record['documents'][topic]
            content += f'Document location audited on {record["audited_on"]}; revision `{record["revision"]}`.\n\n'
            if source:
                content += (f'[Read the authoritative {title.lower()} document]({source_link(source, record)}).\n\n'
                            f'Content SHA-256: `{source["sha256"]}`.\n\n')
            else:
                content += f'No dedicated Excel evidence document was selected in this audit. [Inspect the source repository]({repo}). This is not a claim that no evidence exists.\n\n'
            content += {'methodology': 'Read scope, applicability and assumptions before using any result.',
                        'validation': 'A test specification or validation plan is not an executed validation result.',
                        'excel-evidence': 'Only a dated host execution record can substantiate an Excel run. Static CI checks are insufficient.',
                        'limitations': 'Read the complete source README and methodology for material caveats; the hub does not summarize them away.'}[topic]
        content += '\n\nSnapshot provenance: see the [portfolio evidence](../../portfolio-status.md).'
        write(prefix + topic + '.md', content)


def stage() -> None:
    if CONTENT.exists():
        shutil.rmtree(CONTENT)
    projects = json.loads((ROOT / '.github/portfolio.json').read_text())['projects']
    snapshots = {p['id']: p for p in json.loads((ROOT / 'docs/portfolio-state.json').read_text())}
    records = json.loads((ROOT / 'tools/portal/sources.json').read_text())
    assert set(records) == set(snapshots) == {p['id'] for p in projects}
    for p in projects:
        assert p['repo'] == records[p['id']]['repo'] == snapshots[p['id']]['repo']
        engine(p, snapshots[p['id']], records[p['id']])
    write('index.md', '# K-Risk Engines\n\n## Documentation pilot\n\n'
          'Explore the methodology, validation evidence and limitations behind each engine. '
          'This preview does not replace the [production portfolio](https://danielep71.github.io/K-Risk-Engines/).\n\n'
          + '\n'.join(f'- [{name}](domains/{slug}.md)' for name, (slug, _) in DOMAINS.items())
          + '\n\n[Portfolio status and provenance](portfolio-status.md) · [Compatibility specimen](compatibility.md)\n\n'
          'The source repositories own their documentation and releases. '
          'This portal generates navigation from one manifest and the existing reviewed snapshot; '
          'it does not maintain a second set of engine documentation.\n\n'
          'Release availability, milestone closure and passing CI do not establish independent validation '
          'or production readiness. Snapshot and source-document revisions can differ; each is identified explicitly.')
    for name, (slug, asset) in DOMAINS.items():
        write(f'domains/{slug}.md', f'# {name}\n\n'
              + '\n'.join(f'- [{p["repo"].split("/")[1]}](../engines/{p["id"]}/index.md)' for p in projects if records[p['id']]['domain'] == name)
              + f'\n\n![{name} framework](../assets/{asset})\n\n'
              'Architecture overview only; not a statement of implemented or validated coverage.')
    shutil.copytree(ROOT / 'assets', CONTENT / 'assets', ignore=shutil.ignore_patterns('*.md', '*.css'))
    (CONTENT / 'assets/portal.css').write_text('.md-typeset img {height:auto;max-width:100%}\n.md-typeset a {overflow-wrap:anywhere}\n')
    # Byte-for-byte reuse: no second editable copy of the existing Markdown.
    shutil.copyfile(ROOT / 'docs/PORTFOLIO_STATUS.md', CONTENT / 'portfolio-status.md')
    write('compatibility.md', '# Compatibility specimen\n\n'
          'This page exercises shared Markdown, search, diagrams and local artwork.\n\n'
          '!!! note "Evidence matters"\n    A release is not a validation certificate.\n\n'
          '| Feature | Sample |\n| --- | --- |\n| Search | K-SACCR validation |\n| Markdown | **Strong** and `code` |\n\n'
          '```mermaid\nflowchart TD\n  S[Source repositories] --> M[Reviewed manifest]\n  S --> E[Evidence snapshot]\n  M --> P[Disposable portal]\n  E --> P\n  P --> A[Material build]\n  P --> B[Zensical build]\n```\n\n'
          '![CCR SVG](assets/CCR_framework.svg)\n\n![Liquidity PNG](assets/Liquidity_framework.png)')
    provenance = {'hub_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  'snapshot_sha256': hashlib.sha256((ROOT / 'docs/portfolio-state.json').read_bytes()).hexdigest(),
                  'snapshot_commit_date': subprocess.check_output(['git', 'log', '-1', '--format=%cI', '--', 'docs/portfolio-state.json'], cwd=ROOT, text=True).strip()}
    write('provenance.json', json.dumps(provenance, indent=2))
    # Visible date is the hub commit date, not a newly asserted source observation date.
    with (CONTENT / 'index.md').open('a') as stream:
        stream.write(f'\nSnapshot last committed: {provenance["snapshot_commit_date"]}. [Build provenance](provenance.json).\n')


def main() -> None:
    stage()
    for builder in ('mkdocs', 'zensical'):
        subprocess.run([builder, 'build', '--strict', '-f', 'mkdocs.yml'], cwd=ROOT, check=True)
        target = BUILD / builder
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(BUILD / 'site'), target)
    # Package all tracked existing paths unchanged, with an additive documentation prefix.
    baseline = BUILD / 'baseline'
    if baseline.exists():
        shutil.rmtree(baseline)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, tracked):
        target = baseline / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    for builder in ('mkdocs', 'zensical'):
        destination = BUILD / ('pages-' + builder)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(baseline, destination)
        shutil.copytree(BUILD / builder, destination / 'documentation')
    print('Both builds and additive Pages candidates are ready; nothing was published.')


if __name__ == '__main__':
    main()
