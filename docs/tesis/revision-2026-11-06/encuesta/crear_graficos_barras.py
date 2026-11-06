"""Gráficos descriptivos de la encuesta real. No modifica frecuencias ni respuestas.

Ejecutar con Python y Matplotlib. El archivo resultados_encuesta.json y esta
fuente permanecen en encuesta/; PNG y SVG se escriben en graficos/.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import datetime as dt

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import to_rgba

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'resultados_encuesta.json'
OUT = ROOT / 'graficos'
OUT.mkdir(exist_ok=True)
DPI = 300
FAMILY = 'Liberation Serif'
BLUE = '#1F4E79'

plt.rcParams.update({
    'font.family': FAMILY,
    'font.size': 15,
    'axes.labelsize': 15,
    'xtick.labelsize': 14,
    'ytick.labelsize': 15,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'axes.grid': False,
    'svg.fonttype': 'none',
    'svg.hashsalt': 'encuesta-bi-20261106-barras',
})
# Exigir la familia solicitada; no sustituirla silenciosamente.
font_path = font_manager.findfont(font_manager.FontProperties(family=FAMILY), fallback_to_default=False)

full_labels = [
    'Totalmente en desacuerdo',
    'En desacuerdo',
    'Ni de acuerdo ni en desacuerdo',
    'De acuerdo',
    'Totalmente de acuerdo',
]
wrapped_labels = [
    'Totalmente en\ndesacuerdo',
    'En desacuerdo',
    'Ni de acuerdo ni\nen desacuerdo',
    'De acuerdo',
    'Totalmente de acuerdo',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_state(doc):
    """Estado de los datos que no se permite cambiar al dibujar."""
    state = copy.deepcopy(doc)
    state.get('metodo', {}).pop('graficos', None)
    for question in state['preguntas']:
        question.pop('grafico_png', None)
        question.pop('grafico_svg', None)
    return state


def main():
    document = json.loads(DATA.read_text(encoding='utf-8'))
    before = numeric_state(document)
    assert document['numero_respuestas_finales'] == 102
    assert len(document['preguntas']) == 10
    assert [x['etiqueta'] for x in document['escala']] == full_labels
    checks = []
    for question in document['preguntas']:
        rows = question['frecuencias']
        assert [x['valor'] for x in rows] == [1, 2, 3, 4, 5]
        assert [x['opcion'] for x in rows] == full_labels
        assert sum(x['frecuencia_absoluta'] for x in rows) == 102
        values = [x['porcentaje'] for x in rows]
        labels = [f"{x['frecuencia_absoluta']} ({x['porcentaje_mostrado']})" for x in rows]
        fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=DPI)
        fig.subplots_adjust(left=0.35, right=0.975, bottom=0.20, top=0.97)
        bars = ax.barh(range(5), values, height=0.58, color=BLUE,
                       edgecolor='none', linewidth=0, hatch=None, zorder=2)
        ax.set_yticks(range(5), labels=wrapped_labels)
        ax.set_ylim(4.6, -0.6)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel('Porcentaje de respuestas', labelpad=8)
        ax.tick_params(axis='y', length=0, pad=10, colors='black')
        ax.tick_params(axis='x', length=3, width=0.7, color='#6B6B6B', labelcolor='black')
        for key in ('left', 'top', 'right'):
            ax.spines[key].set_visible(False)
        ax.spines['bottom'].set_color('#6B6B6B')
        ax.spines['bottom'].set_linewidth(0.7)
        ax.grid(False, axis='both', which='both')
        text_items = []
        for y, value, label in zip(range(5), values, labels):
            text_items.append(ax.text(value + 1.1, y, label, ha='left', va='center',
                                      fontsize=15, color='black', clip_on=False))
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        page_box = fig.bbox
        for artist in [*ax.get_yticklabels(), *ax.get_xticklabels(), ax.xaxis.label, *text_items]:
            bb = artist.get_window_extent(renderer)
            assert bb.x0 >= page_box.x0 - 0.5 and bb.x1 <= page_box.x1 + 0.5, (question['numero'], 'texto fuera horizontalmente', bb)
            assert bb.y0 >= page_box.y0 - 0.5 and bb.y1 <= page_box.y1 + 0.5, (question['numero'], 'texto fuera verticalmente', bb)
        assert not any(line.get_visible() for line in ax.get_xgridlines() + ax.get_ygridlines())
        assert all(bar.get_linewidth() == 0 and bar.get_hatch() is None and bar.get_facecolor() == to_rgba(BLUE) for bar in bars)
        png = OUT / f"pregunta_{question['numero']:02d}.png"
        svg = OUT / f"pregunta_{question['numero']:02d}.svg"
        fig.savefig(png, dpi=DPI)
        fig.savefig(svg, metadata={'Title': question['tema'], 'Description': 'Cinco opciones completas; cantidad y porcentaje de las 102 respuestas. Gráfico de barras sin cuadrícula ni subdivisiones.'})
        question['grafico_png'] = png.relative_to(ROOT).as_posix()
        question['grafico_svg'] = svg.relative_to(ROOT).as_posix()
        checks.append({
            'pregunta': question['numero'],
            'opciones_completas': full_labels,
            'porcentajes': values,
            'rotulos': labels,
            'n_respuestas': 102,
            'barras': 5,
            'limites_porcentaje': [0, 100],
            'color_unico': BLUE,
            'cuadricula_visible': False,
            'bordes_de_barras': False,
            'tramas': False,
            'texto_dentro_del_lienzo': True,
            'archivos': [{'archivo': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in (png, svg)],
        })
        plt.close(fig)
    document['metodo']['graficos'] = 'Diez gráficos de barras horizontales. Cada uno conserva las cinco opciones completas, ordenadas desde Totalmente en desacuerdo hasta Totalmente de acuerdo, y presenta cantidad y porcentaje al extremo de la barra. Todos comparten escala porcentual de 0 a 100. Se utiliza relleno azul uniforme, sin cuadrícula, bordes blancos, tramas o subdivisiones internas. Las opciones con cero respuestas se mantienen con etiqueta 0 (0,00 %).'
    assert numeric_state(document) == before, 'Se intentó modificar datos o información distinta de los gráficos'
    temporary = DATA.with_suffix('.json.graficos.tmp')
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, DATA)
    report = {
        'estado': 'conforme',
        'fecha': dt.datetime.now().astimezone().isoformat(),
        'numero_graficos': 10,
        'formatos': ['PNG', 'SVG'],
        'tamano_pulgadas': [8.5, 3.8],
        'resolucion_png_dpi': DPI,
        'fuente': FAMILY,
        'archivo_fuente_tipografica': Path(font_path).name,
        'fuente_puntos': 15,
        'datos_originales_conservados': True,
        'lectura': 'La etiqueta 64 (62,75 %) significa 64 respuestas, equivalentes al 62,75 % de las 102 respuestas válidas.',
        'separacion_de_categorias': 'Los espacios blancos entre categorías son el fondo del gráfico. No hay líneas de cuadrícula ni rayas que atraviesen las barras.',
        'revision_visual': 'Pendiente de inspección de los PNG por el agente.',
        'graficos': checks,
    }
    (ROOT / 'verificacion_graficos.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Generados 10 gráficos PNG y 10 SVG; datos de la encuesta conservados; comprobaciones geométricas correctas.')


if __name__ == '__main__':
    main()
