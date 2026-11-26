"""Reserva con dimensiones reales para rótulos y su primer bloque.

Conserva los comandos de título, sus contadores, destinos e índice; añade una
medición invisible y una petición condicional de espacio antes del bloque.
"""
import re

HEAD = re.compile(r'\\(?P<level>section|subsection|subsubsection|paragraph)\{(?P<title>(?:[^{}\n]|\\[{}]|\{[^{}\n]*\})*)\}')
TABLE = re.compile(r'\\begingroup\n\\fontsize\{10\}\{12\.5\}\\selectfont\n[\s\S]*?\\end\{longtable\}\n\\endgroup')
FORBIDDEN = re.compile(r'\\(?:begin\{(?:enumerate|itemize|longtable)|end\{longtable|pantalla|diagramasistema|IfFileExists|chapter|input)')

def _title_style(level):
    if level == 'section':
        return r'\RaggedRight\sffamily\bfseries\large\color{Azul}'
    if level == 'subsection':
        return r'\sffamily\bfseries\normalsize\color{Teal}'
    if level == 'subsubsection':
        return r'\sffamily\bfseries\normalsize\color{Azul}'
    return r'\normalfont\normalsize\bfseries'

def _intro_for_measurement(intro):
    intro = re.sub(r'\\label\{[^\n]*\}\n?', '', intro)
    intro = re.sub(r'\\Needspace\{[^\n]*\}\n?', '', intro)
    intro = HEAD.sub(lambda m: '\\par\\vspace{6pt}\\noindent\\textbf{' + m['title'] + '}\\hspace{0.5em}' if m['level'] == 'paragraph' else m[0], intro)
    return intro

def reserve_longtable_titles(text):
    insertions, edits = [], []
    headings = list(HEAD.finditer(text))
    for table_match in TABLE.finditer(text):
        candidates = [h for h in headings if h.end() <= table_match.start()]
        chosen = None
        for h in reversed(candidates):
            intro = text[h.end():table_match.start()]
            if len(intro) > 2600 or FORBIDDEN.search(intro):
                break
            if any(x['level'] != 'paragraph' for x in HEAD.finditer(intro)):
                break
            chosen = h
            if h['level'] != 'paragraph':
                break
        if chosen is None:
            continue
        intro = text[chosen.end():table_match.start()]
        if FORBIDDEN.search(intro):
            continue
        block = table_match.group()
        preamble, body = block.split('\\begin{longtable}', 1)
        spec, tail = body.split('\n', 1)
        headers = tail.split('\\toprule\n', 1)[1].split('\\midrule\n', 1)[0]
        first = tail.split('\\endlastfoot\n', 1)[1].split('\\addlinespace', 1)[0]
        table_settings = preamble.removeprefix('\\begingroup\n')
        measure = (
            '\\begingroup\n\\setbox0=\\vbox{\\hsize=\\linewidth\n'
            '{\\normalfont\\normalsize' + _title_style(chosen['level'])
            + '\\hyphenpenalty=10000\\exhyphenpenalty=10000 '
            + chosen['title'] + '\\par}\n'
            + _intro_for_measurement(intro) + '\\par\n\\begingroup\n'
            + table_settings + '\\begin{tabular}' + spec + '\n\\toprule\n'
            + headers + '\\midrule\n' + first
            + '\\bottomrule\n\\end{tabular}\n\\endgroup\n}\n'
            '\\Needspace{\\dimexpr\\ht0+\\dp0+48pt\\relax}\n\\endgroup\n'
        )
        insertions.append((chosen.start(), measure))
        edits.append({'type': 'table', 'level': chosen['level'], 'title': chosen['title']})
    for h in headings:
        if h['level'] != 'paragraph':
            continue
        tail = text[h.end():]
        m = re.match(r'[\s]*\\begin\{itemize\}\n\\item ([\s\S]*?)(?=\n\\item |\n\\end\{itemize\})', tail)
        if not m:
            continue
        measure = (
            '\\begingroup\n\\setbox0=\\vbox{\\hsize=\\linewidth\n'
            '{\\normalfont\\normalsize\\bfseries ' + h['title'] + '\\par}\n'
            '\\begin{itemize}\n\\item ' + m[1]
            + '\n\\end{itemize}\n}\n'
            '\\Needspace{\\dimexpr\\ht0+\\dp0+24pt\\relax}\n\\endgroup\n'
        )
        insertions.append((h.start(), measure))
        edits.append({'type': 'list', 'level': h['level'], 'title': h['title']})
    for pos, value in sorted(insertions, reverse=True):
        text = text[:pos] + value + text[pos:]
    return text, edits
