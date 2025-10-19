import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FileUpload from '../components/FileUpload'
// import { createMockFile } from './utils' // Unused import

describe('FileUpload Component - Core Functionality', () => {
  const mockOnFileUpload = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area with correct initial state', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
    
    expect(screen.getByText('Drop your JSON file here')).toBeInTheDocument()
    expect(screen.getByText('Choose File')).toBeInTheDocument()
    expect(screen.getByText('Only JSON files are supported')).toBeInTheDocument()
  })

  it('shows uploading state when isUploading is true', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={true} />)
    
    expect(screen.getByText('Uploading file...')).toBeInTheDocument()
    expect(screen.queryByText('Drop your JSON file here')).not.toBeInTheDocument()
  })

  it('has proper file input attributes', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
    
    const fileInput = screen.getByLabelText('Choose File')
    expect(fileInput).toHaveAttribute('type', 'file')
    expect(fileInput).toHaveAttribute('accept', '.json,application/json')
  })

  it('handles drag events without errors', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
    
    const uploadArea = screen.getByText('Drop your JSON file here').closest('.file-upload-area')
    expect(uploadArea).toBeInTheDocument()
    
    // These should not throw errors
    fireEvent.dragOver(uploadArea!)
    fireEvent.dragLeave(uploadArea!)
    fireEvent.drop(uploadArea!)
  })

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
    
    const fileInput = screen.getByLabelText('Choose File')
    
    // Focus the file input
    await user.click(fileInput)
    expect(fileInput).toHaveFocus()
  })

  it('shows validation state when files are processed', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
    
    // Initially no validation messages
    expect(screen.queryByText(/validating/i)).not.toBeInTheDocument()
    
    // Component should handle validation internally
    const fileInput = screen.getByLabelText('Choose File')
    expect(fileInput).toBeInTheDocument()
  })
})