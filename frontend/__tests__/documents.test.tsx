import { render, screen, waitFor } from '@testing-library/react'
import DocumentsPage from '../pages/documents'
import { beforeEach } from 'node:test'

beforeEach(() => {
  (global.fetch as jest.Mock) = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ 'abc': { filename: 'sample.txt', chunks: 1 } })
    } as Response)
  )
})

test('renders documents page and lists uploaded docs', async () => {
  render(<DocumentsPage />)
  expect(screen.getByText(/Uploaded Documents/i)).toBeInTheDocument()
  await waitFor(() => expect(screen.getByText(/sample.txt/)).toBeInTheDocument())
})
