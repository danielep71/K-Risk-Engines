#!/usr/bin/env python3
"""Small, dependency-free checks for this static site (not a full HTML validator)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.stack, self.ids, self.links, self.errors = path, [], set(), [], []
        self.doctype = self.language = self.title = False

    def handle_decl(self, decl):
        self.doctype |= decl.lower() == 'doctype html'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if tag == 'html':
            self.language = bool(attrs.get('lang'))
        if tag == 'img' and 'alt' not in attrs:
            self.errors.append('Image missing alt attribute')
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.errors.append('Duplicate id: ' + attrs['id'])
            self.ids.add(attrs['id'])
        for attr in ('href', 'src'):
            if attr in attrs:
                self.links.append(attrs[attr])
        if tag == 'meta' and attrs.get('property') == 'og:image':
            self.links.append(attrs.get('content', ''))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append('Unexpected closing tag: ' + tag)
        else:
            self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1] == 'title' and data.strip():
            self.title = True


def check_external(url):
    # GET follows redirects; HEAD is rejected by some otherwise working sites.
    result = subprocess.run([
        'curl', '--silent', '--show-error', '--location', '--output', '/dev/null',
        '--write-out', '%{http_code}', '--connect-timeout', '10', '--max-time', '25',
        '--retry', '2', '--retry-delay', '2', '--proto', '=https,http',
        '--proto-redir', '=https,http', url
    ], capture_output=True, text=True, timeout=95)
    code = result.stdout.strip()
    if result.returncode or code in ('403', '429') or code.startswith('5'):
        return 'WARN', f'{url}: unavailable for verification (HTTP {code or "unknown"})'
    if not code.startswith('2'):
        return 'ERROR', f'{url}: HTTP {code}'
    return 'PASS', url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external', action='store_true')
    args = parser.parse_args()
    pages = {}
    errors, references = [], []
    for path in ROOT.rglob('*.html'):
        if any(part.startswith('.') for part in path.relative_to(ROOT).parts):
            continue
        page = Page(path)
        page.feed(path.read_text(encoding='utf-8'))
        page.close()
        pages[path.resolve()] = page
        problems = page.errors[:]
        if page.stack:
            problems.append('Unclosed tags: ' + ', '.join(page.stack))
        for name in ('doctype', 'language', 'title'):
            if not getattr(page, name):
                problems.append('Missing ' + name)
        errors.extend(f'{path.relative_to(ROOT)}: {problem}' for problem in problems)
        references.extend((path, link) for link in page.links)
    if not pages:
        errors.append('No HTML pages found')
    for path in (ROOT / 'assets').rglob('*.css'):
        references.extend((path, link.strip(' \"\'')) for link in
                          re.findall(r'url\(([^)]+)\)', path.read_text(encoding='utf-8')))
    external = set()
    for source, link in references:
        url = urlsplit(link)
        if url.scheme in ('http', 'https') or url.netloc:
            external.add(('https:' + link if link.startswith('//') else link).split('#')[0])
            continue
        if url.scheme in ('mailto', 'tel', 'data'):
            continue
        if url.scheme:
            errors.append(f'Unsupported URL scheme: {link}')
            continue
        if url.path.startswith('/'):
            errors.append(f'Root-relative URL breaks project Pages hosting: {link}')
            continue
        target = (source.parent / unquote(url.path)).resolve() if url.path else source.resolve()
        if not target.is_relative_to(ROOT):
            errors.append(f'Path outside site: {link}')
            continue
        if target.is_dir():
            target /= 'index.html'
        if not target.is_file():
            errors.append(f'{source.relative_to(ROOT)}: missing target {link}')
        elif target.stat().st_size == 0:
            errors.append(f'Empty target: {link}')
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f'{source.relative_to(ROOT)}: missing anchor {link}')
    if args.external:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for status, message in pool.map(check_external, sorted(external)):
                print(f'{status}: {message}')
                if status == 'ERROR':
                    errors.append(message)
    for error in errors:
        print('ERROR: ' + error)
    print(f'Checked {len(pages)} HTML page(s), {len(references)} references; {len(errors)} error(s).')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
