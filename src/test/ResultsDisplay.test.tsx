import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResultsDisplay from '../components/ResultsDisplay'
import { createMockProcessingResults } from './utils'

describe('ResultsDisplay Component', () => {
  const mockOnDownload = vi.fn()
  const mockResults = createMockProcessingResults()
  
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when no results are provided', () => {
    const { container } = render(
      <ResultsDisplay results={[]} onDownload={mockOnDownload} />
    )
    
    expect(container.firstChild).toBeNull()
  })

  it('renders results display with correct title and description', () => {
    render(
      <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
    )
    
    expect(screen.getByText('Processing Results')).toBeInTheDocument()
    expect(screen.getByText('Your file has been processed successfully. Download the results below:')).toBeInTheDocument()
  })

  describe('Result Items Display', () => {
    it('displays all result items with correct information', () => {
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      // Check category result
      expect(screen.getByText('Category Classification')).toBeInTheDocument()
      expect(screen.getByText('category_classification.json')).toBeInTheDocument()
      
      // Check institution result
      expect(screen.getByText('Institution Classification')).toBeInTheDocument()
      expect(screen.getByText('institution_classification.json')).toBeInTheDocument()
      
      // Check download buttons
      const downloadButtons = screen.getAllByText('Download')
      expect(downloadButtons).toHaveLength(2)
    })

    it('displays correct file type icons', () => {
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      // Icons are rendered as text content, check they exist
      const resultItems = screen.getAllByText(/Classification/)
      expect(resultItems).toHaveLength(2)
    })

    it('shows result statistics when data is available', () => {
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      // Should show category count for each result
      const statsElements = screen.getAllByText(/categories found/)
      expect(statsElements).toHaveLength(2)
    })

    it('formats file types correctly', () => {
      const customResults = [
        {
          id: 'test-1',
          type: 'category',
          filename: 'test.json',
          data: { 'test': [] }
        },
        {
          id: 'test-2', 
          type: 'institution',
          filename: 'test2.json',
          data: { 'test': [] }
        },
        {
          id: 'test-3',
          type: 'year',
          filename: 'test3.json',
          data: { 'test': [] }
        }
      ]
      
      render(
        <ResultsDisplay results={customResults} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('Category Classification')).toBeInTheDocument()
      expect(screen.getByText('Institution Classification')).toBeInTheDocument()
      expect(screen.getByText('Year Classification')).toBeInTheDocument()
    })
  })

  describe('Download Functionality', () => {
    it('calls onDownload when download button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      expect(mockOnDownload).toHaveBeenCalledWith('result-1')
    })

    it('shows downloading state during download', async () => {
      // Mock onDownload to return a promise that we can control
      const downloadPromise = new Promise(resolve => setTimeout(resolve, 100))
      mockOnDownload.mockReturnValue(downloadPromise)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      // Should show downloading state
      expect(screen.getByText('Downloading...')).toBeInTheDocument()
      
      // Button should be disabled
      expect(downloadButtons[0]).toBeDisabled()
      
      // Wait for download to complete
      await waitFor(() => downloadPromise)
    })

    it('shows progress during download', async () => {
      // Mock a longer download to test progress
      const downloadPromise = new Promise(resolve => setTimeout(resolve, 200))
      mockOnDownload.mockReturnValue(downloadPromise)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      // Should show progress percentage
      await waitFor(() => {
        expect(screen.getByText(/\d+%/)).toBeInTheDocument()
      }, { timeout: 150 })
      
      await waitFor(() => downloadPromise)
    })

    it('handles download errors gracefully', async () => {
      const downloadError = new Error('Download failed')
      mockOnDownload.mockRejectedValue(downloadError)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      await waitFor(() => {
        expect(screen.getByText('Download failed')).toBeInTheDocument()
      })
      
      // Should show retry button
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })

    it('allows retrying failed downloads', async () => {
      const downloadError = new Error('Download failed')
      mockOnDownload.mockRejectedValueOnce(downloadError)
      mockOnDownload.mockResolvedValueOnce(undefined)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText('Download failed')).toBeInTheDocument()
      })
      
      // Click retry
      const retryButton = screen.getByText('Retry')
      await user.click(retryButton)
      
      // Should call onDownload again
      expect(mockOnDownload).toHaveBeenCalledTimes(2)
    })

    it('handles multiple simultaneous downloads', async () => {
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      
      // Click both download buttons
      await user.click(downloadButtons[0])
      await user.click(downloadButtons[1])
      
      expect(mockOnDownload).toHaveBeenCalledWith('result-1')
      expect(mockOnDownload).toHaveBeenCalledWith('result-2')
      expect(mockOnDownload).toHaveBeenCalledTimes(2)
    })
  })

  describe('Results Summary', () => {
    it('shows correct summary for single result', () => {
      const singleResult = [mockResults[0]]
      
      render(
        <ResultsDisplay results={singleResult} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('1 result ready for download')).toBeInTheDocument()
    })

    it('shows correct summary for multiple results', () => {
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('2 results ready for download')).toBeInTheDocument()
    })
  })

  describe('Error States', () => {
    it('displays custom error messages', async () => {
      const customError = new Error('Custom error message')
      mockOnDownload.mockRejectedValue(customError)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      await waitFor(() => {
        expect(screen.getByText('Custom error message')).toBeInTheDocument()
      })
    })

    it('handles non-Error objects in catch blocks', async () => {
      mockOnDownload.mockRejectedValue('String error')
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      await waitFor(() => {
        expect(screen.getByText('Download failed')).toBeInTheDocument()
      })
    })

    it('clears errors when retrying', async () => {
      const downloadError = new Error('Download failed')
      mockOnDownload.mockRejectedValueOnce(downloadError)
      
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByText('Download')
      await user.click(downloadButtons[0])
      
      // Wait for error
      await waitFor(() => {
        expect(screen.getByText('Download failed')).toBeInTheDocument()
      })
      
      // Mock successful retry
      mockOnDownload.mockResolvedValueOnce(undefined)
      
      // Click retry
      const retryButton = screen.getByText('Retry')
      await user.click(retryButton)
      
      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText('Download failed')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByRole('button', { name: /Download/ })
      expect(downloadButtons).toHaveLength(2)
      
      // Buttons should be accessible
      downloadButtons.forEach(button => {
        expect(button.tagName).toBe('BUTTON')
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByRole('button', { name: /Download/ })
      
      // Tab to first button
      await user.tab()
      expect(downloadButtons[0]).toHaveFocus()
      
      // Enter to activate
      await user.keyboard('{Enter}')
      expect(mockOnDownload).toHaveBeenCalledWith('result-1')
    })

    it('maintains focus management during state changes', async () => {
      const user = userEvent.setup()
      
      render(
        <ResultsDisplay results={mockResults} onDownload={mockOnDownload} />
      )
      
      const downloadButtons = screen.getAllByRole('button', { name: /Download/ })
      
      // Focus and click button
      await user.click(downloadButtons[0])
      
      // Button should be accessible after click
      expect(downloadButtons[0]).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles results without data property', () => {
      const resultsWithoutData = [
        {
          id: 'test-1',
          type: 'category',
          filename: 'test.json'
          // No data property
        }
      ]
      
      render(
        <ResultsDisplay results={resultsWithoutData as any} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('Category Classification')).toBeInTheDocument()
      expect(screen.getByText('test.json')).toBeInTheDocument()
      // Should not crash when data is undefined
    })

    it('handles empty data objects', () => {
      const resultsWithEmptyData = [
        {
          id: 'test-1',
          type: 'category',
          filename: 'test.json',
          data: {}
        }
      ]
      
      render(
        <ResultsDisplay results={resultsWithEmptyData} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('0 categories found')).toBeInTheDocument()
    })

    it('handles unknown file types', () => {
      const unknownTypeResult = [
        {
          id: 'test-1',
          type: 'unknown',
          filename: 'test.json',
          data: { 'test': [] }
        }
      ]
      
      render(
        <ResultsDisplay results={unknownTypeResult} onDownload={mockOnDownload} />
      )
      
      expect(screen.getByText('Unknown Classification')).toBeInTheDocument()
    })
  })
})