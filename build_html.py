"""Generate the poetry ebook from four TXT files beside this script (Python 3.10+)."""

import html
from html.parser import HTMLParser
from pathlib import Path
import re


BOOK = '先秦漢魏晉南北朝詩'
SOURCES = (
    ('0', '出版說明.txt'),
    ('toc', '目次.txt'),
    ('1', f'{BOOK}.txt'),
    ('2', '後記.txt'),
)
DYNASTIES = ('先秦', '漢', '魏', '晉', '宋', '齊', '梁', '北魏', '北齊', '北周', '陳', '隋')
MARKERS = {'〔': ('〕', 'note'), '［': ('］', 'intro'), '＜': ('＞', 'bio'), '【': ('】', 'title')}
CITATION = re.compile(r'[ \t]*[○〇]')
VOLUME = re.compile(r'(?:先秦|漢|汉|魏|晉|晋|宋|齊|齐|梁|陳|陈|北魏|北齊|北齐|北周|隋)[詩诗]卷[一二三四五六七八九十百〇零]+')
PAGE = re.compile(r'〈[一二三四五六七八九十百千〇零○0-9]+〉')
FRONT_HEADINGS = {'先秦漢魏晉南北朝詩', '再版說明', '出版說明', '凡例', '引用書目', '後記', '目次', '先秦漢魏晉南北朝詩目次'}

# The reader script and fallback stylesheet travel with build.py.
READER = r"""const book = document.getElementById('book');
const markers = document.getElementById('markers');
const params = new URLSearchParams(location.search);
let saved = {};
try { saved = JSON.parse(localStorage.getItem('poetry-reader') || '{}'); } catch {}
let size = Number(params.get('size') || saved.size) || parseFloat(getComputedStyle(book).fontSize);
size = Math.max(12, Math.min(36, size));
let night = params.has('night') ? params.get('night') === '1' : Boolean(saved.night);
let showMarkers = params.has('markers') ? params.get('markers') !== '0' : saved.markers !== false;
let sidebarHidden = params.has('sidebar') ? params.get('sidebar') === '0'
  : typeof saved.sidebarHidden === 'boolean' ? saved.sidebarHidden : matchMedia('(max-width: 700px)').matches;
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const tocToggles = [...document.querySelectorAll('.toc-toggle')];
const expanded = new Set((params.has('toc') ? params.get('toc').split(',') : Array.isArray(saved.toc) ? saved.toc : []).filter(value => /^(?:[1-9]|1[0-2])$/.test(value)));
if (location.hash) {
  for (const toggle of tocToggles) {
    if (toggle.dataset.current === 'true') expanded.add(toggle.dataset.index);
  }
}
let marked = false;

function update() {
  book.style.fontSize = size + 'px';
  document.body.classList.toggle('night', night);
  document.getElementById('theme').textContent = night ? '日間' : '夜間';
  markers.checked = showMarkers;
  document.body.classList.toggle('sidebar-collapsed', sidebarHidden);
  sidebar.inert = sidebarHidden;
  sidebarToggle.setAttribute('aria-expanded', String(!sidebarHidden));
  sidebarToggle.setAttribute('aria-label', sidebarHidden ? '展開目錄' : '收起目錄');
  sidebarToggle.setAttribute('title', sidebarHidden ? '展開目錄' : '收起目錄');
  for (const toggle of tocToggles) {
    const open = expanded.has(toggle.dataset.index);
    toggle.textContent = open ? '-' : '+';
    toggle.setAttribute('aria-expanded', String(open));
    document.getElementById(toggle.getAttribute('aria-controls')).hidden = !open;
    toggle.setAttribute('aria-label', toggle.getAttribute('aria-label').replace(/^(展開|收起)/, open ? '收起' : '展開'));
  }
  if (!showMarkers && !marked) {
    const walker = document.createTreeWalker(book, NodeFilter.SHOW_TEXT), nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (!/[〔〕［］＜＞【】🟩]/u.test(node.data)) continue;
      const fragment = document.createDocumentFragment();
      for (const part of node.data.split(/([〔〕［］＜＞【】🟩])/u)) {
        if (/^[〔〕［］＜＞【】🟩]$/u.test(part)) {
          const span = document.createElement('span');
          span.className = 'marker';
          span.textContent = part;
          fragment.append(span);
        } else fragment.append(document.createTextNode(part));
      }
      node.replaceWith(fragment);
    }
    marked = true;
  }
  document.body.classList.toggle('hide-markers', !showMarkers);
  try { localStorage.setItem('poetry-reader', JSON.stringify({size, night, markers: showMarkers, sidebarHidden, toc: [...expanded]})); } catch {}
  // Carry preferences between local files even when file:// storage is isolated.
  for (const link of document.querySelectorAll('#toc a')) {
    const target = new URL(link.getAttribute('href'), location.href);
    target.search = target.pathname === location.pathname && target.hash ? location.search
      : new URLSearchParams({size: String(size), night: night ? '1' : '0', markers: showMarkers ? '1' : '0', sidebar: sidebarHidden ? '0' : '1', toc: [...expanded].join(',')}).toString();
    link.href = target.href;
  }
}
document.getElementById('smaller').onclick = () => { size = Math.max(12, size - 1); update(); };
document.getElementById('larger').onclick = () => { size = Math.min(36, size + 1); update(); };
document.getElementById('theme').onclick = () => { night = !night; update(); };
markers.onchange = () => { showMarkers = markers.checked; update(); };
sidebarToggle.onclick = () => { sidebarHidden = !sidebarHidden; update(); };
for (const toggle of tocToggles) {
  toggle.onclick = () => {
    const index = toggle.dataset.index;
    if (expanded.has(index)) expanded.delete(index);
    else expanded.add(index);
    update();
  };
}
update();
"""

DEFAULT_CSS = r"""/* 阅读配色：日间 / 夜间 */
:root {
  --sidebar-width: 240px;
  --sidebar-gap: 12px;
  --background: #fff;
  --text: #05021a;
  --panel: #f8f9fb;
  --border: #e1e4ea;
  --muted: #737a87;
  --title: #211df3;
  --intro: #069;
  --bio: #e65058;
  --note: #888;
  --citation: #b38ab3;
}
body.night {
  --background: #22251f;
  --text: #e0ddcf;
  --panel: #252b35;
  --border: #424956;
  --muted: #a2a9b5;
  --title: #9caaff;
  --intro: #83c4e8;
  --bio: #ff9292;
  --note: #a6a6a6;
  --citation: #c7a4c7;
}

/* 基础与阅读工具 */
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--background);
  color: var(--text);
  font-family: "中华书局宋体00平面", "宋体", "SimSun", serif;
  font-size: 16px;
}
a { color: var(--intro); text-decoration: none; }
a:hover { text-decoration: underline; }
button, input, select {
  font: 14px system-ui;
  color: var(--text);
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 5px;
}
button { padding: 6px 9px; cursor: pointer; }
input[type="checkbox"] { accent-color: var(--intro); }
button:hover { border-color: var(--intro); }
:focus-visible { outline: 2px solid var(--intro); outline-offset: 2px; }

/* 侧栏与版心 */
#sidebar {
  position: fixed;
  inset: var(--sidebar-gap) auto var(--sidebar-gap) var(--sidebar-gap);
  width: var(--sidebar-width);
  overflow: auto;
  padding: 54px 14px 24px;
  z-index: 2;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel);
  font: 14px/1.5 system-ui;
}
.book-name { font-size: 17px; font-weight: 700; margin-bottom: 5px; }
.book-credit { font-size: 13px; color: var(--muted); margin-bottom: 20px; }
.toolbar { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.marker-control { display: block; font-size: 13px; margin: 10px 0 16px; }
#query { width: 100%; padding: 9px; }
#kind { width: 100%; margin: 8px 0; padding: 6px; }
#status { font-size: 12px; color: var(--muted); margin: 5px 0; }
#toc a { display: block; padding: 5px 0; }
#toc .toc-row { display: flex; align-items: baseline; gap: 4px; }
#toc .toc-row > a { flex: 1; min-width: 0; }
#toc .toc-toggle {
  flex: 0 0 22px;
  width: 22px;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 18px;
  line-height: 1.5;
  text-align: center;
}
#toc .toc-plain { padding-left: 26px; }
#toc .toc-authors { margin: 0 0 6px 26px; padding-left: 10px; border-left: 1px solid var(--border); }
#toc .toc-authors a { font-size: 13px; overflow-wrap: anywhere; }
#toc .toc-empty { display: block; padding: 5px 0; color: var(--muted); font-size: 13px; }
#main { margin: 0 0 0 calc(var(--sidebar-width) + var(--sidebar-gap)); padding: 32px 24px 80px; }
.reading-column { max-width: 960px; margin: auto; }
#sidebar-toggle {
  position: fixed;
  top: calc(var(--sidebar-gap) + 10px);
  left: calc(var(--sidebar-gap) + var(--sidebar-width) - 50px);
  width: 38px;
  height: 38px;
  padding: 0;
  z-index: 3;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 5px;
  color: var(--text);
  background: transparent;
}
#sidebar-toggle:hover, #sidebar-toggle:focus-visible { color: var(--text); background: var(--border); }
#sidebar-toggle svg { display: block; }
#sidebar-toggle .sidebar-toggle-label { display: none; }
#sidebar-toggle .sidebar-icon-open { display: none; }
body.sidebar-collapsed #sidebar-toggle .sidebar-icon-close { display: none; }
body.sidebar-collapsed #sidebar-toggle .sidebar-icon-open { display: block; }
body.sidebar-collapsed #sidebar { transform: translateX(-100%); visibility: hidden; }
body.sidebar-collapsed #sidebar-toggle {
  left: var(--sidebar-gap);
  width: auto;
  min-width: 94px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 2px 6px rgb(0 0 0 / 8%);
}
body.sidebar-collapsed #sidebar-toggle .sidebar-toggle-label { display: inline; font-size: 15px; font-weight: 600; }
body.sidebar-collapsed #sidebar-toggle:hover, body.sidebar-collapsed #sidebar-toggle:focus-visible { background: var(--border); }
body.sidebar-collapsed #main { margin-left: 0; padding-top: 80px; }
#reader-info {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font: 12px/1.6 system-ui;
}

/* 正文与七类内容；原始换行和所有标记保留 */
#book {
  font-size: 16px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
#book .page {
  font-family: "中华书局宋体00平面", "宋体", "SimSun", serif;
  font-size: 1em;
  font-weight: 400;
  line-height: 1.6;
  letter-spacing: .08em;
}
#book h2 {
  margin: 0;
  text-align: center;
  font-size: 1.5em;
  font-weight: 400;
  font-family: "Microsoft JhengHei", "微软雅黑", sans-serif;
}
#book .author {
  color: var(--text);
  font-family: "Source Han Sans", "Microsoft YaHei", sans-serif;
  font-weight: 400;
}
#book .bio {
  color: var(--bio);
  font-family: "楷体", "KaiTi", "STKaiti", serif;
  font-size: .93em;
}
#book .title {
  color: var(--title);
  font-family: "Microsoft JhengHei", "微软雅黑", sans-serif;
  font-size: 1.2em;
  font-weight: 400;
}
#book .intro {
  color: var(--intro);
  font-family: "宋体", "SimSun", "Times New Roman", serif;
  font-size: .90em;
}
#book .note {
  color: var(--note);
  font-family: "宋体", "SimSun", "Times New Roman", serif;
  font-size: .75em;
}
#book .citation {
  color: var(--citation);
  font-family: "宋体", "SimSun", "Times New Roman", serif;
  font-size: .80em;
}
#book :is(.note, .intro, .bio, .citation) :is(.note, .intro, .bio, .citation) {
  font-size: 1em;
}
.hide-markers .marker { display: none; }

@media (max-width: 700px) {
  #main { padding: 52px 20px 60px; }
}
@media print {
  #sidebar, #sidebar-toggle, #reader-info { display: none; }
  #main { margin: 0; padding: 0; }
  body.sidebar-collapsed #main { padding: 0; }
  body.night { --background: #fff; --text: #05021a; }
}
""".replace("\n", "\r\n").encode("utf-8")


def render_lines(text, filename, base, warnings):
    """Pair editorial marks within a segment, then render their spans line by line."""
    stack = []
    starts = {}
    ends = set()
    for position, char in enumerate(text):
        pair = MARKERS.get(char)
        if char == '（':
            kind = 'citation' if CITATION.match(text, position + 1) else 'paren'
            pair = ('）', kind)
        if pair:
            stack.append((position, *pair))
        elif stack and char == stack[-1][1]:
            start, _, kind = stack.pop()
            if kind != 'paren':
                starts[start] = kind
                ends.add(position)
        elif char in '〕］＞】':
            warnings.append({'file': filename, 'offset': base + position,
                             'type': 'unmatched_closer', 'symbol': char})
    for position, _, kind in stack:
        if kind != 'paren':
            warnings.append({'file': filename, 'offset': base + position,
                             'type': 'unmatched_opener', 'symbol': text[position]})

    active = []
    offset = 0
    for line in text.splitlines(keepends=True):
        raw = line.rstrip('\r\n')
        pieces = [f'<span class="{kind}">' for kind in active]
        for position, char in enumerate(raw, offset):
            if position in starts:
                kind = starts[position]
                active.append(kind)
                pieces.append(f'<span class="{kind}">')
            pieces.append(html.escape(char))
            if position in ends:
                pieces.append('</span>')
                active.pop()
        pieces.extend('</span>' for _ in active)
        yield raw, ''.join(pieces)
        offset += len(line)


def is_heading(line, section):
    return VOLUME.fullmatch(line) or (section != '1' and line in FRONT_HEADINGS)


def segments(text, section):
    """Reopen inline spans across lines without breaking at page marker lines."""
    start = offset = 0
    for line in text.splitlines(keepends=True):
        raw = line.rstrip('\n')
        if offset > start and (raw.startswith(('🟩', '【')) or is_heading(raw, section)):
            yield start, text[start:offset]
            start = offset
        offset += len(line)
    if start < offset:
        yield start, text[start:offset]


def render_sections(sources):
    warnings = []
    sections = {}
    ident = 0
    for (section, filename), text in sources.items():
        rendered = []
        for base, segment in segments(text, section):
            for raw, content in render_lines(segment, filename, base, warnings):
                ident += 1
                if PAGE.fullmatch(raw):
                    content = f'<span class="page">{html.escape(raw)}</span>'
                elif is_heading(raw, section):
                    content = f'<h2 id="v{ident}">{content}</h2>'
                elif '🟩' in raw:
                    left, marker, right = content.partition('🟩')
                    content = f'{left}<b class="author" id="a{ident}">{marker}{right}</b>'
                rendered.append(content)
        sections[section] = '\n'.join(rendered) + ('\n' if text.endswith('\n') else '')
    return sections, warnings


def split_parts(sections):
    body = sections['1']
    names = '|'.join(DYNASTIES)
    headings = list(re.finditer(rf'<h2\b[^>]*>({names})詩卷一</h2>', body))
    if tuple(heading[1] for heading in headings) != DYNASTIES:
        raise ValueError('正文中十二个朝代的卷一标题缺失或顺序不符')
    starts = [0]
    for heading in headings[1:]:
        start = heading.start()
        page = re.search(rf'<span class="page">{PAGE.pattern}</span>\n\n$', body[:start])
        starts.append(page.start() if page else start)
    starts.append(len(body))
    chunks = [body[a:b] for a, b in zip(starts, starts[1:])]
    parts = [('00a', '前言', '0', sections['0']), ('00b', '目次', 'toc', sections['toc'])]
    parts.extend((f'{i:02d}', name + '詩', '1', chunk)
                 for i, (name, chunk) in enumerate(zip(DYNASTIES, chunks), start=1))
    parts.append(('13', '後記', '2', sections['2']))
    return parts



class AuthorIndex(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchor = None
        self.text = []
        self.rows = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'author' in a.get('class', '').split():
            self.anchor = a['id']
            self.text = []
    def handle_data(self, data):
        if self.anchor is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == 'b' and self.anchor is not None:
            full_label = ''.join(self.text).lstrip('🟩').strip()
            # Remove annotations while retaining any name characters after them
            # (e.g. 翾〔《詩紀》作翔。〕風 must remain 翾風 in the index).
            label = full_label
            previous = None
            while previous != label:
                previous = label
                label = re.sub(r'〔[^〔〕]*〕|＜[^＜＞]*＞|［[^［］]*］', '', label)
            label = label.strip()
            self.rows.append((self.anchor, label or full_label, full_label))
            self.anchor = None


def make_pages(parts):
    names = [f'{prefix}_{label}.html' for prefix, label, _, _ in parts]
    authors = []
    for _, _, _, content in parts:
        parser = AuthorIndex()
        parser.feed(content)
        authors.append(parser.rows)

    pages = {}
    for i, ((_, label, section_id, content), name) in enumerate(zip(parts, names)):
        contents = []
        for j, ((prefix, part_label, part_section, _), n) in enumerate(zip(parts, names)):
            link = f'<a href="{n}"' + (' aria-current="page"' if j == i else '') + '>' + (f'<strong>{part_label}</strong>' if j == i else part_label) + '</a>'
            if part_section == '1':
                dynasty_index = int(prefix)
                author_links = ''.join(f'<a href="{n}#{anchor}" title="{html.escape(full_label, quote=True)}">{html.escape(author_label)}</a>' for anchor, author_label, full_label in authors[j])
                if not author_links:
                    author_links = '<span class="toc-empty">未標作者</span>'
                contents.append(f'<div class="toc-dynasty"><div class="toc-row"><button type="button" class="toc-toggle" data-index="{dynasty_index}" data-current="{str(j == i).lower()}" aria-controls="toc-authors-{dynasty_index}" aria-expanded="false" aria-label="展開{part_label}作者目錄">+</button>' + link + f'</div><div id="toc-authors-{dynasty_index}" class="toc-authors" hidden>' + author_links + '</div></div>')
            else:
                contents.append('<div class="toc-plain">' + link + '</div>')
        contents = ''.join(contents)
        source_content = f'<section id="source-{section_id}">' + content + '</section>'
        pages[name] = ('<!doctype html>\n<html lang="zh-Hant"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>先秦漢魏晉南北朝詩 · {label}</title>'
            '<link rel="stylesheet" href="book.css"></head><body>'
            '<button id="sidebar-toggle" type="button" aria-controls="sidebar" aria-expanded="true" aria-label="收起目錄" title="收起目錄">'
            '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            '<path class="sidebar-icon-close" d="m7 7 10 10M17 7 7 17"/>'
            '<path class="sidebar-icon-open" d="M5 7h14M5 12h14M5 17h14"/></svg><span class="sidebar-toggle-label" aria-hidden="true">目錄</span></button>'
            '<aside id="sidebar"><div class="book-name">先秦漢魏晉南北朝詩</div>'
            '<div class="book-credit">逯欽立 輯校</div>'
            '<div class="toolbar"><button id="smaller" aria-label="縮小字體">字 −</button>'
            '<button id="larger" aria-label="放大字體">字 ＋</button>'
            '<button id="theme">夜間</button></div>'
            '<label class="marker-control"><input type="checkbox" id="markers" checked> 顯示標記</label>'
            '<nav id="toc" aria-label="目錄">' + contents + '</nav></aside>'
            '<main id="main"><div class="reading-column">'
            '<article id="book" class="book">'
            + source_content + '</article></div></main><script>' + READER + '</script></body></html>')

    entry = (
        '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{BOOK}</title><meta http-equiv="refresh" content="0;url={names[0]}"></head>'
        f'<body><a href="{names[0]}">{BOOK}</a></body></html>'
    )
    return {f'{BOOK}.html': entry, **pages}


class PageCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.section = None
        self.text = {}
        self.ids = set()
        self.links = []
        self.span_classes = []
        self.pages = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if ident := attributes.get('id'):
            assert ident not in self.ids, f'重复的 ID：{ident}'
            self.ids.add(ident)
        if tag == 'section':
            self.section = attributes['id'].removeprefix('source-')
            self.text[self.section] = []
        if tag == 'a':
            self.links.append(attributes['href'])
        if self.section is not None:
            classes = attributes.get('class', '').split()
            if tag == 'span':
                if 'page' in classes:
                    assert not self.span_classes, '页码被其他语义标签包住'
                self.span_classes.append(classes)

    def handle_endtag(self, tag):
        if self.section is not None and tag == 'span':
            self.span_classes.pop()
        if tag == 'section':
            self.section = None

    def handle_data(self, text):
        if self.section is not None:
            self.text[self.section].append(text)
            if self.span_classes and 'page' in self.span_classes[-1]:
                self.pages.append(text)


def verify_pages(pages, sources):
    checks = {}
    actual = {}
    page_numbers = []
    for name, markup in pages.items():
        check = PageCheck()
        check.feed(markup)
        check.close()
        assert '<style>' not in markup and ' style=' not in markup
        checks[name] = check
        for section, chunks in check.text.items():
            actual.setdefault(section, []).extend(chunks)
        page_numbers.extend(check.pages)
    assert list(actual) == [section for section, _ in sources]
    for (section, filename), text in sources.items():
        assert ''.join(actual[section]) == text, f'文字核对失败：{filename}'
    expected_pages = [line for text in sources.values() for line in text.splitlines() if PAGE.fullmatch(line)]
    assert page_numbers == expected_pages
    for name, check in checks.items():
        for href in check.links:
            target, _, anchor = href.partition('#')
            assert target or anchor, (name, href)
            assert (target or name) in checks, (name, href)
            if anchor:
                assert anchor in checks[target or name].ids, (name, href)
    return len(page_numbers)


def main():
    root = Path(__file__).resolve().parent
    out = root / f'{BOOK} HTML版'
    raw = {key: (root / key[1]).read_bytes() for key in SOURCES}
    sources = {key: data.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
               for key, data in raw.items()}
    css_path = out / 'book.css'
    css_existed = css_path.is_file()
    css = css_path.read_bytes() if css_existed else DEFAULT_CSS

    sections, warnings = render_sections(sources)
    pages = make_pages(split_parts(sections))
    page_count = verify_pages(pages, sources)
    assert all((root / key[1]).read_bytes() == data for key, data in raw.items())
    if css_existed:
        assert css_path.read_bytes() == css

    out.mkdir(exist_ok=True)
    if not css_existed:
        css_path.write_bytes(css)
    for name, markup in pages.items():
        (out / name).write_bytes(markup.encode('utf-8'))

    print(f'生成并核验完成：{out / (BOOK + ".html")}')
    print(f'{len(pages) - 1} 个分册，{page_count} 处页码。')
    if warnings:
        print(f'{len(warnings)} 处原文括号配对提示。')


if __name__ == '__main__':
    main()
