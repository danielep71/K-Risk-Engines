"""Fail on broken built links, URL drift, unsupported configuration or stale names."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

import yaml

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build'
OBSOLETE = re.compile(r'K-SA-CCR|K-SFT(?!s|[\w-])|K-CCP(?:\b)|/releases/tag/v1\.1\.0(?=["\s])')


class Page(HTMLParser):
    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(str(values['id']))
        self.links.extend(str(values[a]) for a in ('href', 'src') if values.get(a))


def inspect(site: Path) -> dict[str, Page]:
    pages = {str(p.relative_to(site)): Page(p.read_text()) for p in site.rglob('*.html')}
    errors = []
    for name, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (site / name).parent / unquote(url.path) if url.path else site / name
            if url.path.startswith('/'):
                prefix = '/K-Risk-Engines/documentation/'
                if not url.path.startswith(prefix):
                    errors.append(f'{name}: unexpected absolute path {link}')
                    continue
                target = site / unquote(url.path.removeprefix(prefix))
            if target.is_dir():
                target /= 'index.html'
            target = target.resolve()
            if not target.is_relative_to(site.resolve()) or not target.is_file():
                errors.append(f'{name}: missing target {link}')
                continue
            key = str(target.relative_to(site.resolve()))
            if url.fragment and key in pages and unquote(url.fragment) not in pages[key].ids:
                errors.append(f'{name}: missing anchor {link}')
    if errors:
        raise ValueError('\n'.join(errors[:30]))
    return pages


def config_check() -> None:
    # BaseLoader reads the explicitly trusted shared config without executing YAML tags.
    cfg = yaml.load((ROOT / 'mkdocs.yml').read_text(), Loader=yaml.BaseLoader)
    if cfg.get('plugins') != ['search'] or 'hooks' in cfg or 'custom_dir' in cfg['theme']:
        raise ValueError('The portal supports search only; no hooks or template overrides')
    expected = {'admonition', 'attr_list', 'md_in_html', 'tables', 'toc', 'pymdownx.details', 'pymdownx.superfences'}
    extensions = {x if isinstance(x, str) else next(iter(x)) for x in cfg['markdown_extensions']}
    if extensions != expected or (ROOT / 'zensical.toml').exists():
        raise ValueError('Review compatibility before changing extensions or configuration format')


def verify_sources() -> None:
    records = json.loads((ROOT / 'tools/portal/sources.json').read_text())
    checks = {(r['repo'], r['revision'], d['path'], d['sha256'])
              for r in records.values() for d in r['documents'].values() if d}

    def verify(item: tuple[str, str, str, str]) -> None:
        repo, sha, path, digest = item
        url = f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
        with urlopen(url, timeout=30) as response:
            actual = hashlib.sha256(response.read()).hexdigest()
        if actual != digest:
            raise ValueError('Source digest mismatch: ' + url)
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(verify, checks))
    print(f'{len(checks)} immutable source documents verified remotely')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--external', action='store_true')
    args = parser.parse_args()
    config_check()
    counts = {}
    for builder in ('mkdocs', 'zensical'):
        pages = inspect(BUILD / builder)
        counts[builder] = len(pages)
        for path in (BUILD / 'baseline').rglob('*'):
            if path.is_file():
                candidate = BUILD / ('pages-' + builder) / path.relative_to(BUILD / 'baseline')
                if not candidate.is_file() or candidate.read_bytes() != path.read_bytes():
                    raise ValueError('Existing URL changed: ' + str(path))
    first = inspect(BUILD / 'mkdocs')
    second = inspect(BUILD / 'zensical')
    if first.keys() != second.keys():
        raise ValueError('Builder page URL inventories differ')
    # Theme-owned anchors may differ. Every author-owned content heading must survive.
    for path in (BUILD / 'portal-content').rglob('*.md'):
        if path.name == 'portfolio-status.md':
            continue  # Immutable historical quotations can name older releases.
        if OBSOLETE.search(path.read_text()):
            raise ValueError('Obsolete reference in generated gateway: ' + str(path))
    if (BUILD / 'portal-content/portfolio-status.md').read_bytes() != (ROOT / 'docs/PORTFOLIO_STATUS.md').read_bytes():
        raise ValueError('Portfolio Markdown must be reused without editing')
    if args.external:
        verify_sources()
    report = {'pages': counts, 'page_urls': sorted(first),
              'legacy_files_unchanged': True, 'source_digests_checked_online': args.external}
    (BUILD / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'page_urls'}))


if __name__ == '__main__':
    main()
