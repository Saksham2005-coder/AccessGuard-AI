import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders product heading and toolchain confirmation', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /AccessGuard AI/i })).toBeInTheDocument()
    expect(screen.getByText(/Toolchain Initialized/i)).toBeInTheDocument()
  })
})
