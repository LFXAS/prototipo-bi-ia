#!/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"""Compone el manual editable a partir de contenidos y capturas locales.

No consulta ni modifica la aplicación BI. No usa LibreOffice ni crea un PDF.
Ejecutar únicamente con el Python del runtime indicado en RUNTIME_PYTHON.
Antes de la primera ejecución de autoría, el flujo responsable debe registrar
una sola vez la operación de artefactos mediante el marcador de la skill.
Después de crear el DOCX, renderizarlo con la skill documents, revisar TODAS
las páginas y corregir la composición antes de entregar DOCX y PDF.

LibreOffice permitido para esa fase posterior, exclusivamente:
/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice

El índice es estático y enlazado con marcadores nativos. No contiene números
de página inventados ni un campo TOC pendiente de actualización. La numeración
de página del pie es un campo PAGE nativo.

Extensiones opcionales del registro de capturas, sin alterar los originales:
  {"capitulo": 12, "regiones": [{"y": 200, "alto": 730,
    "titulo": "Indicadores elegidos"}], "incluir": true}
También se admite bbox=[izquierda, arriba, derecha, abajo] por región.
Las regiones se guardan en qa/recortes y se rotulan como captura parcial.

--validate-only inspecciona insumos y estructura sin crear el documento.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image


RUNTIME_PYTHON = Path("/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
BASE = Path(__file__).resolve().parent
REPO_ROOT = "/home/ceo/Proyectos/BI/"
SOURCE_COMMIT = "8f1c7d1"
DOCUMENT_DATE = "5 de noviembre de 2026"
BLACK = RGBColor(0, 0, 0)
GRAY = RGBColor(80, 80, 80)
CORE_FIELDS = ("titulo", "objetivo", "rol", "requisitos", "pasos", "resultado", "verificacion", "errores", "explicacion", "fuentes")


@dataclass
class Chapter:
    number: int
    title: str
    introduction: str
    items: list[tuple[str, int]] = field(default_factory=list)


CHAPTERS = [
    Chapter(1, "Propósito del manual y mapa de trabajo", "La plataforma separa la preparación técnica, el diseño de la necesidad, la aprobación humana, la carga controlada y la lectura gerencial. Empiece por este mapa para identificar qué modifica cada operación y qué evidencia deja.", [("roles", 0), ("roles", 3), ("asistente", 0)]),
    Chapter(2, "Conceptos para interpretar datos de ventas", "Una cifra defendible necesita un evento comercial definido, un grano identificable, una fórmula coherente y una unidad conocida. Estas decisiones preceden a los botones del asistente y explican por qué dos sumas pueden describir hechos distintos.", [("analitica", 3), ("analitica", 4), ("analitica", 5), ("analitica", 6), ("analitica", 7), ("asistente", 4), ("asistente", 19)]),
    Chapter(3, "Acceso navegación y fuente de trabajo", "La cuenta establece las acciones autorizadas y la fuente en contexto establece la base a la que se refiere el recorrido. Compruebe ambas antes de interpretar una pantalla o reutilizar un expediente.", [("roles", 1), ("roles", 2)]),
    Chapter(4, "Usuarios roles permisos menús y auditoría", "Administración organiza los accesos con los permisos existentes y revisa las operaciones registradas. La matriz de este capítulo distingue el catálogo del sistema, las responsabilidades propuestas y la evidencia efectiva de una cuenta.", [("roles", 4), ("roles", 5), ("roles", 6), ("roles", 7), ("roles", 8), ("roles", 14)]),
    Chapter(5, "Parámetros operativos y conexiones de datos", "Configure los valores operativos y el acceso de solo lectura a la fuente antes de diseñar. Guardar un registro, probarlo y habilitarlo son estados distintos; conviene verificarlos por separado.", [("roles", 9), ("roles", 12), ("roles", 13)]),
    Chapter(6, "Explorador de metadatos y estructura de las fuentes", "El explorador permite relacionar los conceptos de negocio con las tablas, columnas, tipos y relaciones que la fuente declara. Una instantánea de estructura aporta trazabilidad al diseño y no equivale a una carga de ventas."),
    Chapter(7, "Configuración y operación del proveedor de inteligencia artificial", "La configuración LLM determina el proveedor que recibe el contexto autorizado. Revise los campos, la prueba de conexión, el estado de preparación y los límites de cada alternativa antes de activar el servicio.", [("roles", 10), ("roles", 11), ("analitica", 17)]),
    Chapter(8, "Catálogo analítico y preguntas de negocio", "Consulte primero el catálogo de la fuente seleccionada. Las preguntas y periodicidades orientan la necesidad, pero su disponibilidad no acredita que todos sus importes sean ejecutables o estén conciliados.", [("asistente", 1), ("asistente", 2), ("asistente", 3)]),
    Chapter(9, "Asistente de datamart y formulación de la necesidad", "El primer paso del asistente expresa qué se desea decidir, sobre qué evento comercial y con qué cobertura. Use la evidencia de la fuente para precisar la solicitud y conserve las advertencias de disponibilidad.", [("asistente", 5), ("asistente", 6)]),
    Chapter(10, "Conceptos y propuesta del modelo dimensional", "Los pasos segundo y tercero conectan la necesidad con conceptos, tablas y relaciones permitidas. Revise inclusiones, grano y cobertura antes de tratar el diseño como un contrato de carga.", [("asistente", 7), ("asistente", 8)]),
    Chapter(11, "Personalización revisión y aprobación de propuestas", "Los pasos cuarto y quinto fijan dimensiones, indicadores, agregaciones y decisiones de revisión. La aprobación debe expresar una decisión humana consciente de las fórmulas, las advertencias y la evidencia disponible.", [("asistente", 9), ("asistente", 10), ("asistente", 11), ("asistente", 12), ("asistente", 13)]),
    Chapter(12, "Datamart de ventas y ejecución del proceso ETL", "Los cinco pasos de materialización seleccionan un contrato aprobado, revisan indicadores y transformaciones, preparan la ejecución, cargan y concilian. Identifique el expediente para evitar repetir una operación al consultar su evidencia.", [("asistente", 14), ("asistente", 15), ("asistente", 16), ("asistente", 17), ("asistente", 18), ("asistente", 20)]),
    Chapter(13, "Analítica de ventas y lectura gerencial", "El panel presenta una ejecución concreta con sus filtros y cobertura. La lectura combina valores exactos, contexto financiero y límites de interpretación para que el hallazgo pueda revisarse.", [("analitica", 0), ("analitica", 1), ("analitica", 2), ("analitica", 8), ("analitica", 9), ("analitica", 10)]),
    Chapter(14, "Copiloto analítico y exportación de informes", "El copiloto interpreta preguntas dentro del contexto analítico autorizado. Compruebe lo interpretado y conserve fuente, ejecución, filtros y unidades cuando comunique o exporte los resultados.", [("analitica", 11), ("analitica", 12)]),
    Chapter(15, "Escenarios de AdventureWorks y WideWorldImporters", "Los ejercicios separan el procedimiento reproducible del resultado efectivamente observado. Cada base requiere su propia necesidad, instantánea y expediente; una validación estructural no demuestra por sí sola una carga nueva exitosa.", [("asistente", 21), ("asistente", 22), ("asistente", 23)]),
    Chapter(16, "Incidencias y límites funcionales identificados", "Localice primero la etapa y el estado que conserva la plataforma. Los hallazgos de este capítulo explican límites concretos de la interfaz y evitan responder a un fallo con una carga o una modificación innecesaria.", [("analitica", 13)]),
    Chapter(17, "Operación técnica y preparación de la sustentación", "La demostración debe permitir seguir el razonamiento desde la necesidad hasta la evidencia del resultado. Distinga las responsabilidades de operación, desarrollo y revisión, y comunique los límites de cada prueba.", [("roles", 15), ("analitica", 14), ("analitica", 15), ("analitica", 16)]),
    Chapter(18, "Glosario referencias y atlas de capturas", "Use este capítulo para consultar términos, ubicar el respaldo técnico de los procedimientos y localizar las capturas originales con sus identificadores.", [("asistente", 24)]),
]


GLOSSARY = [
    ("Agregación", "Operación que resume varias filas, por ejemplo suma, promedio, conteo, conteo distinto, mínimo o máximo. Debe ser coherente con el grano y la interpretación del indicador."),
    ("Catálogo analítico", "Conjunto de preguntas y periodicidades disponibles para orientar necesidades por fuente y dominio. Su selección no demuestra que una carga haya sido ejecutada."),
    ("Conciliación", "Comparación registrada entre los resultados del origen y del destino para el alcance que define la ejecución. Su conclusión debe leerse con sus controles, tolerancias y límites."),
    ("Contrato de materialización", "Diseño controlado que vincula la propuesta aprobada con las dimensiones, medidas, relaciones, fórmulas y condiciones que el motor puede ejecutar."),
    ("Datamart", "Estructura analítica orientada a un dominio de negocio. En este proyecto la materialización de ventas se conserva en el destino analítico, separada de la fuente transaccional."),
    ("Dimensión", "Contexto descriptivo con el que se organiza un hecho, por ejemplo fecha, producto o cliente. Debe tener una relación válida con el grano del hecho."),
    ("ETL", "Extracción, transformación y carga. En la plataforma el expediente permite distinguir preparación, ejecución física y validación posterior."),
    ("Expediente de ejecución", "Registro identificable de una materialización, sus controles y resultados. Consultarlo no requiere cargar nuevamente los datos."),
    ("Fuente en contexto", "Base seleccionada en la navegación global para situar las consultas y operaciones. No sustituye la identificación de la fuente dentro de cada expediente."),
    ("Grano", "Significado de una fila del hecho. Determina qué evento se cuenta y qué relaciones o agregaciones pueden usarse sin duplicarlo."),
    ("Hecho", "Evento que se analiza con un grano definido y medidas asociadas, por ejemplo una línea de venta o de factura según el contrato."),
    ("Indicador o KPI", "Medida interpretada para una decisión. Necesita una fórmula, unidad, población, período y alcance explícitos."),
    ("Instantánea de metadatos", "Versión conservada de la estructura de una fuente, con tablas, columnas, tipos, claves y relaciones. Describe estructura y no equivale a copiar todas las filas."),
    ("LLM", "Modelo de lenguaje usado para interpretar y proponer dentro de los contratos del sistema. Sus sugerencias se someten a controles y revisión humana."),
    ("Medida", "Valor cuantitativo asociado a un hecho que puede resumirse con la operación adecuada. No toda columna numérica representa un importe sumable."),
    ("OLTP", "Base transaccional que registra la operación de negocio. La aplicación utiliza una conexión de lectura para inspeccionar y extraer los datos autorizados."),
    ("Propuesta", "Versión del diseño dimensional que se revisa y puede aprobarse antes de materializar. Su aprobación no es una ejecución ETL."),
    ("RBAC", "Autorización mediante roles. Una cuenta obtiene permisos por sus roles asignados y el servidor comprueba cada operación."),
    ("Razón de totales", "Indicador calculado dividiendo dos agregados compatibles. El precio o margen ponderado puede requerir esta operación en lugar del promedio simple de razones por fila."),
    ("Resolución semántica", "Revisión de las etiquetas y del significado con que se presentan conceptos del modelo. Su estado y evidencia deben distinguirse de la conciliación numérica."),
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sí" if value else "No"
    text = str(value)
    for char in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        text = text.replace(char, "-")
    return text.replace("\u00a0", " ").strip()


def heading_text(value: str) -> str:
    """Los encabezados usan solamente letras, números y espacios."""
    return re.sub(r"\s+", " ", "".join(c if c.isalnum() or c.isspace() else " " for c in clean_text(value))).strip()


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", clean_text(value)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def values(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def human_label(key: str) -> str:
    return heading_text(key.replace("_", " ")).capitalize()


def safe_anchor(value: str) -> str:
    """Word bookmark names must be valid identifiers of at most 40 chars."""
    name = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not name or name[0].isdigit():
        name = "a_" + name
    if len(name) > 40:
        name = name[:31] + "_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return name


def read_json(path: Path, required: bool = True) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def section_list(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, dict) and isinstance(obj.get("secciones"), list):
        return obj["secciones"]
    if isinstance(obj, list) and all(isinstance(x, dict) and "titulo" in x for x in obj):
        return obj
    return []


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_capture_date(value: str) -> str:
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Guayaquil"))
        return date.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return clean_text(value)


class Sources:
    def __init__(self) -> None:
        self.entries: OrderedDict[str, str] = OrderedDict()

    def ids(self, refs: Any) -> list[str]:
        result = []
        for raw in values(refs):
            if isinstance(raw, dict):
                raw = raw.get("ruta") or raw.get("fuente") or raw.get("referencia") or json.dumps(raw, ensure_ascii=False)
            ref = clean_text(raw)
            if not ref:
                continue
            if ref.startswith(("backend/", "frontend/", "docs/")):
                ref = REPO_ROOT + ref
            if ref.startswith(REPO_ROOT):
                # Audited source lines moved during the corrective work. Cite
                # the actual file rather than preserve a misleading line number.
                ref = re.sub(r"(\.(?:py|tsx?|md|tex)):\d+(?:[-–]\d+)?$", r"\1", ref)
            if ref not in self.entries:
                self.entries[ref] = f"F{len(self.entries) + 1:03d}"
            if self.entries[ref] not in result:
                result.append(self.entries[ref])
        return result


class Builder:
    def __init__(self, project: Path, output: Path, args: argparse.Namespace) -> None:
        self.project, self.output, self.args = project, output, args
        self.data = {
            "roles": read_json(project / "contenido_roles_parametros.json"),
            "asistente": read_json(project / "contenido_asistente_etl.json"),
            "analitica": read_json(project / "contenido_analitica_sustentacion.json"),
        }
        self.sections = {key: section_list(value) for key, value in self.data.items()}
        self.optional = {
            "metadatos": self.first_optional("cont_nuevo.json", "contenido_nuevo.json", "contenido_metadatos.json"),
            "pruebas": self.first_optional("pruebas_actuales.json"),
            "exportaciones": self.first_optional("contenidoexportaciones.json", "contenido_exportaciones.json", "extras_exportaciones.json"),
            "formacion": self.first_optional("hoja_ruta_capacitacion.json"),
            "preguntas_formacion": self.first_optional("banco_preguntas_formacion.json"),
        }
        self.sections["nuevo"] = section_list(self.optional["metadatos"])
        self.sections["exportaciones"] = section_list(self.optional["exportaciones"])
        self.sections["formacion"] = section_list(self.optional["formacion"])
        self.split_new_content = len(self.sections["nuevo"]) >= 3
        raw_registry = read_json(project / "capturas" / "registro.json", required=False) or []
        self.registry = raw_registry.get("capturas", []) if isinstance(raw_registry, dict) else raw_registry
        self.registry = [r for r in self.registry if r.get("incluir", True)]
        if args.max_figures:
            self.registry = self.registry[:args.max_figures]
        self.sources = Sources()
        self.doc: Any = None
        self.bookmark_id = 0
        self.num_id = 3000
        self.figure_count = 0
        self.figure_entries: list[dict[str, Any]] = []
        self.content_entries: list[dict[str, Any]] = []
        self.warnings: list[str] = []
        self.figure_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self.used_ids: set[str] = set()
        for capture in self.registry:
            capture_id = clean_text(capture.get("id") or Path(capture.get("file", "captura")).stem)
            if capture_id in self.used_ids:
                raise ValueError(f"Identificador de captura duplicado: {capture_id}")
            self.used_ids.add(capture_id)
            self.figure_groups[self.capture_chapter(capture)].append(capture)

    def first_optional(self, *names: str) -> Any:
        for name in names:
            path = self.project / name
            if path.exists():
                return read_json(path)
        return None

    def validate(self) -> dict[str, Any]:
        expected = {"roles": 16, "asistente": 25, "analitica": 18}
        used = [(k, n) for chapter in CHAPTERS for k, n in chapter.items]
        for key, count in expected.items():
            if len(self.sections[key]) != count:
                raise ValueError(f"{key}: se esperaban {count} secciones y se recibieron {len(self.sections[key])}")
            for index, section in enumerate(self.sections[key]):
                missing = [field for field in CORE_FIELDS if field not in section]
                if missing:
                    raise ValueError(f"{key} {index}: campos ausentes {missing}")
                if (key, index) not in used:
                    raise ValueError(f"Sección no incluida: {key} {index}")
        if len(set(used)) != len(used):
            raise ValueError("Una sección principal fue asignada más de una vez")
        image_rows = []
        for record in self.registry:
            path = self.capture_path(record)
            if not path.exists():
                raise FileNotFoundError(path)
            with Image.open(path) as im:
                width, height = im.size
            image_rows.append({"id": record.get("id"), "capitulo": self.capture_chapter(record), "ancho": width, "alto": height})
        if not self.optional["metadatos"]:
            self.warnings.append("Sin contenido adicional de metadatos: el capítulo 6 conserva la introducción y las capturas disponibles.")
        if not self.optional["pruebas"]:
            self.warnings.append("Sin pruebas_actuales.json: los escenarios se presentan como procedimientos y no como resultados nuevos observados.")
        return {"secciones_principales": len(used), "secciones_integradas": sum(len(self.planned_items(chapter)) for chapter in CHAPTERS), "capitulos": len(CHAPTERS), "capturas": image_rows, "opcionales": {k: v is not None for k, v in self.optional.items()}, "advertencias": self.warnings}

    def planned_items(self, chapter: Chapter) -> list[tuple[str, int, dict[str, Any]]]:
        items = [(key, index, self.sections[key][index]) for key, index in chapter.items]
        if chapter.number == 1:
            items = [("formacion", index, section) for index, section in enumerate(self.sections["formacion"])] + items
        if self.split_new_content:
            if chapter.number == 1:
                items.append(("nuevo", 2, self.sections["nuevo"][2]))
            elif chapter.number == 3:
                items.insert(0, ("nuevo", 1, self.sections["nuevo"][1]))
            elif chapter.number == 6:
                items.append(("nuevo", 0, self.sections["nuevo"][0]))
            for index, section in enumerate(self.sections["nuevo"][3:], 3):
                target = int(section.get("capitulo", section.get("chapter", 6)))
                if not 1 <= target <= 18:
                    raise ValueError(f"Capítulo adicional fuera de rango: {target}")
                if chapter.number == target:
                    items.append(("nuevo", index, section))
        if chapter.number == 14:
            for index, section in enumerate(self.sections["exportaciones"]):
                items.append(("exportaciones", index, section))
        return items

    def capture_path(self, record: dict[str, Any]) -> Path:
        raw = Path(record.get("file") or record.get("archivo") or "")
        if raw.is_absolute() and raw.exists():
            return raw
        for candidate in (self.project / raw, self.project / "capturas" / raw.name):
            if candidate.exists():
                return candidate
        return self.project / "capturas" / raw.name

    @staticmethod
    def capture_chapter(record: dict[str, Any]) -> int:
        explicit = record.get("capitulo") or record.get("chapter")
        if explicit is not None:
            chapter = int(explicit)
            if not 1 <= chapter <= 18:
                raise ValueError(f"Capítulo de captura fuera de rango: {explicit}")
            return chapter
        reviewed_chapters = {"25_sesion_vencida": 3, "33_gerente_permiso_metadatos": 4, "39h_aw_detalle_producto": 13, "47_wwi_limites_revisados": 9}
        if record.get("id") in reviewed_chapters:
            return reviewed_chapters[record["id"]]
        groups = [
            (14, ("copiloto", "export", "reporte", "informe_analitico")),
            (13, ("analitica", "dashboard", "filtro", "ranking", "vista_ejecutiva", "vista_analitica", "grafico")),
            (12, ("etl", "materializ", "concili", "carga", "semantica", "transformacion", "datamart_ventas", "expediente", "validar_resultados")),
            (11, ("personaliz", "aprob", "revision", "historial_propuesta", "correccion_guiada")),
            (10, ("concepto", "modelo_dimensional", "propuesta_modelo", "modelo_", "propuesta_")),
            (9, ("necesidad", "viabilidad", "sugerencia", "dominio")),
            (8, ("catalogo",)),
            (7, ("llm", "proveedor")),
            (6, ("metadato", "esquema", "columnas", "relaciones")),
            (5, ("conexion", "parametro", "fuentes_probadas")),
            (4, ("usuario", "roles", "rol_", "permiso", "menus", "auditoria")),
            (3, ("acceso", "menu", "inicio", "fuente_activa", "sesion")),
            (15, ("escenario", "prueba_negativa", "limite")),
        ]
        # The id is normally more specific than the title. For example,
        # "05c_roles_completo" must not move to Catálogo because its title
        # happens to say "Catálogo completo de roles y permisos".
        for field in ("id", "titulo"):
            name = slug(str(record.get(field, "")))
            for chapter, terms in groups:
                if any(term in name for term in terms):
                    return chapter
        return 15

    def bookmark(self, paragraph: Any, name: str) -> None:
        self.bookmark_id += 1
        start, end = OxmlElement("w:bookmarkStart"), OxmlElement("w:bookmarkEnd")
        start.set(qn("w:id"), str(self.bookmark_id))
        start.set(qn("w:name"), safe_anchor(name))
        end.set(qn("w:id"), str(self.bookmark_id))
        paragraph._p.insert(0, start)
        paragraph._p.append(end)

    @staticmethod
    def hyperlink(paragraph: Any, text: str, anchor: str, color: str = "000000") -> None:
        link = OxmlElement("w:hyperlink")
        link.set(qn("w:anchor"), safe_anchor(anchor))
        link.set(qn("w:history"), "1")
        run = OxmlElement("w:r")
        props = OxmlElement("w:rPr")
        clr = OxmlElement("w:color")
        clr.set(qn("w:val"), color)
        props.append(clr)
        run.append(props)
        node = OxmlElement("w:t")
        node.text = clean_text(text)
        run.append(node)
        link.append(run)
        paragraph._p.append(link)

    @staticmethod
    def set_font(style: Any, name: str, size: float, bold: bool = False, color: RGBColor = BLACK) -> None:
        style.font.name, style.font.size, style.font.bold, style.font.color.rgb = name, Pt(size), bold, color
        props = style.element.get_or_add_rPr()
        fonts = props.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            props.append(fonts)
        for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qn(f"w:{attr}"), name)
        for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn(f"w:{attr}"), None)
        clr = props.find(qn("w:color"))
        if clr is not None:
            for attr in ("themeColor", "themeTint", "themeShade"):
                clr.attrib.pop(qn(f"w:{attr}"), None)

    def configure(self) -> None:
        self.doc = Document()
        section = self.doc.sections[0]
        section.page_width, section.page_height = Inches(8.5), Inches(11)
        section.top_margin = section.bottom_margin = Cm(2.2)
        section.left_margin = section.right_margin = Cm(2.2)
        section.header_distance, section.footer_distance = Cm(0.8), Cm(0.9)
        section.different_first_page_header_footer = True
        styles = self.doc.styles
        for name, size, bold in (("Normal", self.args.font_size, False), ("Title", 27, True), ("Subtitle", 15, False), ("Heading 1", 18, True), ("Heading 2", 14, True), ("Heading 3", 11.5, True)):
            self.set_font(styles[name], self.args.font, size, bold)
        normal = styles["Normal"].paragraph_format
        normal.space_after, normal.line_spacing = Pt(5), 1.10
        normal.widow_control = True
        for name in ("Heading 1", "Heading 2", "Heading 3"):
            pf = styles[name].paragraph_format
            pf.keep_with_next, pf.keep_together = True, True
            pf.space_before = Pt(14 if name == "Heading 1" else 12 if name == "Heading 2" else 8)
            pf.space_after = Pt(5 if name != "Heading 3" else 4)
        styles["Title"].paragraph_format.space_after = Pt(14)
        styles["Subtitle"].paragraph_format.space_after = Pt(18)
        custom = [("Manual Caption", 9.5, False, GRAY), ("Manual Small", 9.5, False, GRAY), ("Manual Source", 9, False, GRAY), ("Manual TOC", 11.5, False, BLACK), ("Manual Table", 9.5, False, BLACK), ("Manual Step", self.args.font_size, False, BLACK), ("Manual Bullet", self.args.font_size, False, BLACK)]
        for name, size, bold, color in custom:
            style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = styles["Normal"]
            self.set_font(style, self.args.font, size, bold, color)
            style.paragraph_format.space_after = Pt(5)
        styles["Manual Caption"].paragraph_format.keep_with_next = False
        styles["Manual Caption"].paragraph_format.space_after = Pt(10)
        styles["Manual Source"].paragraph_format.space_before = Pt(2)
        styles["Manual Source"].paragraph_format.space_after = Pt(2)
        styles["Manual Source"].paragraph_format.keep_together = True
        styles["Manual Table"].paragraph_format.space_after = Pt(3)
        styles["Manual Table"].paragraph_format.line_spacing = 1.05
        for name in ("Manual Step", "Manual Bullet"):
            styles[name].paragraph_format.left_indent = Cm(0.65)
            styles[name].paragraph_format.first_line_indent = Cm(-0.45)
            styles[name].paragraph_format.space_after = Pt(4)
        # Black headings and no inherited or direct paragraph borders.
        for name in ("Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
            ppr = styles[name].element.find(qn("w:pPr"))
            if ppr is not None:
                for border in list(ppr.findall(qn("w:pBdr"))):
                    ppr.remove(border)
        settings = self.doc.settings.element
        lang = OxmlElement("w:themeFontLang")
        lang.set(qn("w:val"), "es-EC")
        settings.append(lang)
        props = self.doc.core_properties
        props.title = "Manual de usuario de la plataforma de inteligencia de negocios"
        props.subject = "Configuración operación analítica y sustentación"
        props.author = "Proyecto BI"
        props.keywords = f"Manual usuario BI AdventureWorks WideWorldImporters {SOURCE_COMMIT}"
        props.comments = ""
        footer = section.footer.paragraphs[0]
        self.set_font(styles["Footer"], self.args.font, 8, color=GRAY)
        footer.style = "Footer"
        footer.paragraph_format.space_after = Pt(0)
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = footer.add_run("Manual de usuario BI  |  ")
        run.font.name, run.font.size, run.font.color.rgb = self.args.font, Pt(8), GRAY
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        footer._p.append(field)

    def p(self, text: Any = "", style: str | None = None, bold_lead: str | None = None) -> Any:
        paragraph = self.doc.add_paragraph(style=style)
        if bold_lead:
            paragraph.add_run(bold_lead).bold = True
        paragraph.add_run(clean_text(text))
        return paragraph

    def h(self, title: str, level: int, anchor: str | None = None) -> Any:
        paragraph = self.doc.add_heading(heading_text(title), level)
        if anchor:
            self.bookmark(paragraph, anchor)
        return paragraph

    def numbering(self, bullet: bool = False) -> int:
        self.num_id += 1
        root = self.doc.part.numbering_part.element
        abstract = OxmlElement("w:abstractNum")
        abstract.set(qn("w:abstractNumId"), str(self.num_id))
        multi = OxmlElement("w:multiLevelType")
        multi.set(qn("w:val"), "singleLevel")
        abstract.append(multi)
        level = OxmlElement("w:lvl")
        level.set(qn("w:ilvl"), "0")
        for tag, value in (("start", "1"), ("numFmt", "bullet" if bullet else "decimal"), ("lvlText", "•" if bullet else "%1."), ("lvlJc", "left")):
            el = OxmlElement(f"w:{tag}")
            el.set(qn("w:val"), value)
            level.append(el)
        ppr, ind = OxmlElement("w:pPr"), OxmlElement("w:ind")
        ind.set(qn("w:left"), "370")
        ind.set(qn("w:hanging"), "255")
        ppr.append(ind)
        level.append(ppr)
        abstract.append(level)
        # CT_Numbering requires all abstractNum elements before all num
        # elements. Insert rather than interleaving each new definition.
        first_num = root.find(qn("w:num"))
        if first_num is not None:
            root.insert(root.index(first_num), abstract)
        else:
            num_mac = root.find(qn("w:numIdMac"))
            if num_mac is not None:
                root.insert(root.index(num_mac), abstract)
            else:
                root.append(abstract)
        num = OxmlElement("w:num")
        num.set(qn("w:numId"), str(self.num_id))
        aid = OxmlElement("w:abstractNumId")
        aid.set(qn("w:val"), str(self.num_id))
        num.append(aid)
        num_mac = root.find(qn("w:numIdMac"))
        if num_mac is not None:
            root.insert(root.index(num_mac), num)
        else:
            root.append(num)
        return self.num_id

    def list_items(self, items: Any, ordered: bool = False) -> None:
        members = values(items)
        if not members:
            return
        num = self.numbering(bullet=not ordered)
        for item in members:
            if isinstance(item, (dict, list)):
                self.render_generic(item, depth=0)
                continue
            if ordered and isinstance(item, str):
                item = re.sub(r"^\s*\d+[.)]\s+", "", item)
            paragraph = self.p(item, "Manual Step" if ordered else "Manual Bullet")
            props = paragraph._p.get_or_add_pPr()
            numpr, ilvl, numid = OxmlElement("w:numPr"), OxmlElement("w:ilvl"), OxmlElement("w:numId")
            ilvl.set(qn("w:val"), "0")
            numid.set(qn("w:val"), str(num))
            numpr.extend((ilvl, numid))
            props.append(numpr)

    def source_links(self, raw: Any) -> None:
        refs = self.sources.ids(raw)
        if refs:
            if self.doc.paragraphs:
                # Keep the reference line with actual content rather than
                # allowing an otherwise empty page containing only sources.
                self.doc.paragraphs[-1].paragraph_format.keep_with_next = True
            paragraph = self.p(style="Manual Source")
            paragraph.add_run("Respaldo técnico  ")
            for i, source_id in enumerate(refs):
                if i:
                    paragraph.add_run("  ")
                self.hyperlink(paragraph, source_id, source_id, "505050")

    def cover(self) -> None:
        self.p("Manual de usuario y entrenamiento en BI e IA", "Title")
        self.p("Aprendizaje operación paso a paso y sustentación del prototipo", "Subtitle")
        self.p("Proyecto de inteligencia de negocios para el dominio de ventas")
        self.p("AdventureWorks y WideWorldImporters")
        self.p(DOCUMENT_DATE)
        self.p("Dirigido a administración, análisis BI, gerencia y responsables de desarrollo y sustentación.")
        self.p("Este manual explica cómo preparar las fuentes y los accesos, formular una necesidad comercial, revisar un modelo dimensional, ejecutar y conciliar una carga y consultar sus resultados. También presenta los criterios para elegir campos y fórmulas y para explicar ante el jurado qué evidencia respalda cada conclusión.")
        self.p(f"Referencia técnica del proyecto  {SOURCE_COMMIT}", "Manual Small")
        self.doc.add_page_break()
        self.h("Cómo consultar este manual", 1, "orientacion")
        self.p("Para una instalación ya iniciada, siga los capítulos 1 y 3 a 8 antes de crear una necesidad. Los capítulos 9 a 12 explican el diseño y la materialización. Los capítulos 13 y 14 corresponden a consulta y comunicación de resultados. Los escenarios, incidencias y criterios de sustentación se encuentran en los capítulos 15 a 17.")
        self.p("Las instrucciones describen el resultado esperado de un procedimiento. Las capturas muestran estados observados en la instalación y conservan su fecha. Los registros de pruebas actuales, cuando están disponibles, identifican su propio resultado y sus límites. Una captura de un formulario, una propuesta aprobada o un expediente histórico no acredita una nueva carga exitosa.")
        self.p("Cada sección conserva los requisitos, pasos, verificaciones y errores relevantes. Los identificadores F remiten al respaldo técnico reunido en el capítulo 18. El índice y las referencias internas son enlaces del documento editable y del PDF que los conserve.")
        self.p("Para estudiar, explique en voz alta qué hace una opción, por qué la usaría y cómo comprobaría su resultado. El banco de 25 preguntas del capítulo 17 incluye respuestas razonadas y comprobaciones sobre los casos de ventas. Memorizar la secuencia de botones no sustituye comprender el grano, la fórmula, la unidad y la evidencia.")
        self.p("Las capturas extensas se muestran mediante regiones legibles. El pie identifica cada captura parcial; el archivo original se conserva sin cambios junto con los recursos del manual.")

    def toc(self) -> None:
        self.h("Índice general", 1, "indice")
        for chapter in CHAPTERS:
            paragraph = self.p(style="Manual TOC")
            paragraph.paragraph_format.space_before = Pt(6)
            self.hyperlink(paragraph, f"{chapter.number}  {chapter.title}", f"cap_{chapter.number:02d}")
            for subindex, (key, index, section) in enumerate(self.planned_items(chapter), 1):
                paragraph = self.p(style="Manual Small")
                paragraph.paragraph_format.left_indent = Cm(0.5)
                self.hyperlink(paragraph, f"{chapter.number}.{subindex}  {heading_text(section['titulo'])}", self.section_anchor(chapter.number, key, index), "505050")
            if chapter.number == 6 and self.optional["metadatos"] and not self.split_new_content:
                paragraph = self.p("Exploración de las dos fuentes y lectura de su estructura", "Manual Small")
                paragraph.paragraph_format.left_indent = Cm(0.5)
            if chapter.number == 18:
                for title, anchor in (("Glosario", "glosario"), ("Referencias técnicas", "referencias"), ("Atlas de capturas", "atlas")):
                    paragraph = self.p(style="Manual Small")
                    paragraph.paragraph_format.left_indent = Cm(0.5)
                    self.hyperlink(paragraph, title, anchor, "505050")
            elif chapter.number == 17 and self.optional["preguntas_formacion"]:
                paragraph = self.p(style="Manual Small")
                paragraph.paragraph_format.left_indent = Cm(0.5)
                self.hyperlink(paragraph, "Planes de demostración con evidencia existente o generación nueva", "planes_demostracion", "505050")
                paragraph = self.p(style="Manual Small")
                paragraph.paragraph_format.left_indent = Cm(0.5)
                self.hyperlink(paragraph, "25 preguntas para aprender y sustentar las decisiones", "preguntas_formacion", "505050")

    @staticmethod
    def section_anchor(chapter: int, key: str, index: int) -> str:
        return f"s_{chapter:02d}_{key}_{index:02d}"

    def procedure(self, section: dict[str, Any], chapter: int, subindex: int, key: str = "extra", index: int = 0) -> None:
        anchor = self.section_anchor(chapter, key, index)
        self.h(f"{chapter}.{subindex} {section.get('titulo', 'Procedimiento')}", 2, anchor)
        if section.get("objetivo"):
            self.p(section["objetivo"])
        if section.get("rol"):
            self.p(section["rol"], bold_lead="Responsabilidad  ")
        for explanation in values(section.get("explicacion")):
            if isinstance(explanation, (dict, list)):
                self.render_generic(explanation)
            else:
                self.p(explanation)
        if section.get("requisitos"):
            self.h("Antes de comenzar", 3)
            self.list_items(section["requisitos"])
        if section.get("pasos"):
            self.h("Procedimiento", 3)
            self.list_items(section["pasos"], ordered=True)
        if section.get("resultado"):
            self.h("Resultado esperado", 3)
            self.render_generic(section["resultado"])
        if section.get("verificacion"):
            self.h("Cómo comprobar el resultado", 3)
            self.list_items(section["verificacion"])
        if section.get("errores"):
            self.h("Errores que conviene evitar", 3)
            self.list_items(section["errores"])
        known = set(CORE_FIELDS) | {"capitulo", "chapter", "seccion_manual"}
        for extra_key, value in section.items():
            if extra_key not in known and value not in (None, "", []):
                self.h(human_label(extra_key), 3)
                self.render_generic(value)
        self.source_links(section.get("fuentes"))
        self.content_entries.append({"capitulo": chapter, "subseccion": subindex, "origen": key, "indice": index, "titulo": section.get("titulo"), "campos": list(section), "anchor": anchor})

    def render_generic(self, value: Any, depth: int = 0) -> None:
        """Conserva información opcional sin convertirla en una afirmación de éxito."""
        if value in (None, "", []):
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("fuentes", "referencias", "sources"):
                    self.source_links(item)
                    continue
                if item in (None, "", []):
                    continue
                if isinstance(item, (dict, list)):
                    self.p(human_label(key), bold_lead="")
                    self.render_generic(item, depth + 1)
                else:
                    self.p(item, bold_lead=human_label(key) + "  ")
        elif isinstance(value, list):
            if all(not isinstance(item, (dict, list)) for item in value):
                self.list_items(value)
            else:
                for index, item in enumerate(value):
                    if isinstance(item, dict) and item.get("titulo"):
                        self.h(item["titulo"], 3)
                        self.render_generic({k: v for k, v in item.items() if k != "titulo"}, depth + 1)
                    else:
                        self.render_generic(item, depth + 1)
        else:
            self.p(value)

    def optional_content(self, name: str, chapter: int, first_subindex: int) -> None:
        obj = self.optional.get(name)
        if obj is None:
            return
        sections = section_list(obj)
        if sections:
            for index, section in enumerate(sections):
                self.procedure(section, chapter, first_subindex + index, name, index)
            extra = {k: v for k, v in obj.items() if k != "secciones"} if isinstance(obj, dict) else {}
            if extra:
                self.h("Información complementaria del registro", 2)
                self.render_generic(extra)
        else:
            titles = {"metadatos": "Guía complementaria del explorador", "pruebas": "Registro de los escenarios actuales", "exportaciones": "Informes y descargas disponibles"}
            self.h(titles[name], 2, f"extra_{name}")
            self.render_generic(obj)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> Any:
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        pr = table._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            item = OxmlElement(f"w:{edge}")
            for attribute, val in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
                item.set(qn("w:" + attribute), val)
            borders.append(item)
        pr.append(borders)
        margins = OxmlElement("w:tblCellMar")
        for side, size in (("top", "80"), ("bottom", "80"), ("left", "105"), ("right", "105")):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:w"), size)
            el.set(qn("w:type"), "dxa")
            margins.append(el)
        pr.append(margins)
        for col, width in zip(table.columns, widths):
            col.width = Inches(width)
        all_rows = [headers] + rows
        for rowindex, content in enumerate(all_rows):
            row = table.rows[0] if rowindex == 0 else table.add_row()
            for cell, text, width in zip(row.cells, content, widths):
                cell.width = Inches(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p = cell.paragraphs[0]
                p.style = "Manual Table"
                p.add_run(clean_text(text)).bold = rowindex == 0
                if rowindex == 0:
                    p.paragraph_format.keep_with_next = True
                    shading = OxmlElement("w:shd")
                    shading.set(qn("w:fill"), "EAEAEA")
                    cell._tc.get_or_add_tcPr().append(shading)
            if rowindex == 0:
                header = OxmlElement("w:tblHeader")
                header.set(qn("w:val"), "true")
                row._tr.get_or_add_trPr().append(header)
            no_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(no_split)
        return table

    def permissions_matrix(self) -> None:
        matrix = self.data["roles"].get("matriz_permisos", {})
        records = matrix.get("filas", [])
        if not records:
            return
        self.h("Recomendación de responsabilidades y permisos", 2, "matriz_permisos")
        self.p(matrix.get("criterio", ""))
        self.p("La programadora utiliza los permisos del rol asignado. Esta responsabilidad no crea un rol adicional ni concede acceso por sí misma. Las condiciones particulares se conservan debajo de cada grupo.")
        groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
        for row in records:
            code = row["codigo"]
            group = "Seguridad" if code.startswith("security.") else "Parámetros y proveedor LLM" if code.startswith("parameters.") else "Conexiones" if code.startswith("connections.") else "Metadatos" if code.startswith("metadata.") else "Catálogo y propuestas" if code.startswith("copilot.") else "Materialización" if code.startswith("etl.") else "Analítica informes y auditoría"
            groups.setdefault(group, []).append(row)
        for group, members in groups.items():
            self.h(group, 3)
            rows, notes = [], []
            for row in members:
                states = []
                for role in ("Administrador", "Analista BI", "Gerente comercial"):
                    original = row.get(role, "")
                    short = original.split(";")[0].split(" por ")[0]
                    if len(short) > 23 or original != short:
                        noteid = f"M{len(notes) + 1}"
                        notes.append(f"{noteid}. {row['codigo']} - {role}: {original}.")
                        short = ("No operativo" if original.startswith("No operativo") else "No propuesto" if original.startswith("No propuesto") else "Propuesto" if original.startswith("Propuesto") else "Sí seed") + f" ({noteid})"
                    states.append(short.replace("Sí, seed", "Sí seed"))
                rows.append([row["codigo"], row["actividad"], *states])
                programmer = row.get("Programadora", "")
                if programmer and programmer != "Según rol asignado":
                    notes.append(f"{row['codigo']} - Programadora: {programmer}.")
            self.table(["Código", "Actividad", "Admin", "Analista BI", "Gerencia"], rows, [1.70, 2.0, 0.70, 1.05, 1.10])
            for note in notes:
                self.p(note, "Manual Small")

    def observed_permissions(self) -> None:
        """La configuración leída y la recomendación se presentan separadas."""
        matrix = self.data["roles"].get("matriz_configuracion_observada", {})
        if not matrix:
            return
        self.h(matrix.get("titulo", "Configuración de permisos observada"), 2, "permisos_observados")
        if matrix.get("fecha"):
            self.p(matrix["fecha"], bold_lead="Fecha de observación  ")
        self.p(matrix.get("criterio", ""))
        for summary in matrix.get("resumen", []):
            text = f"{summary.get('rol', '')}: {summary.get('permisos_marcados', '')} permisos marcados."
            if summary.get("sesion_propiedad_rol_probada") is False:
                text += " No se ha acreditado en este registro un recorrido autenticado propio de ese rol."
            elif summary.get("sesion_propiedad_rol_probada") is True:
                text += " El registro indica una sesión propia del rol probada; consulte el alcance de su evidencia."
            self.p(text)
            if summary.get("evidencia"):
                self.source_links(summary["evidencia"])
        rows = [[row.get("codigo", ""), row.get("nombre", ""), row.get("Analista BI", ""), row.get("Gerente comercial", "")] for row in matrix.get("filas", [])]
        if rows:
            self.table(["Código", "Actividad", "Analista BI", "Gerente comercial"], rows, [1.70, 1.88, 1.32, 1.65])
        if matrix.get("codigos_no_marcados_en_ambos"):
            self.h("Códigos no marcados en ambos roles", 3)
            self.p("; ".join(clean_text(code) for code in matrix["codigos_no_marcados_en_ambos"]) + ".")
        if matrix.get("diferencias_con_recomendacion"):
            self.h("Diferencias con la recomendación", 3)
            for difference in matrix["diferencias_con_recomendacion"]:
                self.p(difference)
        self.source_links(matrix.get("fuentes"))
        known = {"titulo", "fecha", "criterio", "resumen", "filas", "codigos_no_marcados_en_ambos", "diferencias_con_recomendacion", "fuentes"}
        for key, value in matrix.items():
            if key not in known:
                self.h(human_label(key), 3)
                self.render_generic(value)

    def functional_alerts(self) -> None:
        alerts = self.data["roles"].get("alertas_funcionales", [])
        if not alerts:
            return
        self.h("Hallazgos de la interfaz y su efecto operativo", 2, "alertas_funcionales")
        self.p("Estos hallazgos describen el comportamiento y los límites identificados en el corte técnico. Su presencia en el manual no representa una corrección aplicada al software.")
        for alert in alerts:
            self.h(alert["id"], 3, "alerta_" + slug(alert["id"]))
            self.p(alert.get("hallazgo", ""))
            self.p(alert.get("impacto", ""), bold_lead="Efecto operativo  ")
            self.source_links(alert.get("fuentes"))

    def observed_tests(self, *, history: bool = False) -> None:
        obj = self.optional.get("pruebas")
        if not isinstance(obj, dict) or not ("casos" in obj or "escenarios" in obj):
            self.optional_content("pruebas", 15, 1)
            return
        self.h("Historial de QA y límites de las pruebas" if history else "Casos de éxito comprobados", 2,
               "historial_pruebas" if history else "extra_pruebas")
        metadata = {k: v for k, v in obj.items() if k not in {"casos", "escenarios"}}
        if not history:
            self.render_generic(metadata)
            self.p("Los casos de esta sección tienen un resultado observado satisfactorio dentro del alcance descrito. La numeración de versiones y expedientes cambia al repetir el ejercicio. Los intentos rechazados, las correcciones y las verificaciones aún pendientes se conservan en el capítulo 16.")
        else:
            self.p("El historial conserva los intentos que motivaron correcciones y los límites de verificación. Un rechazo no se transforma en éxito por la aprobación de otra versión. Cada repetición posterior identifica por separado su resultado y evidencia.")
        cases = [case for case in obj.get("casos", [])
                 if (case.get("seccion_manual") != "exito") == history]
        if cases:
            self.h("Resumen de pruebas registradas", 3)
            self.table(["Identificador", "Prueba", "Estado registrado"], [[str(case.get("id", "")), str(case.get("nombre", "")), str(case.get("estado", ""))] for case in cases], [0.9, 2.6, 3.05])
            for case in cases:
                self.h(f"{case.get('id', '')} {case.get('nombre', '')}", 3)
                self.p(case.get("estado", ""), bold_lead="Estado registrado  ")
                self.p(case.get("observado", ""), bold_lead="Resultado observado  ")
                ids = case.get("capturas", [])
                if ids:
                    paragraph = self.p(style="Manual Small")
                    paragraph.add_run("Capturas de respaldo  ")
                    for i, capture_id in enumerate(ids):
                        if i:
                            paragraph.add_run("  ")
                        if str(capture_id) in self.used_ids:
                            self.hyperlink(paragraph, str(capture_id), "captura_" + slug(str(capture_id)), "505050")
                        else:
                            paragraph.add_run(str(capture_id) + " (original en recursos)")
                for key, value in case.items():
                    if key not in {"id", "nombre", "estado", "observado", "capturas", "seccion_manual"}:
                        if key == "fuentes":
                            self.source_links(value)
                        else:
                            self.p(human_label(key), bold_lead="")
                            self.render_generic(value)
        for index, scenario in enumerate([] if history else obj.get("escenarios", []), 1):
            self.h(f"Escenario {index} {scenario.get('fuente', scenario.get('nombre', ''))}", 3)
            self.render_generic(scenario)

    def learning_questions(self) -> None:
        bank = self.optional.get("preguntas_formacion")
        if not isinstance(bank, dict):
            return
        self.h("Planes de demostración", 2, "planes_demostracion")
        for plan in bank.get("planes_demostracion", []):
            self.h(f"Plan {plan.get('plan', '')}. {plan.get('titulo', '')}", 3)
            self.p(plan.get("objetivo", ""))
            self.p("Preparación", bold_lead="")
            for requirement in plan.get("requisitos", []):
                self.p(requirement)
            self.p("Secuencia", bold_lead="")
            for step in plan.get("secuencia", []):
                self.p(step)
            self.p(plan.get("resultado", ""), bold_lead="Resultado  ")
            self.p(plan.get("limite", ""), bold_lead="Alcance de la prueba  ")
        self.h("25 preguntas para aprender y sustentar las decisiones", 2, "preguntas_formacion")
        self.p(bank.get("objetivo", ""))
        for instruction in bank.get("uso_docente", []):
            self.p(instruction)
        for index, question in enumerate(bank.get("preguntas", []), 1):
            self.h(f"{index}. {question.get('tema', '')}", 3, f"formacion_{index:02d}")
            self.p(question.get("pregunta", ""), bold_lead="Pregunta  ")
            self.p(question.get("respuesta_razonada", ""), bold_lead="Respuesta razonada  ")
            self.p("Comprobación en la plataforma", bold_lead="")
            for check in question.get("comprobacion", []):
                self.p(check)
            self.p(question.get("caso_observado", ""), bold_lead="Caso observado  ")
            self.p(question.get("limite", ""), bold_lead="Límite de la respuesta  ")
            self.source_links(question.get("fuentes"))
        self.h("Criterios de dominio del aprendizaje", 3)
        for criterion in bank.get("criterios_evaluacion", []):
            self.p(criterion)

    def capture_regions(self, record: dict[str, Any]) -> list[tuple[Path, str, bool, list[int] | None]]:
        path = self.capture_path(record)
        with Image.open(path) as original:
            width, height = original.size
            explicit = record.get("regiones") or record.get("regions")
            # Two reviewed regions retain role identity plus the key metadata
            # and export controls. The editable observed matrix reproduces
            # every recorded checkbox; these partial images do not claim to
            # display the complete form or an applied change.
            role_regions = {
                "05d_rol_analista": [{"y": 230, "alto": 760, "titulo": "identidad del rol y primeros permisos"}, {"y": 1310, "alto": 760, "titulo": "permisos de metadatos y exportación"}],
                "05e_rol_gerente": [{"y": 230, "alto": 760, "titulo": "identidad del rol y primeros permisos"}, {"y": 1310, "alto": 760, "titulo": "permisos de metadatos y exportación"}],
                "09_parametros": [{"y": 150, "alto": 760, "titulo": "parámetros de conexión y proveedor"}, {"y": 913, "alto": 760, "titulo": "parámetros de metadatos e interfaz"}],
                "10_conexiones": [{"y": 150, "alto": 760, "titulo": "campos del registro de conexión"}, {"y": 900, "alto": 732, "titulo": "controles de transporte y fuentes registradas"}],
                "10b_conexiones_probadas": [{"y": 950, "alto": 750, "titulo": "resultados de validación de ambas fuentes"}],
                "11c_llm_alternativa_probada": [{"y": 845, "alto": 675, "titulo": "resultado de conectividad y configuraciones disponibles"}],
                "12b_metadatos_aw_detalle": [{"y": 1400, "alto": 730, "titulo": "columnas y claves de SalesOrderDetail"}, {"y": 2130, "alto": 550, "titulo": "LineTotal y relaciones declaradas"}],
                "13b_metadatos_wwi_detalle": [{"y": 1515, "alto": 715, "titulo": "columnas de InvoiceLines"}, {"y": 2210, "alto": 650, "titulo": "importes y relaciones de la línea de factura"}],
                "14_catalogo_aw": [{"y": 2085, "alto": 595, "titulo": "pregunta de negocio y sus campos"}, {"y": 3920, "alto": 850, "titulo": "criterios de costos y valores por unidad"}],
                "14b_catalogo_criterios": [{"y": 195, "alto": 415, "titulo": "criterio corregido para costos verificables"}],
                "15b_catalogo_wwi_guardado": [{"y": 2050, "alto": 725, "titulo": "confirmación de guardado y primera pregunta"}, {"y": 4030, "alto": 860, "titulo": "criterios de costos y razones por unidad"}],
                "17_aw_necesidad_opciones": [{"y": 830, "alto": 855, "titulo": "objetivo consentimiento y ayudas"}, {"y": 1720, "alto": 800, "titulo": "preguntas periodicidad y validación"}],
                "17b_aw_sugerencias_limitadas": [{"y": 2000, "alto": 620, "titulo": "sugerencia y límites identificados"}, {"y": 2590, "alto": 520, "titulo": "respaldo insuficiente y uso deshabilitado"}],
                "18_aw_necesidad_final": [{"y": 830, "alto": 855, "titulo": "objetivo de 531 caracteres y consentimiento"}, {"y": 1720, "alto": 800, "titulo": "cuatro preguntas y periodicidad elegidas"}],
                "19_aw_viabilidad_objetivo_rechazado": [{"y": 780, "alto": 720, "titulo": "rechazo y objetivo conservado"}],
            }
            if not explicit:
                explicit = role_regions.get(record.get("id"))
            # Long model and ETL screens carry essential controls in the
            # centre. Show representative consecutive areas rather than the
            # recurring navigation header and unrelated historical footer.
            extensive_screens = {"23h_aw_propuesta_modelo": 5, "24h_aw_personalizacion": 4, "29h_aw_etl_indicadores": 3, "30h_aw_etl_plan": 4}
            if not explicit and record.get("id") in extensive_screens:
                count = extensive_screens[record["id"]]
                start = min(110, max(0, height - 760))
                region_height = min(900, height - start)
                last_start = max(start, height - region_height)
                explicit = [{"y": round(start + (last_start - start) * index / max(1, count - 1)), "alto": region_height, "titulo": f"región {index + 1} de {count} del contenido"} for index in range(count)]
            if not explicit and height <= 1000:
                return [(path, "", False, None)]
            if explicit:
                specs = explicit
            else:
                # Keep scale consistent with the narrow captured viewport.
                # At the preferred width a short region remains readable; never shrink
                # a 6000 px page to one printed page.
                content_y = int(record.get("content_y", 110 if width >= 800 else 150))
                content_y = min(max(0, content_y), max(0, height - 760))
                region_height = min(int(record.get("content_height", 760)), height - content_y)
                specs = [{"y": content_y, "alto": region_height, "titulo": "región del contenido"}]
                if record.get("mostrar_final", False) and height > region_height * 1.6:
                    specs.append({"y": height - region_height, "alto": region_height, "titulo": "región final"})
            result = []
            crop_dir = self.project / "qa" / "recortes"
            crop_dir.mkdir(parents=True, exist_ok=True)
            for index, spec in enumerate(specs, 1):
                bbox = spec.get("bbox")
                if bbox:
                    if len(bbox) != 4:
                        raise ValueError(f"bbox inválido en {record.get('id')}")
                    left, top, right, bottom = map(int, bbox)
                else:
                    left = int(spec.get("x", 0))
                    top = int(spec.get("y", 0))
                    right = left + int(spec.get("ancho", width))
                    bottom = top + int(spec.get("alto", 760))
                left, top = max(0, left), max(0, top)
                right, bottom = min(width, right), min(height, bottom)
                if right <= left or bottom <= top:
                    raise ValueError(f"Recorte vacío en {record.get('id')}")
                out = crop_dir / f"{slug(record.get('id', path.stem))}_{index:02d}.jpg"
                # Preserve native pixels and high quality text edges without
                # embedding inflated PNG recompressions of JPEG originals.
                original.crop((left, top, right, bottom)).convert("RGB").save(
                    out, quality=95, subsampling=0, optimize=True
                )
                result.append((out, clean_text(spec.get("titulo") or f"región {index}"), True, [left, top, right, bottom]))
            return result

    def figures(self, chapter: int) -> None:
        if self.args.omit_images or not self.figure_groups.get(chapter):
            return
        self.h("Capturas del recorrido", 2, f"capturas_cap_{chapter:02d}")
        for record in self.figure_groups[chapter]:
            self.figure_count += 1
            number = self.figure_count
            source = self.capture_path(record)
            title = clean_text(record.get("titulo") or source.stem)
            detail = clean_text(record.get("detalle", ""))
            anchor = f"fig_{number:03d}"
            self.h(f"Figura {number} {title}", 3, anchor)
            self.bookmark(self.doc.paragraphs[-1], "captura_" + slug(str(record.get("id", source.stem))))
            if detail:
                self.p(detail).paragraph_format.keep_with_next = True
            regions = self.capture_regions(record)
            for index, (path, label, partial, box) in enumerate(regions, 1):
                with Image.open(path) as im:
                    width, height = im.size
                preferred_width = 6.4 if width >= 800 else 5.5
                # A Letter page has more than nine inches of usable height.
                # Reserve room for title, description and caption while
                # keeping narrow screenshots near their readable width.
                image_width = min(preferred_width, 7.0 * width / height)
                paragraph = self.p()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.keep_with_next = True
                inline = paragraph.add_run().add_picture(str(path), width=Inches(image_width))
                inline._inline.docPr.set("descr", title + (". Captura parcial de " + label if partial else "") + (". " + detail if detail else ""))
                suffix = f"{chr(96 + index)}" if len(regions) > 1 else ""
                caption = f"Figura {number}{suffix}. {title}. "
                caption += f"Captura parcial, {label}. " if partial else "Captura del área visible. "
                date = local_capture_date(record.get("captured_at", ""))
                if date:
                    caption += f"{date}, hora de Guayaquil. "
                caption += f"Original {source.name}."
                self.p(caption, "Manual Caption")
            self.figure_entries.append({"numero": number, "id": record.get("id"), "titulo": title, "capitulo": chapter, "original": source.name, "captured_at": record.get("captured_at"), "sha256_original": file_sha256(source), "anchor": anchor, "regiones": [{"archivo": str(path.relative_to(self.project)) if path.is_relative_to(self.project) else str(path), "titulo": label, "parcial": partial, "bbox": box} for path, label, partial, box in regions]})

    def glossary(self) -> None:
        self.h("Glosario", 2, "glosario")
        new = self.optional.get("metadatos")
        provided = new.get("glosario", []) if isinstance(new, dict) else []
        entries: list[tuple[str, str]] = []
        for item in provided:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                entries.append((str(item[0]), str(item[1])))
            elif isinstance(item, dict):
                term = item.get("termino") or item.get("titulo")
                definition = item.get("definicion") or item.get("descripcion")
                if term and definition:
                    entries.append((str(term), str(definition)))
        aliases = {"grano_o_granularidad": "grano", "kpi_o_indicador": "indicador", "indicador_o_kpi": "indicador", "instantanea_de_metadatos": "instantanea"}
        seen = {aliases.get(slug(term), slug(term)) for term, _ in entries}
        for term, definition in GLOSSARY:
            key = aliases.get(slug(term), slug(term))
            if key not in seen:
                entries.append((term, definition))
                seen.add(key)
        for term, definition in entries:
            self.p(definition, bold_lead=term + "  ")

    def references(self) -> None:
        self.h("Referencias técnicas", 2, "referencias")
        self.p(f"Los procedimientos remiten al código y la documentación internos del proyecto BI, con referencia de corte {SOURCE_COMMIT}. Los identificadores F permiten localizar las rutas sin interrumpir la lectura del procedimiento. Las referencias de observación conservan su procedencia y fecha.")
        self.p(f"Raíz del repositorio  {REPO_ROOT.rstrip('/')}", "Manual Small")
        self.p("Las referencias al repositorio identifican archivos: las correcciones pueden desplazar sus líneas y no se presentan números de línea antiguos como ubicaciones actuales. Las fuentes editables conservan la procedencia de las inspecciones. Las rutas indicadas como Recursos del manual se resuelven desde la carpeta que contiene este documento y sus archivos de apoyo. Las capturas se identifican también en el atlas y conservan sus originales.")
        for ref, source_id in self.sources.entries.items():
            display = ref[len(REPO_ROOT):] if ref.startswith(REPO_ROOT) else ref
            project_prefix = str(self.project) + "/"
            if ref.startswith(project_prefix):
                display = "Recursos del manual/" + ref[len(project_prefix):]
            paragraph = self.p(style="Manual Source")
            self.bookmark(paragraph, source_id)
            paragraph.add_run(source_id + "  ").bold = True
            paragraph.add_run(display)

    def atlas(self) -> None:
        self.h("Atlas de capturas", 2, "atlas")
        self.p("El número de figura enlaza con su ubicación en el manual. El nombre identifica el original conservado en la carpeta de recursos. Una figura puede mostrar una o varias regiones de ese mismo original.")
        for chapter in CHAPTERS:
            records = [entry for entry in self.figure_entries if entry["capitulo"] == chapter.number]
            if not records:
                continue
            self.h(f"Capítulo {chapter.number} {chapter.title}", 3)
            for entry in records:
                paragraph = self.p(style="Manual Small")
                self.hyperlink(paragraph, f"Figura {entry['numero']}", entry["anchor"])
                paragraph.add_run(f"  {entry['titulo']}  |  {entry['original']}")
        if not self.figure_entries:
            self.p("No se incorporaron capturas en esta composición.")

    def build(self) -> None:
        self.configure()
        self.cover()
        self.toc()
        for chapter in CHAPTERS:
            self.doc.add_page_break()
            self.h(f"{chapter.number} {chapter.title}", 1, f"cap_{chapter.number:02d}")
            paragraph = self.p(style="Manual Small")
            self.hyperlink(paragraph, "Volver al índice", "indice", "505050")
            self.p(chapter.introduction)
            if chapter.number == 15:
                self.observed_tests()
            for subindex, (key, index, section) in enumerate(self.planned_items(chapter), 1):
                self.procedure(section, chapter.number, subindex, key, index)
            if chapter.number == 4:
                self.observed_permissions()
                self.permissions_matrix()
            elif chapter.number == 6 and not self.split_new_content:
                self.optional_content("metadatos", chapter.number, 1)
            elif chapter.number == 14 and not self.sections["exportaciones"]:
                self.optional_content("exportaciones", chapter.number, len(chapter.items) + 1)
            elif chapter.number == 16:
                self.observed_tests(history=True)
                self.functional_alerts()
            elif chapter.number == 17:
                self.learning_questions()
            if chapter.number == 18:
                self.glossary()
                self.references()
                self.atlas()
            self.figures(chapter.number)
        # The file is native, editable OOXML; images are the only raster content.
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(self.output)
        qa = self.project / "qa"
        qa.mkdir(parents=True, exist_ok=True)
        manifest = {"documento": self.output.name, "fecha_documental": DOCUMENT_DATE, "corte_referencia": SOURCE_COMMIT, "capitulos": [{"numero": c.number, "titulo": c.title} for c in CHAPTERS], "contenido": self.content_entries, "capturas": self.figure_entries, "fuentes": [{"id": source_id, "referencia": ref} for ref, source_id in self.sources.entries.items()], "advertencias": self.warnings, "estado_qa": "Pendiente de renderizado e inspección de todas las páginas"}
        (qa / "estructura_manual.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"docx": str(self.output), "capitulos": len(CHAPTERS), "secciones": len(self.content_entries), "capturas_originales": len(self.figure_entries), "fuentes": len(self.sources.entries), "qa": "Pendiente de renderizado e inspección de todas las páginas"}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Maqueta el manual BI editable sin consultar la aplicación.")
    parser.add_argument("--project-dir", type=Path, default=BASE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--font", default="Calibri")
    parser.add_argument("--font-size", type=float, default=11.5)
    parser.add_argument("--omit-images", action="store_true")
    parser.add_argument("--max-figures", type=int, default=0, help="Límite sólo para borradores; 0 incorpora todos los originales registrados.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not 10.5 <= args.font_size <= 13:
        parser.error("El tamaño del cuerpo debe estar entre 10.5 y 13 puntos.")
    if args.max_figures < 0:
        parser.error("--max-figures debe ser cero o un entero positivo.")
    project = args.project_dir.resolve()
    output = (args.output or (project / "Manual_de_usuario_Plataforma_BI.docx")).resolve()
    builder = Builder(project, output, args)
    summary = builder.validate()
    if args.validate_only:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if Path(sys.executable).resolve() != RUNTIME_PYTHON.resolve():
        raise RuntimeError(f"Use el runtime autorizado: {RUNTIME_PYTHON}")
    builder.build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
