#!/usr/bin/env python3
"""Small, dependency-free checks for this static site and its Markdown docs (not a full HTML validator)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
FENCE = re.compile(r' {0,3}(`{3,}|~{3,})')
ATTRIBUTE = r'\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'=<>`]+))'


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


def github_slug(heading):
    """Anchor GitHub generates for a Markdown heading (before duplicate suffixes)."""
    text = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', heading)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def heading_anchor(slug, used):
    """Make a heading slug unique the way GitHub does: -1, -2... until unused."""
    anchor = slug
    while anchor in used:
        used[slug] += 1
        anchor = f'{slug}-{used[slug]}'
    used[anchor] = 0
    return anchor


def inline_destinations(line):
    """Destinations of [text](destination "title"), allowing <...> and balanced parentheses."""
    found = []
    for match in re.finditer(r'\]\(', line):
        rest = line[match.end():].lstrip()
        if rest.startswith('<'):
            end = rest.find('>')
            if end > 1:
                found.append(rest[1:end])
            continue
        depth, destination = 0, ''
        for char in rest:
            if char.isspace() or (char == ')' and depth == 0):
                break
            depth += {'(': 1, ')': -1}.get(char, 0)
            destination += char
        if destination:
            found.append(destination)
    return found


def markdown_links(text):
    """Return (links, anchors) of a Markdown document, ignoring fenced and inline code."""
    links, anchors, used, fence = [], set(), {}, None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        heading = re.match(r' {0,3}#{1,6}\s+(.*?)(?:\s+#+)?\s*$', line)
        if heading:
            anchors.add(heading_anchor(github_slug(heading.group(1)), used))
        line = re.sub(r'(`+).*?\1', '', line)
        anchors.update(''.join(value) for value in
                       re.findall(r'<a\s[^>]*?(?<![\w-])(?:id|name)' + ATTRIBUTE, line))
        links += inline_destinations(line)
        links += [''.join(value) for value in
                  re.findall(r'^ {0,3}\[(?!\^)[^\]]+\]:\s*(?:<([^>]*)>|(\S+))', line)]
        links += re.findall(r'<(https?://[^>\s]+)>', line)
        links += [''.join(value) for value in re.findall(r'(?<![\w-])(?:href|src)' + ATTRIBUTE, line)]
    return links, anchors


def tracked_markdown(root):
    try:
        names = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--', '*.md'],
                               capture_output=True, text=True, check=True).stdout.split('\0')
        return [root / name for name in names if name]
    except (OSError, subprocess.CalledProcessError):
        return [path for path in root.rglob('*.md') if '.git' not in path.relative_to(root).parts]


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


def check(root=ROOT):
    """Return (errors, external URLs, HTML page count, Markdown file count, reference count)."""
    pages, anchors = {}, {}
    errors, references = [], []
    for path in root.rglob('*.html'):
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        page = Page(path)
        page.feed(path.read_text(encoding='utf-8'))
        page.close()
        pages[path.resolve()] = page
        anchors[path.resolve()] = page.ids
        problems = page.errors[:]
        if page.stack:
            problems.append('Unclosed tags: ' + ', '.join(page.stack))
        for name in ('doctype', 'language', 'title'):
            if not getattr(page, name):
                problems.append('Missing ' + name)
        errors.extend(f'{path.relative_to(root)}: {problem}' for problem in problems)
        references.extend((path, link) for link in page.links)
    if not pages:
        errors.append('No HTML pages found')
    markdown = tracked_markdown(root)
    for path in markdown:
        links, anchors[path.resolve()] = markdown_links(path.read_text(encoding='utf-8'))
        references.extend((path, link) for link in links)
    for path in (root / 'assets').rglob('*.css'):
        references.extend((path, link.strip(' \"\'')) for link in
                          re.findall(r'url\(([^)]+)\)', path.read_text(encoding='utf-8')))
    external = set()
    for source, link in references:
        url = urlsplit(link)
        where = source.relative_to(root)
        if url.scheme in ('http', 'https') or url.netloc:
            external.add(('https:' + link if link.startswith('//') else link).split('#')[0])
            continue
        if url.scheme in ('mailto', 'tel', 'data'):
            continue
        if url.scheme:
            errors.append(f'{where}: unsupported URL scheme: {link}')
            continue
        if url.path.startswith('/'):
            errors.append(f'{where}: root-relative URL breaks project Pages hosting: {link}')
            continue
        target = (source.parent / unquote(url.path)).resolve() if url.path else source.resolve()
        if not target.is_relative_to(root.resolve()):
            errors.append(f'{where}: path outside repository: {link}')
            continue
        if target.is_dir() and source.suffix == '.html':
            target /= 'index.html'
        if not target.exists():
            errors.append(f'{where}: missing target {link}')
        elif target.is_file() and target.stat().st_size == 0:
            errors.append(f'{where}: empty target {link}')
        elif url.fragment and target in anchors and unquote(url.fragment) not in anchors[target]:
            errors.append(f'{where}: missing anchor {link}')
    return errors, external, len(pages), len(markdown), len(references)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external', action='store_true')
    args = parser.parse_args(argv)
    errors, external, pages, markdown, references = check()
    if args.external:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for status, message in pool.map(check_external, sorted(external)):
                print(f'{status}: {message}')
                if status == 'ERROR':
                    errors.append(message)
    for error in errors:
        print('ERROR: ' + error)
    print(f'Checked {pages} HTML page(s), {markdown} Markdown file(s), {references} references; '
          f'{len(errors)} error(s).')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
