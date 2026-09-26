import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { failed: boolean }

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(error: Error, information: ErrorInfo) {
    console.error('La interfaz no pudo completar el renderizado.', error, information)
  }

  render() {
    if (!this.state.failed) return this.props.children
    return <main className="application-recovery" role="alert">
      <span aria-hidden="true">!</span>
      <p className="eyebrow">Recuperación de la interfaz</p>
      <h1>El expediente sigue seguro</h1>
      <p>La pantalla encontró un problema inesperado, pero no repitió el ETL ni modificó los datos publicados.</p>
      <button type="button" onClick={() => window.location.reload()}>Recargar la aplicación</button>
    </main>
  }
}
