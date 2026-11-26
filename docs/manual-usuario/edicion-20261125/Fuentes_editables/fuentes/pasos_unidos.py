"""Propuesta de último ajuste, todavía no aplicada a la candidata congelada."""

def _measurement(body, width=r'\linewidth', extra=r'2\baselineskip'):
    return (
        '\\begingroup\n\\setbox0=\\vbox{\\hsize=' + width + '\n\\everypar{}\\csname @newlistfalse\\endcsname\n'
        + body + '\\par\n}\n'
        '\\dimen0=\\dimexpr\\ht0+\\dp0+' + extra + '\\relax\n'
    )

def keep_training_steps(bodies, heading_tex):
    """Agrupa cada paso completo cuando cabe en la altura útil.

    Reserva también el subtítulo y el primer paso antes de comenzar la lista.
    El bloque conserva párrafos normales; samepage no dibuja cajas.
    """
    if not bodies:
        return heading_tex
    result = _measurement(bodies[0], r'\dimexpr\linewidth-1.7em\relax', r'4\baselineskip')
    result += '\\ifdim\\dimen0<\\textheight\\Needspace{\\dimen0}\\fi\n\\endgroup\n'
    result += heading_tex + '\\begin{enumerate}\n'
    for body in bodies:
        result += _measurement(body)
        result += '\\ifdim\\dimen0<\\textheight\n\\Needspace{\\dimen0}\n\\endgroup\n'
        result += '\\item \\begin{samepage}\n' + body + '\\end{samepage}\n'
        result += '\\else\n\\endgroup\n\\item ' + body + '\\fi\n'
    return result + '\\end{enumerate}\n'
