#!/usr/bin/env python3
"""Create the two manuals from editorial JSON and NEW complete-view screenshots.

Run only with bundled Python. The coordinating author must run the document-skill
operation marker immediately before the first authoring invocation.

Examples (paths relative to this file unless explicitly absolute):
  python crear_manuales.py --check --only universidad --capture-map mapeo_capturas.json
  python crear_manuales.py --only ambos --capture-map mapeo_capturas.json --render-pages

--check creates no DOCX/PDF. --docx-only writes an internal first-layout draft in
qa/build, not a delivery. The regular build creates a native updateable TOC, exports
through BUNDLED LibreOffice, derives actual heading page numbers from the PDF,
rebuilds until the index is stable, and keeps provenance/geometry in qa.
The final visual QA is a human review of EVERY rendered page, never an automatic
claim that the manual was operationally tested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any
from zipfile import ZipFile

BASE = Path(__file__).resolve().parent
RUNTIME = Path('/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies')
PYTHON = RUNTIME / 'python/bin/python3'
SOFFICE = RUNTIME / 'bin/override/soffice'
RENDERER = Path('/home/ceo/.codex/plugins/cache/openai-primary-runtime/documents/26.1104.11149/skills/documents/render_docx.py')
DEFAULT_ARCHITECTURE = Path('/home/ceo/Documentos/ChatGPT/Tesis 2026 CII/capitulo3-revision-ejemplos-20261106/arquitectura/Arquitectura_general_BI_IA.png')
FONT = 'Liberation Sans'
BLACK = '000000'
ACCENT = '24445E'

# One compact screenshot per listed stage. Architecture is one additional page.
# Logical keys remain internal production metadata and are not printed.
COMPACT_GROUPS = [
    ('Comenzar y reconocer responsabilidades', [3, 4, 5], []),
    ('Preparar las fuentes y la inteligencia artificial', [6, 7, 8], ['conexiones', 'llm_configuraciones']),
    ('Leer esquemas y relaciones', [10, 11], ['esquema_adventureworks', 'esquema_wideworldimporters']),
    ('Definir el catálogo analítico', [12, 13, 14], ['catalogo_preguntas']),
    ('Expresar la necesidad y comprobar su viabilidad', [15, 16], ['asistente_necesidad', 'asistente_viabilidad', 'asistente_conceptos']),
    ('Revisar el modelo y aprobar la propuesta', [17, 18], ['asistente_propuesta', 'asistente_personalizacion', 'asistente_aprobacion']),
    ('Seleccionar y materializar el datamart', [19, 20], ['etl_elegir_propuesta', 'etl_indicadores', 'etl_confirmacion', 'etl_materializacion']),
    ('Conciliar los datos y revisar las etiquetas', [21], ['etl_conciliacion']),
    ('Leer los indicadores y los gráficos', [22, 23, 24], []),
    ('Conversar y exportar los resultados', [25, 26], ['copiloto_aw', 'exportacion_panel']),
    ('Demostrar el caso AdventureWorks', [27, 28, 29], ['caso_aw_panel_filtrado']),
    ('Demostrar el caso WideWorldImporters', [30, 31, 32], ['caso_wwi_panel_filtrado']),
    ('Administrar y resolver problemas', [9, 33, 34, 35], []),
]
assert sum(len(g[2]) for g in COMPACT_GROUPS) == 20

ALIASES = {
    'acceso': ['login'],
    'inicio_adventureworks': ['inicio_aw', 'home_aw'],
    'inicio_wideworldimporters': ['inicio_wwi', 'home_wwi'],
    'conexiones': ['conexiones_listado', 'connections_list', 'connections'],
    'conexion_formulario': ['conexiones_formulario', 'connection_form'],
    'esquema_adventureworks': ['esquema_aw', 'schema_aw'],
    'esquema_wideworldimporters': ['esquema_wwi', 'schema_wwi'],
    'esquema_relaciones_aw': ['esquema_aw_relaciones', 'schema_aw_detail'],
    'esquema_relaciones_wwi': ['esquema_wwi_relaciones', 'schema_wwi_detail'],
    'catalogo_preguntas': ['catalogo_aw_preguntas', 'catalog_questions'],
    'asistente_necesidad': ['assistant_need'],
    'asistente_viabilidad': ['assistant_viability'],
    'asistente_conceptos': ['assistant_concepts'],
    'asistente_propuesta': ['assistant_proposal'],
    'asistente_personalizacion': ['assistant_personalization'],
    'asistente_aprobacion': ['assistant_review', 'assistant_approval'],
    'etl_elegir_propuesta': ['etl_select', 'etl_proposal'],
    'etl_indicadores': ['etl_indicators', 'etl_kpis'],
    'etl_confirmacion': ['etl_confirmation'],
    'etl_materializacion': ['etl_materialize'],
    'etl_conciliacion': ['etl_reconciliation'],
    'caso_aw_panel_filtrado': ['analytics_aw_filtered', 'analitica_aw_filtros'],
    'caso_wwi_panel_filtrado': ['analytics_wwi_filtered', 'analitica_wwi_filtros'],
    'copiloto_aw': ['analytics_aw_copilot', 'copilot_aw'],
    'exportacion_panel': ['analytics_export', 'export_panel'],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise ValueError(f'Falta el archivo requerido: {path}')
    return json.loads(path.read_text(encoding='utf8'))


def text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    return str(value)


def texts(value: Any) -> list[str]:
    if value is None:
        return []
    return [text(v) for v in (value if isinstance(value, list) else [value]) if text(v)]


def heading_text(value: Any) -> str:
    # The user's labels remain exact in procedures; editorial headings use words.
    cleaned = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', text(value).replace('_', ' '), flags=re.UNICODE)).strip()
    return cleaned[:1].upper() + cleaned[1:]


class CaptureResolver:
    def __init__(self, manifest: Path, capture_map: Path | None, architecture: Path):
        self.manifest_path = manifest.resolve()
        self.root = self.manifest_path.parent.resolve()
        data = load_json(self.manifest_path)
        items = data if isinstance(data, list) else data.get('captures', data.get('capturas', data.get('items', [])))
        self.records: dict[str, dict] = {}
        for item in items:
            key = text(item.get('key', item.get('capture_key', item.get('id'))))
            if not key:
                raise ValueError('Hay una captura sin key en el manifiesto.')
            if key in self.records:
                raise ValueError(f'Clave repetida en el manifiesto: {key}')
            self.records[key] = item
        self.config = load_json(capture_map) if capture_map else {}
        self.mapping = self.config.get('aliases', self.config.get('mapeo', self.config))
        self.architecture = architecture.resolve()
        self.used: dict[str, dict] = {}

    def resolve(self, key: str) -> dict:
        mapped = self.mapping.get(key, key)
        if isinstance(mapped, dict):
            mapped = mapped.get('key', mapped.get('target', mapped.get('capture_key', key)))
        candidates = [mapped, key, *ALIASES.get(key, [])]
        # Aliases are symmetric so formation and compact can share the new image.
        for original, variants in ALIASES.items():
            if key == original or key in variants:
                candidates.extend([original, *variants])
        record = next((self.records[k] for k in candidates if isinstance(k, str) and k in self.records), None)
        if record is None:
            raise ValueError(f'Falta captura requerida para {key}. Añádala al manifiesto o al mapeo externo.')
        raw = record.get('path', record.get('file', record.get('archivo')))
        if not raw:
            raise ValueError(f'La captura {key} no tiene path.')
        path = Path(raw)
        path = (self.root / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f'Imagen fuera del directorio de capturas NUEVAS: {key} → {path}')
        if not path.is_file() or path.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
            raise ValueError(f'Imagen ausente o formato no admitido para {key}: {path}')
        if record.get('full_viewport') is not True:
            raise ValueError(f'La captura {key} no acredita full_viewport=true; no se admiten recortes.')
        checksum = sha(path)
        declared = record.get('sha256', record.get('sha'))
        if declared and declared != checksum:
            raise ValueError(f'Cambió la captura después de su registro: {key}')
        result = {**record, 'path': str(path), 'logical_key': key, 'sha256': checksum,
                  'title': text(self.config.get('captions', {}).get(record.get('key'), self.config.get('captions', {}).get(key, record.get('title', record.get('titulo', 'Pantalla del sistema')))))}
        self.used[key] = result
        return result

    def diagram(self) -> dict:
        if not self.architecture.is_file():
            raise ValueError(f'Falta la arquitectura nueva requerida: {self.architecture}')
        if self.architecture.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
            raise ValueError('Exporte la arquitectura nueva como PNG o JPEG para insertarla sin alterarla.')
        result = {'logical_key': 'arquitectura_general', 'key': 'arquitectura_general',
                  'title': 'Cómo funciona la plataforma de ventas con IA',
                  'path': str(self.architecture), 'sha256': sha(self.architecture), 'kind': 'diagram',
                  'note': 'El origen se consulta en modo de sólo lectura; el contrato, la revisión humana y la conciliación controlan el paso al análisis.'}
        self.used['arquitectura_general'] = result
        return result


def input_capture_keys(data: dict, kind: str) -> list[str]:
    if kind == 'universidad':
        return [key for _, _, keys in COMPACT_GROUPS for key in keys]
    keys = []
    for unit in data['unidades']:
        for step in unit.get('pasos', []):
            if step.get('capture_key'):
                keys.append(step['capture_key'])
        keys.extend(texts(unit.get('capture_keys')))
    return list(dict.fromkeys(keys))


def validate_inputs(args, resolver, datasets) -> dict:
    errors = []
    for kind, data in datasets.items():
        if kind == 'universidad' and len(data.get('fichas', [])) != 35:
            errors.append('El contenido universitario debe contener las 35 fichas editoriales.')
        if kind == 'formacion' and not data.get('unidades'):
            errors.append('El contenido de formación no contiene unidades.')
        keys = input_capture_keys(data, kind)
        if kind == 'universidad' and resolver.config.get('university_figures'):
            chosen = {}
            for row in resolver.config['university_figures']:
                chosen.setdefault(row['after_group'], []).append(row['key'])
            keys = [key for n, (_, _, defaults) in enumerate(COMPACT_GROUPS, 1) for key in chosen.get(n, defaults)]
        for key in keys:
            try:
                resolver.resolve(key)
            except ValueError as exc:
                errors.append(str(exc))
    try:
        resolver.diagram()
    except ValueError as exc:
        errors.append(str(exc))
    return {'valido': not errors, 'errores': list(dict.fromkeys(errors)),
            'capturas_resueltas': sorted(resolver.used), 'manifest': str(resolver.manifest_path),
            'imagenes_alteradas': False, 'interfaz_probada_por_generador': False}


# Imported only after --check. This script itself creates no document on import.
def authoring_imports():
    global Document, Inches, Pt, RGBColor, WD_ORIENT, WD_SECTION, WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, OxmlElement, qn
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.section import WD_ORIENT, WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn


def set_fonts(style, points=11.5, bold=False, italic=False):
    style.font.name = FONT
    style.font.size = Pt(points)
    style.font.bold = bold
    style.font.italic = italic
    style.font.color.rgb = RGBColor.from_string(BLACK)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts'); rpr.insert(0, fonts)
    for attr in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
        fonts.set(qn('w:' + attr), FONT)
    for attr in ['asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme']:
        fonts.attrib.pop(qn('w:' + attr), None)


def field(paragraph, instruction, cached=''):
    begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = instruction
    separate = OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'), 'separate')
    end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
    for el in [begin, instr, separate]: paragraph.add_run()._r.append(el)
    paragraph.add_run(cached)
    paragraph.add_run()._r.append(end)


class Book:
    def __init__(self, title: str, compact=False):
        self.doc = Document()
        self.title = heading_text(title)
        self.compact = compact
        self.orientation = 'portrait'
        self.headings: list[tuple[str, str]] = []
        self.figure_count = 0
        self.media: list[dict] = []
        self.bookmark_count = 1
        styles = self.doc.styles
        # Remove template title rules; typography and whitespace carry hierarchy.
        for border in list(styles.element.xpath('.//w:pBdr')):
            border.getparent().remove(border)
        from docx.enum.style import WD_STYLE_TYPE
        for name in ['Procedure', 'FigureOrientation', 'ManualNote', 'ContentsTitle', 'TOC 1']:
            if name not in styles: styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        set_fonts(styles['Normal'], 11.0 if compact else 11.5)
        p = styles['Normal'].paragraph_format
        p.line_spacing = 1.04 if compact else 1.10
        p.space_after = Pt(4 if compact else 6)
        p.widow_control = True
        for name, size in [('Title', 25), ('Subtitle', 13), ('Heading 1', 17), ('Heading 2', 12), ('Heading 3', 11.5)]:
            set_fonts(styles[name], size, name != 'Subtitle')
            fmt = styles[name].paragraph_format
            fmt.space_before = Pt(11 if name.startswith('Heading') else 0)
            fmt.space_after = Pt(5 if name.startswith('Heading') else 12)
            fmt.keep_with_next = True; fmt.keep_together = True
        for name in ['Caption', 'FigureOrientation', 'ManualNote']:
            set_fonts(styles[name], 9.5 if name != 'ManualNote' else 10.0)
            styles[name].paragraph_format.line_spacing = 1.0
            styles[name].paragraph_format.space_after = Pt(4)
        set_fonts(styles['ContentsTitle'], 20, True)
        styles['ContentsTitle'].paragraph_format.space_after = Pt(12)
        set_fonts(styles['Procedure'], 11 if compact else 11.5)
        styles['Procedure'].paragraph_format.line_spacing = 1.02 if compact else 1.07
        styles['Procedure'].paragraph_format.space_after = Pt(3 if compact else 5)
        styles['Procedure'].paragraph_format.widow_control = True
        set_fonts(styles['TOC 1'], 11)
        styles['TOC 1'].paragraph_format.space_after = Pt(6)
        styles['TOC 1'].paragraph_format.line_spacing = 1.05
        self.set_geometry(self.doc.sections[0], 'portrait')
        for style in [styles['Header'], styles['Footer']]: set_fonts(style, 9)
        self.doc.sections[0].header.paragraphs[0].text = 'Plataforma de datamarts de ventas'
        footer = self.doc.sections[0].footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        field(footer, 'PAGE', '1')
        settings = self.doc.settings.element
        upd = OxmlElement('w:updateFields'); upd.set(qn('w:val'), 'false'); settings.append(upd)
        lang = OxmlElement('w:themeFontLang'); lang.set(qn('w:val'), 'es-EC'); settings.append(lang)
        self.doc.core_properties.title = self.title
        self.doc.core_properties.subject = 'Operación supervisada y aprendizaje de la plataforma de ventas'
        self.doc.core_properties.author = 'Proyecto BI'
        self.doc.core_properties.keywords = 'Manual de usuario, ventas, inteligencia de negocios, aprendizaje'

    def set_geometry(self, section, orientation):
        if orientation == 'landscape':
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width, section.page_height = Inches(11), Inches(8.5)
            section.top_margin = section.bottom_margin = Inches(.45)
            section.left_margin = section.right_margin = Inches(.55)
        else:
            section.orientation = WD_ORIENT.PORTRAIT
            section.page_width, section.page_height = Inches(8.5), Inches(11)
            section.top_margin = section.bottom_margin = Inches(.65)
            section.left_margin = section.right_margin = Inches(.70)
        section.header_distance = section.footer_distance = Inches(.25)
        # A single continuous Arabic sequence across portrait/landscape sections.
        pg = section._sectPr.find(qn('w:pgNumType'))
        if pg is not None: section._sectPr.remove(pg)

    def start_page(self, orientation='portrait'):
        if orientation != self.orientation:
            section = self.doc.add_section(WD_SECTION.NEW_PAGE)
            self.set_geometry(section, orientation)
            self.orientation = orientation
        else:
            self.doc.add_page_break()

    def paragraph(self, value: str, style=None, lead=None):
        p = self.doc.add_paragraph(style=style)
        if lead: p.add_run(lead + ' ').bold = True
        p.add_run(text(value))
        return p

    def heading(self, value: str, level=1):
        title = heading_text(value)
        p = self.doc.add_paragraph(title, style=f'Heading {level}')
        if level == 1:
            anchor = f'chapter_{len(self.headings) + 1:03d}'
            start = OxmlElement('w:bookmarkStart'); start.set(qn('w:id'), str(self.bookmark_count)); start.set(qn('w:name'), anchor)
            end = OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'), str(self.bookmark_count))
            p._p.insert(0, start); p._p.append(end)
            self.bookmark_count += 1
            self.headings.append((title, anchor))
        return p

    def procedure(self, actions: list[str], start_number=1):
        if not actions: return
        numbering = self.doc.part.numbering_part.element
        abstracts = [int(el.get(qn('w:abstractNumId'))) for el in numbering.findall(qn('w:abstractNum'))]
        nums = [int(el.get(qn('w:numId'))) for el in numbering.findall(qn('w:num'))]
        aid, nid = max(abstracts + [0]) + 1, max(nums + [0]) + 1
        abstract = OxmlElement('w:abstractNum'); abstract.set(qn('w:abstractNumId'), str(aid))
        lvl = OxmlElement('w:lvl'); lvl.set(qn('w:ilvl'), '0')
        for tag, value in [('start', str(start_number)), ('numFmt', 'decimal'), ('lvlText', '%1.'), ('lvlJc', 'left')]:
            e = OxmlElement('w:' + tag); e.set(qn('w:val'), value); lvl.append(e)
        pp = OxmlElement('w:pPr'); ind = OxmlElement('w:ind'); ind.set(qn('w:left'), '300'); ind.set(qn('w:hanging'), '300'); pp.append(ind); lvl.append(pp)
        abstract.append(lvl); numbering.append(abstract)
        num = OxmlElement('w:num'); num.set(qn('w:numId'), str(nid))
        ref = OxmlElement('w:abstractNumId'); ref.set(qn('w:val'), str(aid)); num.append(ref); numbering.append(num)
        for action in actions:
            p = self.paragraph(action, 'Procedure')
            props = p._p.get_or_add_pPr(); npr = OxmlElement('w:numPr')
            il = OxmlElement('w:ilvl'); il.set(qn('w:val'), '0')
            ni = OxmlElement('w:numId'); ni.set(qn('w:val'), str(nid)); npr.extend([il, ni]); props.append(npr)

    def cover(self, paragraphs: list[str], subtitle: str):
        p = self.paragraph('Universidad de Guayaquil', 'Subtitle')
        p.paragraph_format.space_before = Pt(40)
        self.paragraph(self.title, 'Title')
        self.paragraph(subtitle, 'Subtitle')
        for value in paragraphs: self.paragraph(value)
        self.paragraph('Edición de noviembre de 2026', 'ManualNote')

    def toc(self, entries: list[tuple[str, str]], page_map: dict[str, int]):
        self.start_page('portrait')
        self.paragraph('Contenido', 'ContentsTitle')
        p = self.doc.add_paragraph()
        for el in [('fldChar', 'begin'), ('instrText', None), ('fldChar', 'separate')]:
            obj = OxmlElement('w:' + el[0])
            if el[0] == 'fldChar': obj.set(qn('w:fldCharType'), el[1])
            else: obj.set(qn('xml:space'), 'preserve'); obj.text = ' TOC \\o "1-1" \\h \\z \\u '
            p.add_run()._r.append(obj)
        for title, anchor in entries:
            p = self.doc.add_paragraph(style='TOC 1')
            p.paragraph_format.tab_stops.add_tab_stop(Inches(6.95), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            hyperlink = OxmlElement('w:hyperlink'); hyperlink.set(qn('w:anchor'), anchor)
            run = OxmlElement('w:r'); tx = OxmlElement('w:t'); tx.text = title; run.append(tx); hyperlink.append(run); p._p.append(hyperlink)
            p.add_run('\t')
            field(p, f' PAGEREF {anchor} \\h ', str(page_map.get(title, 1)))
        end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end'); p.add_run()._r.append(end)

    def figure(self, record: dict, note=''):
        from PIL import Image
        self.start_page('landscape')
        self.figure_count += 1
        p = self.doc.add_paragraph(style='Caption')
        anchor = f'figure_{self.figure_count:03d}'
        start = OxmlElement('w:bookmarkStart'); start.set(qn('w:id'), str(self.bookmark_count)); start.set(qn('w:name'), anchor)
        end = OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'), str(self.bookmark_count))
        p._p.append(start)
        p.add_run(f'Figura {self.figure_count}').bold = True
        p._p.append(end)
        self.bookmark_count += 1
        p.add_run('. ')
        p.add_run(record['title']).italic = True
        p.paragraph_format.keep_with_next = True
        if note or record.get('note'):
            np = self.paragraph(note or record['note'], 'FigureOrientation')
            np.paragraph_format.keep_with_next = True
        path = Path(record['path'])
        with Image.open(path) as im:
            width_px, height_px = im.size
        max_w, max_h = 9.9, 6.50
        width = min(max_w, max_h * width_px / height_px)
        pp = self.doc.add_paragraph()
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.paragraph_format.space_after = Pt(0)
        pp.paragraph_format.line_spacing = 1.0
        shape = pp.add_run().add_picture(str(path), width=Inches(width))
        shape._inline.docPr.set('descr', record['title'])
        self.media.append({**record, 'figure': self.figure_count, 'pixel_width': width_px, 'pixel_height': height_px,
                           'printed_width_inches': width, 'printed_height_inches': width * height_px / width_px,
                           'image_bytes_preserved': True})

    def save(self, path):
        self.doc.save(path)
        # No crop instruction or composited image is ever introduced.
        with ZipFile(path) as z:
            xml = z.read('word/document.xml')
            if b'srcRect' in xml: raise ValueError('Se encontró recorte de imagen no autorizado.')
            embedded = {hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
            for rec in self.media:
                if rec['sha256'] not in embedded: raise ValueError(f'Imagen no preservada íntegramente: {rec["logical_key"]}')


def compact_entries() -> list[tuple[str, str]]:
    return [(heading_text(title), f'chapter_{i+1:03d}') for i, (title, _, _) in enumerate(COMPACT_GROUPS)]


def build_compact(data: dict, resolver: CaptureResolver, path: Path, pages: dict[str, int]):
    book = Book(data['titulo'], True)
    fichas = {f['pagina_planificada']: f for f in data['fichas']}
    cover = fichas[1]['parrafos'][:2]
    book.cover(cover, 'Guía operativa para aprender y demostrar el prototipo')
    book.toc(compact_entries(), pages)
    selected = resolver.config.get('university_figures')
    override_figures = {}
    if selected:
        for row in selected:
            override_figures.setdefault(row['after_group'], []).append(row['key'])
    seen_figures = {}
    for number, (title, nums, keys) in enumerate(COMPACT_GROUPS, 1):
        book.start_page('portrait'); book.heading(title)
        for index in nums:
            ficha = fichas[index]
            book.heading(ficha['titulo'], 2)
            for paragraph in ficha['parrafos']: book.paragraph(paragraph)
            book.procedure(ficha['pasos'])
            book.paragraph(ficha['resultado'], 'ManualNote', 'Resultado esperado')
            book.paragraph(ficha['precaucion'], 'ManualNote', 'Atención')
        # Architecture is newly authored and distinguished from an application screenshot.
        if number == 1: book.figure(resolver.diagram())
        for key in override_figures.get(number, keys):
            rec = resolver.resolve(key)
            if rec['sha256'] not in seen_figures:
                seen_figures[rec['sha256']] = book.figure_count + 1
                book.figure(rec, 'Consulte el procedimiento anterior y confirme el estado visible antes de continuar.')
            else:
                reference = book.doc.add_paragraph(style='ManualNote')
                reference.add_run('La misma vista completa se muestra en la ')
                number_seen = seen_figures[rec['sha256']]
                field(reference, f' REF figure_{number_seen:03d} \\h ', f'Figura {number_seen}')
                reference.add_run('. Confirme los identificadores y filtros descritos en este caso.')
    book.save(path)
    return book


def unit_heading(unit):
    return heading_text(unit['titulo'])


def build_training(data: dict, resolver: CaptureResolver, path: Path, pages: dict[str, int]):
    units = data['unidades']
    book = Book(data['titulo'])
    book.cover([
        'Este manual de formación explica cómo operar el prototipo y cómo justificar las decisiones de inteligencia de negocios. Está dirigido a personas que comienzan desde cero y a quienes deben demostrar su funcionamiento.',
        'Siga las unidades en orden para una instalación nueva o consulte la unidad que corresponda a su responsabilidad. La extensión responde al aprendizaje y no tiene un mínimo de páginas.',
        'Una consulta de expedientes existentes y una generación nueva son actividades distintas. Los casos históricos deben identificarse con su fuente, propuesta, ejecución y condiciones.'
    ], 'Formación práctica en inteligencia de negocios e inteligencia artificial')
    entries = [(unit_heading(u), f'chapter_{i+1:03d}') for i, u in enumerate(units)]
    if data.get('glosario'): entries.append(('Glosario de consulta', f'chapter_{len(entries)+1:03d}'))
    book.toc(entries, pages)
    seen_figures = {}
    for idx, unit in enumerate(units):
        book.start_page('portrait'); book.heading(unit['titulo'])
        book.paragraph(text(unit.get('objetivo')))
        if unit.get('roles'): book.paragraph(', '.join(texts(unit['roles'])), 'ManualNote', 'Responsabilidades')
        if unit.get('ruta_interfaz'): book.paragraph(text(unit['ruta_interfaz']), 'ManualNote', 'Dónde trabajar')
        for intro in texts(unit.get('introduccion')): book.paragraph(intro)
        if idx == 0:
            book.figure(resolver.diagram())
            book.start_page('portrait')
        concepts = unit.get('conceptos', [])
        if concepts:
            book.heading('Conceptos para tomar la decisión', 2)
            for item in concepts: book.paragraph(text(item.get('explicacion')), lead=text(item.get('termino')))
        options = unit.get('campos_y_criterios', [])
        if options:
            book.heading('Qué significa cada opción', 2)
            for option in options:
                book.paragraph(text(option.get('que_significa')), lead=text(option.get('opcion')))
                if option.get('criterio_de_uso'): book.paragraph(text(option['criterio_de_uso']), 'ManualNote', 'Criterio de uso')
        if unit.get('pasos'): book.heading('Procedimiento', 2)
        # Keep a complete procedure together; its full screenshots follow inside
        # this same unit. Native figure references preserve the action-to-view link.
        pending_figures = []
        for step_index, step in enumerate(unit.get('pasos', []), 1):
            book.procedure([text(step.get('accion'))], start_number=int(step.get('numero', step_index)))
            if step.get('resultado_que_debe_observar'):
                book.paragraph(text(step['resultado_que_debe_observar']), 'ManualNote', 'Qué debe observar')
            if step.get('capture_key'):
                rec = resolver.resolve(step['capture_key'])
                if rec['sha256'] not in seen_figures:
                    seen_figures[rec['sha256']] = book.figure_count + len(pending_figures) + 1
                    pending_figures.append(rec)
                figure_number = seen_figures[rec['sha256']]
                reference = book.doc.add_paragraph(style='ManualNote')
                reference.add_run('Consulte la ')
                field(reference, f' REF figure_{figure_number:03d} \\h ', f'Figura {figure_number}')
                reference.add_run(' para reconocer la pantalla de este paso. Las capturas completas se agrupan al final de esta unidad.')
        if unit.get('resultado_esperado'): book.paragraph(text(unit['resultado_esperado']), lead='Resultado esperado')
        for label, fieldname in [('Comprobaciones', 'comprobaciones'), ('Cómo explicarlo en la sustentación', 'que_explicar_al_jurado'), ('Criterios de aprendizaje', 'notas_de_aprendizaje')]:
            if unit.get(fieldname):
                book.heading(label, 2)
                for value in texts(unit[fieldname]): book.paragraph(value)
        exercise = unit.get('ejercicio')
        if exercise:
            book.heading('Practique lo aprendido', 2)
            book.paragraph(text(exercise.get('consigna')))
            if exercise.get('respuesta_orientativa'): book.paragraph(text(exercise['respuesta_orientativa']), lead='Orientación')
        # Distinguish a new observed run from a previous reference case.
        for evidence_key, label in [('evidencia_actual', 'Resultado comprobado en esta revisión'),
                             ('evidencia_previa', 'Referencia de un caso anterior')]:
            evidence = unit.get(evidence_key)
            if not evidence:
                continue
            book.heading(label, 2)
            if isinstance(evidence, dict):
                for key, value in evidence.items():
                    if key not in {'capturas', 'images', 'path', 'rutas', 'origen_documental'}: book.paragraph('; '.join(texts(value)), lead=heading_text(key))
            else:
                for value in texts(evidence): book.paragraph(value)
        unitkeys = texts(unit.get('capture_keys'))
        for key in dict.fromkeys(unitkeys):
            rec = resolver.resolve(key)
            if rec['sha256'] in seen_figures:
                continue
            seen_figures[rec['sha256']] = book.figure_count + len(pending_figures) + 1
            pending_figures.append(rec)
        for rec in pending_figures:
            book.figure(rec, 'Pantalla de referencia para el procedimiento de esta unidad. Lea el paso vinculado y confirme fuente, identificadores y estado visible.')
    if data.get('glosario'):
        book.start_page('portrait'); book.heading('Glosario de consulta')
        glossary = data['glosario']
        items = glossary.items() if isinstance(glossary, dict) else [(x.get('termino', ''), x.get('definicion', x.get('explicacion', ''))) for x in glossary]
        for term, definition in items: book.paragraph(text(definition), lead=text(term))
    book.save(path)
    return book


def export_pdf(docx: Path, destination: Path, work: Path):
    destination.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix='lo-profile-', dir=work))
    home = work / 'home'; home.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['HOME'] = str(home)
    env['PATH'] = os.pathsep.join([str(RUNTIME / 'bin/override'), str(RUNTIME / 'bin/fallback'), env.get('PATH', '')])
    command = [str(SOFFICE), f'-env:UserInstallation={profile.as_uri()}', '--headless', '--convert-to', 'pdf:writer_pdf_Export', '--outdir', str(destination), str(docx)]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=240)
    (work / ('lo-' + docx.stem + '.log')).write_text(result.stdout + '\n' + result.stderr)
    pdf = destination / (docx.stem + '.pdf')
    if result.returncode or not pdf.is_file() or pdf.stat().st_size < 1024:
        raise RuntimeError(f'No se generó el PDF con LibreOffice del runtime: {result.stderr[-1500:]}')
    return pdf


def pdf_heading_pages(pdf: Path, headings: list[tuple[str, str]]):
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    required = {title for title, _ in headings}
    found = {}
    def visit(items):
        for item in items:
            if isinstance(item, list): visit(item)
            else:
                title = heading_text(getattr(item, 'title', item.get('/Title', '')))
                if title in required:
                    found[title] = reader.get_destination_page_number(item) + 1
    visit(reader.outline)
    # Do not fall back to first text occurrence: the index itself contains titles.
    missing = sorted(required - found.keys())
    if missing: raise RuntimeError('No se pudieron verificar páginas reales de estos encabezados PDF: ' + '; '.join(missing))
    return found, len(reader.pages)


def build_one(kind, data, resolver, args):
    stem = 'Manual_de_usuario_universidad' if kind == 'universidad' else 'Manual_de_formacion_BI_IA'
    work = BASE / 'qa/build' / kind
    work.mkdir(parents=True, exist_ok=True)
    builder = build_compact if kind == 'universidad' else build_training
    if args.docx_only:
        draft = work / (stem + '_primer_borrador.docx')
        book = builder(data, resolver, draft, {})
        return {'tipo': kind, 'estado': 'Borrador interno para primera revisión; índice pendiente de paginación', 'docx': str(draft), 'figuras': book.figure_count}
    pages = {}
    passes = []
    stable = False
    for attempt in range(1, 5):
        passdir = work / f'pasada_{attempt:02d}'; passdir.mkdir(exist_ok=True)
        docx = passdir / (stem + '.docx')
        book = builder(data, resolver, docx, pages)
        pdf = export_pdf(docx, passdir / 'pdf', work)
        observed, count = pdf_heading_pages(pdf, book.headings)
        passes.append({'pasada': attempt, 'paginas': count, 'indice_estable': observed == pages})
        if observed == pages:
            stable = True; break
        pages = observed
    if not stable: raise RuntimeError(f'El índice de {kind} no se estabilizó; revise composición antes de entregar.')
    if kind == 'universidad' and not args.min_compact_pages <= count <= args.max_compact_pages:
        raise RuntimeError(f'El compacto resultó de {count} páginas; objetivo {args.min_compact_pages}–{args.max_compact_pages}. Ajuste agrupación o figuras, sin reducir legibilidad.')
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    final_docx = out / docx.name; final_pdf = out / pdf.name
    shutil.copy2(docx, final_docx); shutil.copy2(pdf, final_pdf)
    rendered = None
    if args.render_pages:
        renderdir = BASE / 'qa/render' / kind
        renderdir.mkdir(parents=True, exist_ok=True)
        # A shorter revision must not inherit PNGs from a longer prior render.
        for old_page in renderdir.glob('page-*.png'):
            old_page.unlink()
        run = subprocess.run([str(PYTHON), str(RENDERER), str(final_docx), '--output_dir', str(renderdir), '--emit_pdf'], capture_output=True, text=True, timeout=1800)
        (work / 'render.log').write_text(run.stdout + '\n' + run.stderr)
        if run.returncode: raise RuntimeError(f'Falló render_docx.py: {run.stderr[-1500:]}')
        pngs = list(renderdir.glob('page-*.png'))
        if len(pngs) != count: raise RuntimeError(f'Faltan páginas renderizadas de {kind}: {len(pngs)} / {count}')
        # Same canonical rendering controls the delivered PDF as the PNG review.
        canonical_pdf = renderdir / (final_docx.stem + '.pdf')
        if canonical_pdf.is_file(): shutil.copy2(canonical_pdf, final_pdf)
        check_pages, check_count = pdf_heading_pages(final_pdf, book.headings)
        if check_pages != pages or check_count != count: raise RuntimeError('La paginación del render final difiere del índice. No entregar; reconstruir.')
        rendered = str(renderdir)
    report = {'tipo': kind, 'estado': 'Composición completa; requiere inspección visual humana de todas las páginas',
              'docx': str(final_docx), 'pdf': str(final_pdf), 'docx_sha256': sha(final_docx), 'pdf_sha256': sha(final_pdf),
              'paginas': count, 'figuras': book.figure_count, 'indice_nativo_verificado': True,
              'paginas_del_indice': pages, 'pasadas': passes, 'render_png': rendered,
              'minimo_paginas_formacion': None, 'imagenes': book.media,
              'runtime_python': str(PYTHON), 'runtime_libreoffice': str(SOFFICE),
              'pruebas_operativas_nuevas_realizadas_por_generador': False}
    (BASE / 'qa' / f'composicion_{kind}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return {k: v for k, v in report.items() if k not in {'imagenes', 'paginas_del_indice'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--only', choices=['ambos', 'universidad', 'formacion'], default='ambos')
    parser.add_argument('--universidad', type=Path, default=BASE / 'contenido_universidad.json')
    parser.add_argument('--formacion', type=Path, default=BASE / 'contenido_formacion.json')
    parser.add_argument('--manifest', type=Path, default=BASE / 'capturas/manifest.json')
    parser.add_argument('--capture-map', type=Path)
    parser.add_argument('--architecture', type=Path, default=DEFAULT_ARCHITECTURE)
    parser.add_argument('--output-dir', type=Path, default=BASE / 'output')
    parser.add_argument('--check', action='store_true', help='Validar fuentes e imágenes sin autoría DOCX/PDF.')
    parser.add_argument('--docx-only', action='store_true', help='Primer borrador interno para revisar geometría; no entrega final.')
    parser.add_argument('--render-pages', action='store_true', help='Render canónico final de todas las páginas para su revisión visual.')
    parser.add_argument('--min-compact-pages', type=int, default=30)
    parser.add_argument('--max-compact-pages', type=int, default=40)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError(f'Ejecute con el Python bundled: {PYTHON}')
    kinds = ['universidad', 'formacion'] if args.only == 'ambos' else [args.only]
    datasets = {kind: load_json(getattr(args, kind)) for kind in kinds}
    resolver = CaptureResolver(args.manifest, args.capture_map, args.architecture)
    verification = validate_inputs(args, resolver, datasets)
    if args.check:
        print(json.dumps(verification, ensure_ascii=False, indent=2))
        return 0 if verification['valido'] else 2
    if not verification['valido']:
        raise ValueError('No se generan documentos incompletos:\n' + '\n'.join(verification['errores']))
    authoring_imports()
    reports = [build_one(kind, datasets[kind], resolver, args) for kind in kinds]
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(2)
