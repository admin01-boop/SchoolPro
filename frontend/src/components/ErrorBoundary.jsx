import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Unhandled UI error:', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="loading-state" role="alert">
        <p>Something went wrong.</p>
        <button type="button" onClick={() => window.location.reload()}>Reload</button>
      </div>
    )
  }
}
