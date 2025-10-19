import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FileUpload from '../components/FileUpload'
import { createMockFile, createMockDragEvent, createMockChangeEvent, validTestJsonData, invalidTestJsonData } from './utils'

describe('FileUpload Component', () => {
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

  describe('File Validation', () => {
    it('accepts valid JSON files', async () => {
      const validFile = createMockFile('test.json', 'application/json', JSON.stringify(validTestJsonData))
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([validFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(mockOnFileUpload).toHaveBeenCalledWith(validFile)
      })
      
      expect(screen.getByText('test.json')).toBeInTheDocument()
    })

    it('rejects non-JSON files', async () => {
      const invalidFile = createMockFile('test.txt', 'text/plain', 'some text content')
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([invalidFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('Please upload a valid JSON file. Other file types are not supported.')).toBeInTheDocument()
      })
      
      expect(mockOnFileUpload).not.toHaveBeenCalled()
    })

    it('rejects files that are too large', async () => {
      const largeContent = 'x'.repeat(11 * 1024 * 1024) // 11MB
      const largeFile = createMockFile('large.json', 'application/json', largeContent)
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([largeFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('The file is too large. Please upload a file smaller than 10MB.')).toBeInTheDocument()
      })
      
      expect(mockOnFileUpload).not.toHaveBeenCalled()
    })

    it('rejects empty files', async () => {
      const emptyFile = createMockFile('empty.json', 'application/json', '')
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([emptyFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('The uploaded file is empty')).toBeInTheDocument()
      })
      
      expect(mockOnFileUpload).not.toHaveBeenCalled()
    })

    it('rejects files with invalid JSON content', async () => {
      const invalidJsonFile = createMockFile('invalid.json', 'application/json', invalidTestJsonData)
      
      // Mock FileReader to return invalid JSON
      const originalFileReader = window.FileReader
      window.FileReader = class MockFileReader {
        result: string | null = null
        onload: ((event: any) => void) | null = null
        
        readAsText() {
          setTimeout(() => {
            this.result = invalidTestJsonData
            if (this.onload) this.onload({})
          }, 0)
        }
      } as any
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([invalidJsonFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('The file contains invalid JSON format')).toBeInTheDocument()
      })
      
      expect(mockOnFileUpload).not.toHaveBeenCalled()
      
      // Restore original FileReader
      window.FileReader = originalFileReader
    })
  })

  describe('Drag and Drop Functionality', () => {
    it('handles drag over events correctly', () => {
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const uploadArea = screen.getByText('Drop your JSON file here').closest('.file-upload-area')
      expect(uploadArea).toBeInTheDocument()
      
      const dragEvent = createMockDragEvent([])
      fireEvent.dragOver(uploadArea!, dragEvent)
      
      expect(dragEvent.preventDefault).toHaveBeenCalled()
      expect(dragEvent.stopPropagation).toHaveBeenCalled()
    })

    it('handles drag leave events correctly', () => {
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const uploadArea = screen.getByText('Drop your JSON file here').closest('.file-upload-area')
      
      const dragEvent = createMockDragEvent([])
      fireEvent.dragLeave(uploadArea!, dragEvent)
      
      expect(dragEvent.preventDefault).toHaveBeenCalled()
      expect(dragEvent.stopPropagation).toHaveBeenCalled()
    })

    it('handles file drop with valid JSON file', async () => {
      const validFile = createMockFile('dropped.json', 'application/json', JSON.stringify(validTestJsonData))
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const uploadArea = screen.getByText('Drop your JSON file here').closest('.file-upload-area')
      const dropEvent = createMockDragEvent([validFile])
      
      fireEvent.drop(uploadArea!, dropEvent)
      
      await waitFor(() => {
        expect(mockOnFileUpload).toHaveBeenCalledWith(validFile)
      })
    })

    it('handles file drop with invalid file type', async () => {
      const invalidFile = createMockFile('dropped.txt', 'text/plain', 'text content')
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const uploadArea = screen.getByText('Drop your JSON file here').closest('.file-upload-area')
      const dropEvent = createMockDragEvent([invalidFile])
      
      fireEvent.drop(uploadArea!, dropEvent)
      
      await waitFor(() => {
        expect(screen.getByText('Please upload a valid JSON file. Other file types are not supported.')).toBeInTheDocument()
      })
      
      expect(mockOnFileUpload).not.toHaveBeenCalled()
    })
  })

  describe('File Information Display', () => {
    it('displays file information after successful upload', async () => {
      const validFile = createMockFile('test-file.json', 'application/json', JSON.stringify(validTestJsonData))
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([validFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('test-file.json')).toBeInTheDocument()
      })
      
      // Should show file size
      expect(screen.getByText(/KB/)).toBeInTheDocument()
      
      // Should show change file button
      expect(screen.getByText('Change File')).toBeInTheDocument()
    })

    it('allows changing the uploaded file', async () => {
      const firstFile = createMockFile('first.json', 'application/json', JSON.stringify(validTestJsonData))
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([firstFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        expect(screen.getByText('first.json')).toBeInTheDocument()
      })
      
      // Click change file button
      const changeButton = screen.getByText('Change File')
      fireEvent.click(changeButton)
      
      // Should return to initial state
      expect(screen.getByText('Drop your JSON file here')).toBeInTheDocument()
      expect(screen.queryByText('first.json')).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays multiple validation errors', async () => {
      const emptyFile = createMockFile('', 'text/plain', '')
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      const changeEvent = createMockChangeEvent([emptyFile])
      
      fireEvent.change(fileInput, changeEvent)
      
      await waitFor(() => {
        // Should show both file type and empty file errors
        expect(screen.getByText('Please upload a valid JSON file. Other file types are not supported.')).toBeInTheDocument()
        expect(screen.getByText('The uploaded file is empty')).toBeInTheDocument()
      })
    })

    it('clears errors when changing files', async () => {
      const invalidFile = createMockFile('invalid.txt', 'text/plain', 'content')
      const validFile = createMockFile('valid.json', 'application/json', JSON.stringify(validTestJsonData))
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      
      // Upload invalid file first
      fireEvent.change(fileInput, createMockChangeEvent([invalidFile]))
      
      await waitFor(() => {
        expect(screen.getByText('Please upload a valid JSON file. Other file types are not supported.')).toBeInTheDocument()
      })
      
      // Upload valid file
      fireEvent.change(fileInput, createMockChangeEvent([validFile]))
      
      await waitFor(() => {
        expect(screen.queryByText('Please upload a valid JSON file. Other file types are not supported.')).not.toBeInTheDocument()
        expect(screen.getByText('valid.json')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      expect(fileInput).toHaveAttribute('type', 'file')
      expect(fileInput).toHaveAttribute('accept', '.json,application/json')
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      // const validFile = createMockFile('keyboard.json', 'application/json', JSON.stringify(validTestJsonData)) // Unused variable
      
      render(<FileUpload onFileUpload={mockOnFileUpload} isUploading={false} />)
      
      const fileInput = screen.getByLabelText('Choose File')
      
      // Focus the file input
      await user.click(fileInput)
      expect(fileInput).toHaveFocus()
    })
  })
})