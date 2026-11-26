#!/usr/bin/env python3
r"""Compone el manual de aprendizaje sin modificar los insumos ni la aplicación.

Uso: python generar_manual.py [--compile]
Las capturas se conectan desde insumos/mapa_capturas.json; se admiten también
llamadas locales a \pantalla en manual_latex/capturas/<id_de_unidad>.tex.
Esos archivos opcionales no se sobrescriben.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from reservar_titulos import reserve_longtable_titles
from pasos_unidos import keep_training_steps

W = Path(__file__).resolve().parents[1]
OUT = W / 'manual_latex'
SECTIONS = OUT / 'secciones'
RES = OUT / 'recursos' / 'diagramas'
for folder in (OUT, SECTIONS, RES, OUT / 'capturas'):
    folder.mkdir(parents=True, exist_ok=True)

NAMES = ['introduccion_y_fundamentos.json', 'operacion_configuracion_y_catalogo.json', 'operacion_bi_etl_analitica.json', 'base_datos_manual.json']
DATA = {name: json.loads((W / 'insumos' / name).read_text(encoding='utf-8')) for name in NAMES}
INTRO, CONFIG, BI, DB = [DATA[name] for name in NAMES]
COVERAGE: list[dict] = []
HOOKS: list[dict] = []
LAYOUT_EDITS: list[dict] = []
MAP_PATH = next((p for p in (W/'insumos/mapa_capturas.json', W/'mapa_capturas.json') if p.exists()), None)
PHOTO_MAP = json.loads(MAP_PATH.read_text(encoding='utf-8')) if MAP_PATH else {}
UPDATES_PATH = W/'insumos'/'actualizacion_20261125'/'actualizaciones_operacion.json'
UPDATES = json.loads(UPDATES_PATH.read_text(encoding='utf-8'))['units'] if UPDATES_PATH.exists() else {}
if isinstance(PHOTO_MAP, dict) and isinstance(PHOTO_MAP.get('units'), dict):
    PHOTO_MAP = PHOTO_MAP['units']
elif isinstance(PHOTO_MAP, dict) and isinstance(PHOTO_MAP.get('capturas'), dict):
    PHOTO_MAP = PHOTO_MAP['capturas']

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def esc(value) -> str:
    """Texto literal Unicode; los identificadores largos admiten salto tras separadores."""
    if value is None:
        return 'No aplica'
    if isinstance(value, bool):
        return 'Sí' if value else 'No'
    value = str(value).replace('\u00a0', ' ').replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_\allowbreak{}', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '→': r'\(\rightarrow\)', '←': r'\(\leftarrow\)', '↔': r'\(\leftrightarrow\)', '×': r'\(\times\)', '÷': r'\(\div\)', '≥': r'\(\geq\)', '≤': r'\(\leq\)', '≠': r'\(\neq\)'}
    return ''.join(mapping.get(c, c) for c in value)

def code(value) -> str:
    return r'\texttt{\seqsplit{' + esc(value).replace(r'\allowbreak{}', '') + '}}'

def para(value) -> str:
    if value is None or value == '':
        return ''
    return esc(value) + '\n\n'

def paragraphs(items) -> str:
    if isinstance(items, str):
        return para(items)
    return ''.join(para(x) for x in (items or []))

def heading(title, level='subsection') -> str:
    return '\\' + level + '{' + esc(title) + '}\n'

def table_heading(title, level='subsection') -> str:
    # longtable puede empezar en la página siguiente; reserva título,
    # encabezados y una primera fila sin forzar cada subsección al mismo alto.
    return '\\Needspace{8\\baselineskip}\n' + heading(title, level)

def bullets(items) -> str:
    if not items:
        return ''
    return '\\begin{itemize}\n' + ''.join('\\item ' + esc(x) + '\n' for x in items) + '\\end{itemize}\n\n'

def numbered(items) -> str:
    if not items:
        return ''
    return '\\begin{enumerate}\n' + ''.join('\\item ' + esc(x) + '\n' for x in items) + '\\end{enumerate}\n\n'

def table(headers: list[str], rows: list[list], widths: list[float] | None = None, raw=False) -> str:
    if not rows:
        return ''
    n = len(headers)
    if n > 3:
        # Conserva todas las celdas de ejemplos anchos en tres columnas legibles.
        middle = 1 + (n-1)//2
        rows = [[esc(row[0]), r'\par\smallskip'.join(r'\textbf{' + esc(headers[i]) + ':} ' + esc(row[i]) for i in range(1,middle)), r'\par\smallskip'.join(r'\textbf{' + esc(headers[i]) + ':} ' + esc(row[i]) for i in range(middle,n))] for row in rows]
        headers = [headers[0], 'Descripción', 'Datos del ejemplo']
        n, raw = 3, True
    assert 2 <= n <= 3
    widths = widths or ([.27, .66] if n == 2 else [.22, .30, .39])
    specs = '@{}' + ''.join('>{\\RaggedRight\\arraybackslash}p{' + str(x) + '\\linewidth}' for x in widths) + '@{}'
    head = ' & '.join('\\textbf{' + esc(x) + '}' for x in headers) + r' \\' + '\n'
    content = ['\\begingroup\n\\fontsize{10}{12.5}\\selectfont\n\\setlength{\\tabcolsep}{5pt}\n\\renewcommand{\\arraystretch}{1.15}\n', '\\begin{longtable}{' + specs + '}\n\\toprule\n', head, '\\midrule\n\\endfirsthead\n\\toprule\n', head, '\\midrule\n\\endhead\n\\midrule\n\\multicolumn{' + str(n) + '}{r}{\\footnotesize Continúa en la página siguiente}\\\\\n\\endfoot\n\\bottomrule\n\\endlastfoot\n']
    for row in rows:
        assert len(row) == n
        content.append(' & '.join(str(v) if raw else esc(v) for v in row) + r' \\' + '\n\\addlinespace[3pt]\n')
    content.append('\\end{longtable}\n\\endgroup\n\n')
    return ''.join(content)

def label(key):
    return {'titulo': 'Título', 'codigo': 'Identificación de práctica', 'estado': 'Estado de la evidencia', 'fuente': 'Fuente', 'nivel': 'Nivel', 'necesidad_para_copiar': 'Necesidad para la práctica', 'preguntas': 'Preguntas de negocio', 'periodicidad': 'Periodicidad', 'grano': 'Granularidad', 'indicadores': 'Indicadores', 'criterios_de_exito': 'Criterios de éxito', 'referencia_numerica': 'Referencia numérica', 'rutas_a_comprobar': 'Rutas que deben comprobarse', 'pasos_especificos': 'Pasos específicos', 'historico': 'Resultados del caso histórico', 'pregunta_chat_para_copiar': 'Pregunta para el copiloto', 'fecha': 'Fecha', 'propuesta': 'Propuesta', 'ejecucion': 'Ejecución', 'filas_origen': 'Filas de origen', 'filas_destino': 'Filas de destino', 'diferencia_filas': 'Diferencia de filas', 'tablas': 'Tablas', 'global': 'Selección completa', 'filtro': 'Selección filtrada', 'anio': 'Año', 'territorio': 'Territorio', 'importe_exacto': 'Importe exacto', 'moneda': 'Moneda', 'unidades': 'Unidades', 'pedidos_distintos': 'Pedidos distintos', 'facturas_distintas': 'Facturas distintas', 'importe_por_pedido_exacto': 'Importe por pedido exacto', 'importe_por_factura_exacto': 'Importe por factura exacto', 'mes_mayor_unidades': 'Mes de mayor cantidad', 'unidades_mes_lider': 'Unidades del mes de mayor cantidad', 'interpretacion': 'Interpretación de etiquetas', 'exportacion': 'Exportación', 'esperado': 'Resultado esperado', 'caso': 'Caso', 'tipo': 'Tipo de comprobación'}.get(key, key.replace('_', ' ').capitalize())

def structured(value, level='subsubsection') -> str:
    """Conserva contenido de prácticas adicionales sin convertir documentos en una celda gigante."""
    if isinstance(value, str):
        return para(value)
    if isinstance(value, (int, float, bool)):
        return para(value)
    if isinstance(value, list):
        if not value:
            return ''
        if all(not isinstance(x, (dict, list)) for x in value):
            return bullets(value)
        if all(isinstance(x, dict) and 'criterio' in x and 'evidencia' in x for x in value):
            return table(['Criterio', 'Puntos máximos', 'Evidencia que se espera'], [[x['criterio'], x.get('maximo', ''), x['evidencia']] for x in value])
        if all(isinstance(x, dict) and 'puntos' in x and 'descripcion' in x for x in value):
            return table(['Puntos', 'Descripción'], [[x['puntos'], x['descripcion']] for x in value])
        return ''.join(structured(x, level) for x in value)
    if isinstance(value, dict):
        result = ''
        title = value.get('titulo') or value.get('title')
        if title:
            result += heading(title, level)
        simple = [(k, v) for k, v in value.items() if not isinstance(v, (dict, list)) and k not in ('titulo', 'title')]
        # Valores breves en una tabla, texto extenso en prosa; no se sacrifica el ancho.
        short = [(k, v) for k, v in simple if len(str(v)) <= 160]
        if short:
            result += table(['Dato', 'Contenido'], [[label(k), v] for k, v in short])
        for k, v in simple:
            if len(str(v)) > 160:
                result += '\\paragraph{' + esc(label(k)) + '} ' + para(v)
        for k, v in value.items():
            if isinstance(v, (list, dict)) and v:
                child_level = {'section': 'subsection', 'subsection': 'subsubsection', 'subsubsection': 'paragraph', 'paragraph': 'paragraph'}.get(level, 'paragraph')
                result += heading(label(k), child_level) + structured(v, child_level)
        return result
    return para(value)

def training_section(s):
    """Lee las ocho unidades canónicas de guiones y defensa como un manual,
    sin imprimir la copia de validación del primer nivel del JSON."""
    result = heading(s['titulo'], 'section')
    if s.get('objetivo_de_aprendizaje'):
        result += '\\textbf{Al terminar podrá:} ' + para(s['objetivo_de_aprendizaje'])
    result += paragraphs(s.get('introduccion'))
    for key, value in s.items():
        if key in ('codigo', 'titulo', 'objetivo_de_aprendizaje', 'introduccion') or not value:
            continue
        if key == 'autoevaluacion':
            for q in value:
                result += '\\paragraph{' + esc(q['pregunta']) + '} ' + para(q['respuesta_orientativa'])
                result += '\\textbf{Cómo sostener la respuesta:} ' + para(q['evidencia_o_actividad'])
        elif key == 'presupuestos_y_contingencia':
            result += table_heading('Tiempo previsto y alternativas')
            result += table(['Condición', 'Cómo organizarse'], [[label(k), v] for k, v in value.items()])
        elif key == 'pasos':
            bodies = []
            for step in value:
                body = '\\textbf{Minutos ' + esc(step['intervalo_minutos']) + '.} ' + para(step['accion'])
                duration = step['duracion_maxima_guion_minutos']
                body += '{\\small\\textbf{Tiempo máximo previsto de este bloque:} ' + esc(duration) + (' minuto.' if duration == 1 else ' minutos.') + '\\par}\n'
                body += '\\textbf{Qué debe observar:} ' + para(step['resultado_que_debe_observar'])
                body += '\\textbf{Qué registrar:} ' + para(step['evidencia_a_registrar'])
                body += '\\textbf{Si no se cumple:} ' + para(step['si_no_se_cumple'])
                bodies.append(body)
            result += keep_training_steps(bodies, heading('Guion paso a paso'))
        elif key == 'criterios_de_cierre':
            result += heading('Antes de dar por terminado el ejercicio') + bullets(value)
        elif key == 'textos_basicos_para_copiar':
            result += heading('Necesidades básicas para la práctica')
            for case in value:
                result += '\\paragraph{' + esc(case['fuente']) + '} ' + para(case['texto']) + para(case['estado'])
        elif key == 'errores_y_recuperacion':
            result += table_heading('Reconocer la situación y actuar con criterio')
            result += table(['Qué ocurre', 'Qué hacer', 'Qué no debe afirmarse'], [[x['situacion'], x['accion'], x['no_declarar']] for x in value])
        elif key == 'rubrica':
            if value['uso'] not in s.get('introduccion', []):
                result += para(value['uso'])
            result += '\\textbf{Puntuación máxima:} ' + esc(value['puntuacion_maxima']) + ' puntos.\n\n'
            result += structured(value['criterios'])
            result += table_heading('Cómo asignar los puntos') + structured(value['escala'])
            result += para(value['criterios_no_observados']) + para(value['interpretacion'])
            result += heading('Condiciones que obligan a detenerse y corregir') + bullets(value['condiciones_criticas'])
        elif key == 'hoja_de_registro':
            result += paragraphs([instruction for instruction in value['instrucciones'] if instruction not in s.get('introduccion', [])])
            result += table_heading('Datos de contexto de su práctica')
            result += table(['Dato que debe registrar', 'Valor de su ejecución'], [[label(k), ' ' * 8] for k in value['contexto']])
            result += heading('Tipos de actividad') + bullets(value['opciones_tipo_actividad'])
            result += heading('Estados que puede registrar') + bullets(value['opciones_estado'])
            for tabkey, title in [('tabla_comprobaciones', 'Registro de comprobaciones'), ('tabla_rubrica', 'Registro de autoevaluación')]:
                tbl = value[tabkey]
                result += table_heading(title)
                columns = tbl['columnas']
                rows = [list(row.values()) if isinstance(row, dict) else row for row in tbl['filas']]
                result += table(columns, rows)
            result += heading('Conclusión de la práctica') + structured(value['cierre'])
        elif key == 'casos_de_referencia':
            for case in value:
                result += heading(case['fuente']) + structured({k: v for k, v in case.items() if k != 'fuente'})
        else:
            result += heading(label(key)) + structured(value)
    return result

def current_update(identifier):
    """Integra el insumo vigente en la unidad pertinente; no regenera la historia."""
    u = UPDATES.get(identifier)
    if not u:
        return ''
    result = heading(u['title']) + paragraphs(u.get('paragraphs'))
    result += numbered(u.get('steps'))
    if u.get('table'):
        t = u['table']
        result += table_heading(t['title']) + table(t['headers'], t['rows'])
    result += paragraphs(u.get('after_table'))
    if u.get('screenshot'):
        photo = u['screenshot']
        source = W/'capturas'/'actualizacion_20261125'/photo['file']
        dest = OUT/'recursos'/'pantallas'/photo['file']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        result += r'\pantallaactual{recursos/pantallas/' + dest.name + '}{' + esc(photo['title']) + '}{' + esc(photo['caption']) + '}\n'
    return result

def hook(identifier, title):
    HOOKS.append({'id': identifier, 'title': title, 'file': f'capturas/{identifier}.tex', 'usage': r'\pantalla{../capturas/archivo.jpg}{Título de la pantalla}{Qué debe observar y comprobar.}'})
    result = ''
    photos = PHOTO_MAP.get(identifier, []) if isinstance(PHOTO_MAP, dict) else []
    if isinstance(photos, dict):
        photos = photos.get('photos', photos.get('capturas', [photos]))
    for photo in photos:
        filename = photo.get('file', photo.get('archivo'))
        caption = photo.get('caption', photo.get('leyenda', photo.get('nota', '')))
        photo_title = photo.get('title', photo.get('titulo', title))
        if not filename:
            raise ValueError(f'Captura sin archivo: {identifier}')
        image_path = Path(filename)
        if not image_path.is_absolute():
            image_path = W/'capturas'/image_path
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        dest = OUT/'recursos'/'pantallas'/image_path.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(image_path, dest)
        result += '\\pantalla{recursos/pantallas/' + dest.name + '}{' + esc(photo_title) + '}{' + esc(caption) + '}\n'
    return result + '\n\\IfFileExists{capturas/' + identifier + '.tex}{\\input{capturas/' + identifier + '.tex}}{}\n'

def diagram(filename, title, note):
    source = W / 'figuras' / filename
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, RES / filename)
    svg = source.with_suffix('.svg')
    if svg.exists():
        shutil.copy2(svg, RES / svg.name)
    return '\\diagramasistema{recursos/diagramas/' + filename + '}{' + esc(title) + '}{' + esc(note) + '}\n'

def foundation(chapter, index):
    result = '\\chapter{' + esc(chapter['title']) + '}\n' + paragraphs(chapter.get('paragraphs'))
    if index == 0:
        result += '\\Needspace{36\\baselineskip}\n' + table_heading('Dónde encontrar cada opción', 'section')
        result += para('Puede abrir la unidad desde la última columna. El menú visible depende de los permisos de su sesión; el enlace del manual no concede acceso a la aplicación.')
        menu_rows = [
            ('Inicio', 'Reconocer la preparación y la fuente de trabajo.', 'operacion_02'),
            ('Conexiones de datos', 'Registrar y comprobar el acceso a cada origen.', 'operacion_09'),
            ('Parámetros', 'Comprender los valores generales de operación.', 'operacion_10'),
            ('Configuración LLM', 'Preparar y comprobar el proveedor de IA.', 'operacion_11'),
            ('Explorador de esquema', 'Revisar tablas, columnas y relaciones capturadas.', 'operacion_12'),
            ('Catálogo analítico', 'Definir preguntas y opciones propias de cada fuente.', 'operacion_13'),
            ('Asistente de datamart', 'Convertir la necesidad en una propuesta supervisada.', 'BI02'),
            ('Datamart de ventas', 'Preparar, confirmar y conciliar una carga.', 'ETL01'),
            ('Analítica de ventas', 'Filtrar, interpretar, conversar y exportar.', 'AN01'),
            ('Usuarios', 'Administrar cuentas y asignaciones de acceso.', 'operacion_04'),
            ('Roles', 'Agrupar permisos de acuerdo con responsabilidades.', 'operacion_05'),
            ('Permisos', 'Consultar qué autoriza cada capacidad.', 'operacion_06'),
            ('Menús', 'Comprender la navegación y su visibilidad.', 'operacion_07'),
            ('Auditoría', 'Consultar los eventos registrados por la aplicación.', 'operacion_08'),
        ]
        result += table(['Opción visible', 'Para qué acudir', 'Unidad del manual'], [[esc(name), esc(purpose), '\\hyperref[unidad:' + identifier + ']{Abrir sección \\ref*{unidad:' + identifier + '}}'] for name,purpose,identifier in menu_rows], [.25,.44,.22], raw=True)
    for s in chapter.get('sections', []):
        result += heading(s['title'], 'section')
        result += paragraphs(s.get('paragraphs'))
        if s.get('table'):
            result += table(s['table']['headers'], s['table']['rows'])
        result += numbered(s.get('steps'))
    COVERAGE.append({'source': NAMES[0], 'path': f'chapters[{index}]', 'title': chapter['title'], 'rendered': True})
    return result + hook(f'fundamentos_{index+1:02d}', chapter['title'])

def config_section(s, index):
    result = heading(s['title'], 'section') + '\\label{unidad:' + s['id'] + '}\n'
    result += '\\textbf{Para quién:} ' + esc(', '.join(s['audience'])) + '\\par\n'
    result += '\\textbf{Opción:} ' + esc(s['ui_path']) + '\\par\n\n'
    result += paragraphs(s['paragraphs'])
    result += current_update(s['id'])
    if s['id'] == 'operacion_05':
        roles_path = W/'insumos'/'roles_permisos_actuales_sin_usuarios.json'
        if roles_path.exists():
            observed_roles = json.loads(roles_path.read_text(encoding='utf-8'))
            result += heading('Roles y permisos observados en la instalación de referencia')
            result += para('La siguiente relación procede de una consulta de definiciones de roles y permisos, sin cuentas ni asignaciones de personas. Describe la configuración observada; no acredita una sesión autenticada ni una prueba integral bajo cada perfil. Una instalación limpia puede conservar únicamente el perfil administrativo base.')
            descriptions = {'Administrador': 'Perfil protegido de administración con los 29 permisos base.', 'Operador': 'Configuración local de cuatro permisos específicos; no representa un perfil completo de operación ni acredita acceso a todos los módulos.', 'Analista BI': 'Configuración local para diseñar, revisar y materializar con consulta de contexto, catálogo, auditoría y analítica.', 'Gerente comercial': 'Consulta analítica, conexiones sin secretos, metadatos y exportación. No incluye ETL ni aprobación de propuestas.'}
            result += table(['Perfil', 'Permisos activos', 'Alcance observado'], [[r['role_name'], sum(p['is_active'] for p in r['permissions']), descriptions.get(r['role_name'],'Configuración local.')] for r in observed_roles])
            for role in observed_roles:
                result += '\\paragraph{' + esc(role['role_name']) + '}\n'
                result += table(['Permiso concedido', 'Estado'], [[p['name'], 'Activo' if p['is_active'] else 'Inactivo'] for p in role['permissions']])
            result += para('Gerente comercial necesita Consultar metadatos porque el selector actual de fuentes utiliza esa consulta. También puede abrir el Explorador en lectura; ese permiso no concede actualización de metadatos ni ejecución ETL. En Operador, Probar conexiones y Administrar parámetros no incluyen por sí solos los permisos de consulta complementarios: no se asume que pueda recorrer sus pantallas completas.')
    result += heading('Conceptos para comprender la opción')
    for c in s['concepts']:
        result += '\\paragraph{' + esc(c['term']) + '} ' + esc(c['explanation']) + (' ' + esc(c['example']) if c.get('example') else '') + '\n\n'
    result += heading('Paso a paso') + numbered(s['steps'])
    result += table_heading('Campos y botones')
    rows = []
    for c in s['controls']:
        rows.append([esc(c['name']), esc(c['purpose']), '\\textbf{Ejemplo:} ' + esc(c['example']) + '\\par\\smallskip\\textbf{Resultado:} ' + esc(c['result'])])
    result += table(['Control', 'Para qué sirve', 'Ejemplo y resultado'], rows, raw=True)
    for p in s['practice']:
        result += heading(p['title']) + para(p['evidence_status']) + numbered(p['steps'])
        result += '\\textbf{Qué debe obtener.} ' + esc(' '.join(p['expected_results'])) + '\n\n'
        result += '\\textbf{Cómo comprobarlo.} ' + para(p['success_criterion'])
    result += table_heading('Si aparece un problema')
    rows = []
    for e in s['errors']:
        rows.append([esc(e['symptom']), esc(e['possible_cause']), esc(e['action']) + '\\par\\smallskip\\textbf{Comprobación:} ' + esc(e['verification'])])
    result += table(['Qué observa', 'Causa posible', 'Qué hacer y comprobar'], rows, raw=True)
    result += heading('Para explicar durante la sustentación')
    for q in s['defense_qa']:
        result += '\\paragraph{' + esc(q['question']) + '} ' + para(q['answer'])
    COVERAGE.append({'source': NAMES[1], 'path': f'sections[{index}]', 'title': s['title'], 'rendered': True})
    if s['id'] in ('operacion_08', 'operacion_12', 'operacion_14'):
        result = '\\begingroup\n\\setlength{\\parskip}{4pt plus 1pt minus 1pt}\n\\setlist[enumerate]{itemsep=3pt,topsep=4pt}\n\\titlespacing*{\\paragraph}{0pt}{4pt}{0.5em}\n' + result + '\\endgroup\n'
    return result + hook(s['id'], s['title'])

def bi_section(s, index):
    display_title = re.sub(r'^(Asistente|Materialización) paso (\d+) (.+)$', lambda m: f'{m[1]}, paso {m[2]}: {m[3]}', s['titulo'])
    display_title = {'Antes de empezar piense qué decisión necesita apoyar': 'Antes de empezar: piense qué decisión necesita apoyar', 'Costos descuentos y márgenes una ampliación que exige evidencia': 'Costos, descuentos y márgenes: una ampliación que exige evidencia'}.get(display_title, display_title)
    result = heading(display_title, 'section') + '\\label{unidad:' + s['codigo'] + '}\n'
    result += '\\textbf{Para quién:} ' + esc(', '.join(s['roles'])) + '\\par\n'
    result += '\\textbf{Al terminar podrá:} ' + para(s['objetivo_de_aprendizaje'])
    result += paragraphs(s['introduccion'])
    result += current_update(s['codigo'])
    result += heading('Conceptos para decidir con criterio')
    for c in s['conceptos']:
        result += '\\paragraph{' + esc(c['termino']) + '} ' + para(c['explicacion'])
    result += table_heading('Campos y controles')
    result += table(['Campo o control', 'Significado y criterio'], [[x['campo'], x['significado_y_criterio']] for x in s['campos_y_controles']])
    result += heading('Paso a paso')
    result += '\\begin{enumerate}\n'
    for p in s['pasos']:
        result += '\\item ' + esc(p['accion']) + '\\par\\nopagebreak[4]\\smallskip{\\small\\textbf{Compruebe:} ' + esc(p['resultado_que_debe_observar']) + '}\n'
    result += '\\end{enumerate}\n'
    for key, title in [('que_hace_la_IA', 'Qué hace la IA'), ('que_valida_la_plataforma', 'Qué comprueba la plataforma'), ('que_decide_o_aprueba_la_persona', 'Qué decide la persona')]:
        result += heading(title) + paragraphs(s[key])
    result += '\\paragraph{Resultado esperado} ' + para(s['resultado_esperado'])
    result += table_heading('Errores y recuperación') + table(['Situación', 'Qué hacer'], [[x['situacion'], x['accion']] for x in s['errores_y_recuperacion']])
    result += heading('Ejercicio') + para(s['ejercicio']['consigna']) + '\\textbf{Respuesta orientativa.} ' + para(s['ejercicio']['respuesta_orientativa'])
    result += heading('Compruebe lo que aprendió')
    for q in s['autoevaluacion']:
        result += '\\paragraph{' + esc(q['pregunta']) + '} ' + para(q['respuesta_orientativa'])
    for key, title in [('practicas', 'Casos para practicar'), ('regresiones_para_practicar', 'Escenarios de comprobación y rechazo esperado')]:
        if s.get(key):
            result += heading(title) + structured(s[key])
    COVERAGE.append({'source': NAMES[2], 'path': f'secciones[{index}]', 'title': s['titulo'], 'display_title': display_title, 'rendered': True})
    if s['codigo'] in ('ETL01', 'ETL05', 'ETL06', 'AN02'):
        result = '\\begingroup\n\\setlength{\\parskip}{4pt plus 1pt minus 1pt}\n\\setlist[enumerate]{itemsep=3pt,topsep=4pt}\n\\titlespacing*{\\paragraph}{0pt}{4pt}{0.5em}\n' + result + '\\endgroup\n'
    return result + hook(s['codigo'], display_title)

def dictionary_table(t, index, group):
    result = heading(t['tabla'], 'subsection')
    for k, title in [('area', 'Área'), ('que_guarda', 'Qué guarda'), ('como_se_usa', 'Cómo se utiliza')]:
        if t.get(k):
            result += '\\paragraph{' + title + '} ' + para(t[k])
    rows = []
    for c in t['columnas']:
        condition = esc(c['type']) + '\\par\\smallskip ' + ('Admite nulos.' if c['nullable'] else 'Obligatorio.')
        if c.get('clave_primaria'):
            condition += ' Clave primaria.'
        if c.get('has_default'):
            condition += ' Con valor predeterminado.'
        if c.get('identity'):
            condition += ' Identidad: ' + esc(c['identity']) + '.'
        if c.get('generated'):
            condition += ' Generación: ' + esc(c['generated']) + '.'
        rows.append([code(c['name']), condition, esc(c['explicacion'])])
    result += table(['Columna', 'Tipo y condición', 'Qué representa'], rows, [.23, .23, .45], raw=True)
    constraints = t.get('restricciones', [])
    if constraints:
        result += '\\paragraph{Restricciones físicas observadas} '
        texts = []
        for c in constraints:
            kind = {'p': 'Clave primaria', 'u': 'Unicidad', 'f': 'Clave foránea', 'c': 'Comprobación'}.get(c['kind'], c['kind'])
            text = kind + ': ' + ', '.join(c.get('columns') or [])
            if c.get('reference_table'):
                text += ' hacia ' + c['reference_schema'] + '.' + c['reference_table'] + ' (' + ', '.join(c.get('reference_columns') or []) + ')'
                text += '; al eliminar: ' + {'c': 'cascada SQL', 'n': 'referencia nula', 'a': 'sin acción SQL', 'r': 'restricción', 'd': 'predeterminado'}.get(c.get('delete_action', '').strip(), 'regla no indicada')
            texts.append(text + '.')
        result += bullets(texts)
    if t.get('indices_unicos'):
        result += '\\paragraph{Índices únicos} ' + bullets([', '.join(i.get('columns') or []) + ('; índice parcial.' if i.get('partial') else '; índice completo.') for i in t['indices_unicos']])
    COVERAGE.append({'source': NAMES[3], 'path': f'{group}[{index}]', 'title': t['tabla'], 'rendered': True, 'columns_rendered': len(t['columnas'])})
    return result

def write(name, text):
    text, edits = reserve_longtable_titles(text)
    LAYOUT_EDITS.extend([{'section_file': name, **edit} for edit in edits])
    (SECTIONS / name).write_text(text, encoding='utf-8')

includes = []
for i, c in enumerate(INTRO['chapters']):
    text = foundation(c, i)
    if i == 2:
        text += diagram('Arquitectura_plataforma.pdf', 'Arquitectura de la plataforma', 'Interfaz, servicios, fuentes de lectura, persistencia y proveedor de IA. La aplicación comprueba las reglas y una persona autoriza el diseño y confirma la carga por separado.')
    name = f'{i+1:02d}_fundamentos.tex'
    write(name, text); includes.append(name)

groups = [(0, 3, 'Ingresar, orientarse y elegir la fuente'), (8, 12, 'Preparar las fuentes y el asistente de IA'), (12, 14, 'Configurar el catálogo con criterio comercial')]
for i, (start, end, title) in enumerate(groups, 4):
    text = '\\chapter{' + title + '}\n'
    for index in range(start, end):
        text += config_section(CONFIG['sections'][index], index)
    if start == 12:
        text += heading('Seis orientaciones comerciales y cómo redactarlas', 'section')
        text += para('Estos textos son ejemplos de capacitación. No se aplicaron a ningún catálogo durante la redacción; revíselos según el respaldo de la fuente antes de incorporarlos.')
        for q in CONFIG['business_question_examples']:
            text += heading(q['label']) + para(q['classification']) + '\\textbf{Explicación para el analista.} ' + para(q['description']) + '\\textbf{Instrucción funcional para la IA.} ' + para(q['prompt_instruction'])
    name = f'{i:02d}_configuracion.tex'; write(name, text); includes.append(name)

bi_groups = [(0, 7, 'Del objetivo comercial a una propuesta supervisada'), (7, 13, 'Materializar, conciliar y revisar los resultados'), (13, 17, 'Analizar, conversar y exportar con contexto')]
for i, (start, end, title) in enumerate(bi_groups, 7):
    text = '\\chapter{' + title + '}\n'
    for index in range(start, end):
        text += bi_section(BI['secciones'][index], index)
    name = f'{i:02d}_operacion_bi.tex'; write(name, text); includes.append(name)

security_text = '\\chapter{Administrar cuentas, permisos y trazabilidad}\n'
for index in range(3, 8):
    security_text += config_section(CONFIG['sections'][index], index)
write('10_administracion.tex', security_text); includes.append('10_administracion.tex')

practice_text = '\\chapter{Practicar, resolver incidencias y preparar la defensa}\n'
for index in range(17, len(BI['secciones'])):
    practice_text += bi_section(BI['secciones'][index], index)
PRACTICE_PATH = W/'insumos'/'operacion_practicas_y_defensa.json'
if PRACTICE_PATH.exists():
    extra = json.loads(PRACTICE_PATH.read_text(encoding='utf-8'))
    for key in ('sections', 'secciones', 'chapters'):
        if isinstance(extra.get(key), list):
            for i, value in enumerate(extra[key]):
                practice_text += training_section(value)
                COVERAGE.append({'source': PRACTICE_PATH.name, 'path': f'{key}[{i}]', 'title': value.get('title', value.get('titulo', str(i+1))), 'rendered': True})
            break
    else:
        practice_text += structured(extra, 'section')
        COVERAGE.append({'source': PRACTICE_PATH.name, 'path': '$', 'title': extra.get('title', extra.get('titulo','Prácticas y defensa')), 'rendered': True})
write('11_practica.tex', practice_text); includes.append('11_practica.tex')

dbtext = '\\chapter{Comprender la base de datos y el linaje}\n'
for i, s in enumerate(DB['secciones']):
    dbtext += heading(s['titulo'], 'section') + para(s['texto'])
    COVERAGE.append({'source': NAMES[3], 'path': f'secciones[{i}]', 'title': s['titulo'], 'rendered': True})
dbtext += heading('Esquemas conservados en la instalación de referencia', 'section')
dbtext += table(['Esquema', 'Tablas observadas'], [[x['name'], x['table_count']] for x in DB['esquemas_observados']])
dbtext += heading('Relación comprobada entre los casos de demostración', 'section')
dbtext += table(['Fuente', 'Diseño y metadatos', 'Ejecución'], [[x['database_name'], f"Propuesta {x['proposal_id']} ({x['proposal_status']}); instantánea {x['metadata_snapshot_id']}.", f"Expediente {x['execution_id']} ({x['execution_status']})."] for x in DB['linaje_verificado_sin_json']])
manifest = json.loads((W / 'figuras' / 'manifest_figuras_datos.json').read_text())
for figure in sorted([f for f in manifest if f['archivo_svg'].startswith('ER_')], key=lambda f: f['archivo_svg']):
    dbtext += diagram(figure['archivo_svg'].replace('.svg', '.pdf'), figure['titulo'], figure['nota'])
dbtext += heading('Diccionario de las tablas de la aplicación', 'section')
dbtext += para('El nombre de cada tabla y columna coincide con el inventario observado. Estas fichas ayudan a comprender lo que guarda la plataforma; las tareas de operación se realizan desde la interfaz, sin modificar estas tablas con SQL.')
for i, t in enumerate(DB['tablas_app']):
    dbtext += dictionary_table(t, i, 'tablas_app')
dbtext += heading('Diccionario de los dos datamarts de demostración', 'section')
dbtext += para('Los campos físicos pertenecen a los expedientes de referencia. Un diseño nuevo puede producir otro conjunto de atributos. Una relación lógica del materializador no debe confundirse con una clave foránea física que la base no ha declarado.')
for i, t in enumerate(DB['tablas_fisicas_demostracion']):
    dbtext += dictionary_table(t, i, 'tablas_fisicas_demostracion')
dbtext += heading('Alcance del inventario y límites', 'section') + paragraphs(DB['limites'])
# El inventario histórico y los diagramas se conservan en la revisión editorial auditada.
db_override = W/'insumos'/'actualizacion_20261125'/'12_base_datos.tex'
if db_override.exists():
    dbtext = db_override.read_text(encoding='utf-8')
write('12_base_datos.tex', dbtext); includes.append('12_base_datos.tex')

perms = CONFIG['permission_manifest']
appendix = '\\chapter{Responsabilidades, permisos y precisión de esta edición}\n' + para(perms['status'])
appendix += heading('Lectura de la matriz', 'section') + paragraphs(perms['recommended_role_notes'])
appendix += heading('Permisos de la plataforma', 'section')
for p in perms['items']:
    appendix += heading(p['visible_name']) + para(p['catalog_description'])
    appendix += '\\textbf{Referencia técnica:} ' + code(p['technical_code_for_developers']) + '\\par\n'
    appendix += table(['Perfil', 'Tratamiento en la formación'], [['Administración', p['administrator_baseline']], ['Analista de BI', p['training_analyst_proposal']], ['Gerencia comercial', p['training_manager_proposal']]])
    if p.get('note'):
        appendix += para(p['note'])
appendix += heading('Dependencias que deben comprobarse', 'section') + table(['Operación', 'Permisos y condición'], [[d['operation'], d['requirement']] for d in perms['dependencies']])
appendix += heading('Precisiones respecto de documentación anterior', 'section')
for p in CONFIG['implementation_precision']:
    appendix += heading(p['topic']) + para(p['fact']) + para(p['manual_treatment'])
appendix += heading('Origen de los contenidos y de los ejemplos', 'section')
appendix += para('Esta edición integra la lectura de código y especificaciones, las capturas históricas del 18 de noviembre y las comprobaciones operativas del 25 de noviembre. Los casos 135/23 y 136/24 son recorridos nuevos comprobados con OpenAI Sol. Luna sólo tiene comprobación mínima de conexión y JSON. Los ejercicios para que el grupo practique siguen distinguiéndose de esas pruebas realizadas.')
appendix += paragraphs(BI.get('reglas_editoriales'))
appendix += para('El material base del 18 de noviembre se redactó sin nuevas propuestas ni ETL. La campaña adicional del 25 de noviembre sí incluyó configuración OpenAI, correcciones, propuestas aprobadas y ETL nuevos, documentados en sus unidades. Copiar y compilar este manual no vuelve a ejecutar esas operaciones. Las capturas actuales son vistas reales estrechas, conservadas sin estirar; no se presentan como nuevas capturas de escritorio completo.')
appendix += heading('Reproducir una práctica en otro equipo', 'section')
appendix += para('Un portable limpio no debe contener la API key privada ni todos los expedientes locales de quien preparó el proyecto. La administración registra su propia credencial, comprueba el proveedor y configura las fuentes. Los números 135, 136, 23 y 24 son referencias de esta instalación, no valores que deban forzarse en las bases. La guía de traslado vigente acompaña la entrega y debe usarse para puertos, credenciales locales y encendido.')
appendix += para('La política de ahorro consiste en elegir un modelo económico compatible, reducir clics repetidos y reutilizar evidencia conservada. No se recortan metadatos verificados, requisitos ni validaciones para abaratar una propuesta: esa pérdida de contexto puede dejar fuera un resultado obligatorio.')
appendix += heading('Fuentes para consultar modelos y facturación', 'section')
appendix += para('Las tarifas se consultaron el 25 de noviembre de 2026 en la documentación oficial de OpenAI. Pueden cambiar; verifique modelo y disponibilidad antes de una demostración.')
for url in ['https://developers.openai.com/api/docs/models/gpt-6-luna','https://developers.openai.com/api/docs/models/gpt-5.4-mini','https://developers.openai.com/api/docs/models/gpt-6.1-terra','https://developers.openai.com/api/docs/models/gpt-6.2-sol','https://developers.openai.com/api/docs/models/gpt-6.2-astra']:
    appendix += r'\url{' + url + r'}\par\smallskip' + '\n'
write('13_permisos_precision.tex', appendix); includes.append('13_permisos_precision.tex')

PREAMBLE = r'''\documentclass[11pt,a4paper,oneside,openany]{book}
\usepackage[spanish,es-nodecimaldot,es-noquoting]{babel}
\usepackage{fontspec}
\setmainfont{texgyrepagella-regular.otf}[Path=recursos/fuentes/,BoldFont=texgyrepagella-bold.otf,ItalicFont=texgyrepagella-italic.otf,BoldItalicFont=texgyrepagella-bolditalic.otf]
\setsansfont{texgyreheros-regular.otf}[Path=recursos/fuentes/,BoldFont=texgyreheros-bold.otf,ItalicFont=texgyreheros-italic.otf,BoldItalicFont=texgyreheros-bolditalic.otf]
\setmonofont{texgyrecursor-regular.otf}[Path=recursos/fuentes/,BoldFont=texgyrecursor-bold.otf,ItalicFont=texgyrecursor-italic.otf,BoldItalicFont=texgyrecursor-bolditalic.otf,Scale=MatchLowercase]
\usepackage[a4paper,margin=2.1cm,headheight=15pt,headsep=0.6cm,footskip=1cm]{geometry}
\usepackage{xcolor}
\definecolor{Azul}{HTML}{16324F}
\definecolor{Teal}{HTML}{007E80}
\definecolor{Gris}{HTML}{526171}
\usepackage{graphicx,booktabs,longtable,array,ragged2e,enumitem,pdflscape,needspace,titlesec,fancyhdr,microtype,seqsplit}
\usepackage[unicode,colorlinks=true,linkcolor=Azul,urlcolor=Teal,citecolor=Azul,bookmarksnumbered=true,pdfdisplaydoctitle=true]{hyperref}
\usepackage{bookmark}
\hypersetup{pdftitle={Manual de operación y aprendizaje de la plataforma BI con IA},pdfauthor={Proyecto académico BI - Universidad de Guayaquil},pdfsubject={Formación y operación supervisada de datamarts de ventas}}
\setcounter{tocdepth}{1}
\setcounter{secnumdepth}{1}
\renewcommand{\baselinestretch}{1.13}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt plus 1pt minus 1pt}
\setlength{\emergencystretch}{3em}
\tolerance=1800
\widowpenalty=10000
\clubpenalty=10000
\displaywidowpenalty=10000
\raggedbottom
\setlist[itemize]{leftmargin=1.5em,itemsep=3pt,topsep=4pt,parsep=2pt}
\setlist[enumerate]{leftmargin=1.7em,label=\textcolor{Teal}{\bfseries\arabic*.},itemsep=5pt,topsep=5pt,parsep=3pt}
\titleformat{\chapter}[display]{\RaggedRight\sffamily\bfseries\color{Azul}\hyphenpenalty=10000\exhyphenpenalty=10000}{\fontsize{11}{13}\selectfont CAPÍTULO \thechapter}{5pt}{\fontsize{24}{28}\selectfont}
\titlespacing*{\chapter}{0pt}{-8pt}{18pt}
\titleformat{\section}{\RaggedRight\sffamily\bfseries\large\color{Azul}\hyphenpenalty=10000\exhyphenpenalty=10000}{\thesection}{0.7em}{}
\titleformat{\subsection}{\sffamily\bfseries\normalsize\color{Teal}}{}{0pt}{}
\titleformat{\subsubsection}{\sffamily\bfseries\normalsize\color{Azul}}{}{0pt}{}
\titleformat{\paragraph}[runin]{\bfseries}{}{0pt}{}
\titlespacing*{\section}{0pt}{16pt}{7pt}
\titlespacing*{\subsection}{0pt}{11pt}{5pt}
\titlespacing*{\subsubsection}{0pt}{9pt}{4pt}
\titlespacing*{\paragraph}{0pt}{6pt}{0.5em}
\usepackage{etoolbox}
\makeatletter
\renewcommand*{\l@section}{\@dottedtocline{1}{1.5em}{3.3em}}
\makeatother
\pretocmd{\section}{\Needspace{5\baselineskip}}{}{}
\pretocmd{\subsection}{\Needspace{4\baselineskip}}{}{}
\pretocmd{\subsubsection}{\Needspace{4\baselineskip}}{}{}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\sffamily\footnotesize\color{Gris} PLATAFORMA BI + IA}
\fancyhead[R]{\sffamily\footnotesize\color{Gris} Operación y aprendizaje}
\fancyfoot[L]{\sffamily\footnotesize\color{Gris} Edición de formación 2.0 - 25 de noviembre de 2026}
\fancyfoot[R]{\sffamily\small\color{Azul}\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\sffamily\footnotesize\color{Gris} Manual de operación y aprendizaje}\fancyfoot[R]{\sffamily\small\thepage}\renewcommand{\headrulewidth}{0pt}}
\newcounter{pantallas}
\newcounter{diagramas}
\newcommand{\pantalla}[3]{%
  \clearpage\begin{landscape}\thispagestyle{empty}\begingroup
  \setlength{\parskip}{0pt}\phantomsection
  {\sffamily\bfseries\fontsize{14}{17}\selectfont\color{Azul}#2\par}
  \vspace{0.22cm}
  {\centering\includegraphics[width=25cm,height=13.8cm,keepaspectratio]{#1}\par}
  \vspace{0.18cm}\refstepcounter{pantallas}
  {\fontsize{10}{12}\selectfont\textbf{Pantalla \thepantallas.} #3\par}
  \vfill{\hfill\sffamily\footnotesize\thepage\par}
  \endgroup\end{landscape}%
}
\newcommand{\pantallaactual}[3]{%
  \clearpage\thispagestyle{plain}\begingroup
  {\sffamily\bfseries\large\color{Azul}#2\par}
  \vspace{0.3cm}
  {\centering\includegraphics[width=10.1cm,height=16.5cm,keepaspectratio]{#1}\par}
  \vspace{0.3cm}\refstepcounter{pantallas}
  {\small\textbf{Pantalla \thepantallas.} #3\par}
  \endgroup\clearpage
}
\newcommand{\diagramasistema}[3]{%
  \clearpage\begin{landscape}\thispagestyle{empty}\begingroup
  \setlength{\parskip}{0pt}\phantomsection
  {\sffamily\bfseries\fontsize{14}{17}\selectfont\color{Azul}#2\par}
  \vspace{0.22cm}
  {\centering\includegraphics[width=25cm,height=13.6cm,keepaspectratio]{#1}\par}
  \vspace{0.18cm}\refstepcounter{diagramas}
  {\fontsize{10}{12}\selectfont\textbf{Diagrama \thediagramas.} #3\par}
  \vfill{\hfill\sffamily\footnotesize\thepage\par}
  \endgroup\end{landscape}%
}
\begin{document}
\begin{titlepage}
\thispagestyle{empty}
{\sffamily\bfseries\color{Teal} UNIVERSIDAD DE GUAYAQUIL\par}
\vspace{0.35cm}
{\sffamily\color{Gris} Proyecto académico de inteligencia de negocios\par}
\vspace{2.0cm}
{\sffamily\bfseries\fontsize{30}{35}\selectfont\color{Azul} Manual de operación\par y aprendizaje\par}
\vspace{0.6cm}
{\sffamily\fontsize{20}{25}\selectfont\color{Teal} Plataforma BI con IA\par}
\vspace{0.8cm}
{\large Construcción supervisada de datamarts de ventas\par}
\vspace{0.5cm}
{\large Comprender, configurar, practicar y explicar\par}
\vspace{1cm}
{\color{Teal}\rule{\textwidth}{1.2pt}\par}
\vspace{0.6cm}
Para administración, analistas de BI, gerencia comercial\par
y programadoras del prototipo funcional.\par
\vfill
{\sffamily\color{Gris} Edición de formación 2.0\par 25 de noviembre de 2026\par}
\end{titlepage}
\frontmatter
\section*{Alcance de esta edición}
Esta edición de formación 2.0, del 25 de noviembre de 2026, integra las mejoras
operativas de navegación, sesiones, catálogo y cobertura de las propuestas,
así como la configuración de OpenAI y el criterio de costo de sus modelos.
Conserva los trece capítulos de la edición anterior, sus explicaciones,
sus 52 capturas de referencia del 18 de noviembre y sus ocho diagramas.
Añade tres vistas actuales, sin deformarlas ni presentarlas como capturas
de escritorio completo.

Las propuestas 129 y 131 y las ejecuciones 21 y 22 se mantienen como historia
de la campaña del 6 de noviembre. Los casos nuevos comprobados el 25 de
noviembre son AdventureWorks 136/24 y WideWorldImporters 135/23, con OpenAI
Sol y razonamiento Medio. La opción económica activa, OpenAI Luna con
razonamiento Bajo, sólo tiene una prueba mínima de conexión y salida
estructurada: su calidad BI completa sigue pendiente de una campaña propia.

Este manual permite estudiar y repetir el proceso, sin garantizar que
cualquier texto, modelo o motor produzca siempre una propuesta aprobable.
Las reglas verifican estructura y cálculos; la persona conserva la decisión
sobre significado comercial, alcance y uso del resultado. Los identificadores
son propios de cada instalación y cambian en un entorno limpio.

Las funciones de IA dependen de la disponibilidad del proveedor y pueden
consumir su cuota. El manual permite aprender con los expedientes conservados;
no exige generar otra propuesta ni repetir una carga para comprender el flujo.

\clearpage
\begingroup
\setlength{\parskip}{0pt}
\tableofcontents
\endgroup
\mainmatter
'''

main = PREAMBLE + '\n'.join('\\input{secciones/' + x + '}' for x in includes) + '\n\\end{document}\n'
(OUT / 'main.tex').write_text(main, encoding='utf-8')

expected = len(INTRO['chapters']) + len(CONFIG['sections']) + len(BI['secciones']) + len(DB['secciones']) + len(DB['tablas_app']) + len(DB['tablas_fisicas_demostracion'])
assert len([c for c in COVERAGE if c['source'] in NAMES]) == expected, (len(COVERAGE), expected)
assert len({(c['source'], c['path']) for c in COVERAGE}) == len(COVERAGE)
extra_inputs = [p for p in (UPDATES_PATH, W/'insumos'/'actualizacion_20261125'/'12_base_datos.tex', PRACTICE_PATH, W/'insumos'/'roles_permisos_actuales_sin_usuarios.json', MAP_PATH) if p and p.exists()]
mapped_ids = set(PHOTO_MAP) if isinstance(PHOTO_MAP, dict) else set()
assert not mapped_ids - {h['id'] for h in HOOKS}, mapped_ids - {h['id'] for h in HOOKS}
coverage = {'input_files': [{'file': str(W/'insumos'/name), 'sha256': sha(W/'insumos'/name)} for name in NAMES] + [{'file': str(p), 'sha256': sha(p)} for p in extra_inputs], 'base_units_expected': expected, 'units_rendered': len(COVERAGE), 'all_sections_rendered': True, 'dictionary_columns_rendered': sum(c.get('columns_rendered', 0) for c in COVERAGE), 'photos_mapped': sum(len(v) for v in PHOTO_MAP.values()) if isinstance(PHOTO_MAP,dict) else 0, 'unmapped_photo_units': [], 'units': COVERAGE, 'capture_hooks': HOOKS}
(OUT / 'ajustes_maquetacion.json').write_text(json.dumps(LAYOUT_EDITS, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUT / 'cobertura_contenido.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUT / 'capturas' / 'LEEME.txt').write_text('Añada archivos <id>.tex con llamadas a \\pantalla{ruta_relativa}{titulo}{leyenda}.\nEl generador incluye estos archivos si existen y nunca los sobrescribe.\nLa relación de id y unidad está en ../cobertura_contenido.json.\nLas rutas de imágenes se interpretan desde manual_latex.\nEjemplo: \\pantalla{../capturas/01_inicio.jpg}{Inicio y preparación}{Observe la fuente seleccionada y los tres prerrequisitos.}\n', encoding='utf-8')

args = argparse.ArgumentParser()
args.add_argument('--compile', action='store_true')
args = args.parse_args()
if args.compile:
    for run in range(2):
        result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'main.tex'], cwd=OUT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (OUT / f'compilacion_{run+1}.txt').write_text(result.stdout, encoding='utf-8')
        if result.returncode:
            print(result.stdout[-8000:])
            raise SystemExit(result.returncode)
    log = (OUT/'main.log').read_text(errors='replace')
    warnings = [x for x in log.splitlines() if 'Overfull' in x or 'Missing character' in x or 'LaTeX Warning:' in x]
    (OUT/'revision_compilacion.json').write_text(json.dumps({'warnings': warnings, 'pdf_sha256': sha(OUT/'main.pdf'), 'tex_sha256': sha(OUT/'main.tex')}, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'main': str(OUT/'main.tex'), 'sections': len(includes), 'covered_units': len(COVERAGE), 'capture_hooks': len(HOOKS), 'dictionary_columns': coverage['dictionary_columns_rendered']}, ensure_ascii=False))
