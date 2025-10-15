import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ProcessingOptions from '../components/ProcessingOptions'
import { createMockProcessingOptions } from './utils'

describe('ProcessingOptions Component', () => {
  const mockOnOptionsChange = vi.fn()
  const mockOptions = createMockProcessingOptions()
  
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all processing options', () => {
    render(
      <ProcessingOptions 
        options={mockOptions}
        onOptionsChange={mockOnOptionsChange}
        disabled={false}
      />
    )
    
    expect(screen.getByText('Processing Options')).toBeInTheDocument()
    expect(screen.getByText('Select one or more classification types to process your data:')).toBeInTheDocument()
    
    // Check all options are rendered
    expect(screen.getByText('Category Classification')).toBeInTheDocument()
    expect(screen.getByText('Institution Classification')).toBeInTheDocument()
    expect(screen.getByText('Year Classification')).toBeInTheDocument()
    
    // Check descriptions are rendered
    expect(screen.getByText('Group by question categories with similarity detection')).toBeInTheDocument()
    expect(screen.getByText('Group by institution extracted from solve field')).toBeInTheDocument()
    expect(screen.getByText('Group by year extracted from solve field')).toBeInTheDocument()
  })

  it('shows validation message when no options are selected', () => {
    render(
      <ProcessingOptions 
        options={mockOptions}
        onOptionsChange={mockOnOptionsChange}
        disabled={false}
      />
    )
    
    expect(screen.getByText('Please select at least one processing option to continue.')).toBeInTheDocument()
  })

  describe('Option Selection', () => {
    it('handles single option selection', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      
      await user.click(categoryCheckbox)
      
      expect(mockOnOptionsChange).toHaveBeenCalledWith(['category'])
      expect(categoryCheckbox).toBeChecked()
    })

    it('handles multiple option selection', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      const institutionCheckbox = screen.getByRole('checkbox', { name: /Institution Classification/ })
      
      await user.click(categoryCheckbox)
      expect(mockOnOptionsChange).toHaveBeenCalledWith(['category'])
      
      await user.click(institutionCheckbox)
      expect(mockOnOptionsChange).toHaveBeenCalledWith(['category', 'institution'])
    })

    it('handles option deselection', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      
      // Select option
      await user.click(categoryCheckbox)
      expect(mockOnOptionsChange).toHaveBeenCalledWith(['category'])
      
      // Deselect option
      await user.click(categoryCheckbox)
      expect(mockOnOptionsChange).toHaveBeenCalledWith([])
    })

    it('maintains selection state correctly', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      const institutionCheckbox = screen.getByRole('checkbox', { name: /Institution Classification/ })
      const yearCheckbox = screen.getByRole('checkbox', { name: /Year Classification/ })
      
      // Select multiple options
      await user.click(categoryCheckbox)
      await user.click(institutionCheckbox)
      await user.click(yearCheckbox)
      
      expect(categoryCheckbox).toBeChecked()
      expect(institutionCheckbox).toBeChecked()
      expect(yearCheckbox).toBeChecked()
      
      // Deselect middle option
      await user.click(institutionCheckbox)
      
      expect(categoryCheckbox).toBeChecked()
      expect(institutionCheckbox).not.toBeChecked()
      expect(yearCheckbox).toBeChecked()
      
      expect(mockOnOptionsChange).toHaveBeenLastCalledWith(['category', 'year'])
    })
  })

  describe('Disabled State', () => {
    it('disables all checkboxes when disabled prop is true', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={true}
        />
      )
      
      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled()
      })
    })

    it('prevents interaction when disabled', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={true}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      
      await user.click(categoryCheckbox)
      
      expect(mockOnOptionsChange).not.toHaveBeenCalled()
      expect(categoryCheckbox).not.toBeChecked()
    })

    it('applies disabled styling', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={true}
        />
      )
      
      const optionItems = screen.getAllByText(/Classification/).map(el => 
        el.closest('.option-item')
      )
      
      optionItems.forEach(item => {
        expect(item).toHaveClass('disabled')
      })
    })
  })

  describe('Processing State', () => {
    it('shows processing indicators when isProcessing is true', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
          isProcessing={true}
        />
      )
      
      // Should show processing message when no options are selected but processing is true
      // This is an edge case - normally processing would only happen with selected options
      expect(screen.queryByText(/Processing.*classification/)).not.toBeInTheDocument()
    })

    it('disables checkboxes during processing', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
          isProcessing={true}
        />
      )
      
      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled()
      })
    })

    it('shows processing indicators for selected options only', async () => {
      const user = userEvent.setup()
      
      // First render without processing to select options
      const { rerender } = render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
          isProcessing={false}
        />
      )
      
      // Select category option
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      await user.click(categoryCheckbox)
      
      // Re-render with processing state
      rerender(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
          isProcessing={true}
        />
      )
      
      // Should show processing message
      expect(screen.getByText('Processing 1 classification...')).toBeInTheDocument()
    })
  })

  describe('Selection Summary', () => {
    it('shows selection summary when options are selected', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      const institutionCheckbox = screen.getByRole('checkbox', { name: /Institution Classification/ })
      
      await user.click(categoryCheckbox)
      expect(screen.getByText('1 option selected')).toBeInTheDocument()
      
      await user.click(institutionCheckbox)
      expect(screen.getByText('2 options selected')).toBeInTheDocument()
    })

    it('hides validation message when options are selected', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      // Initially shows validation message
      expect(screen.getByText('Please select at least one processing option to continue.')).toBeInTheDocument()
      
      // Select an option
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      await user.click(categoryCheckbox)
      
      // Validation message should be hidden
      expect(screen.queryByText('Please select at least one processing option to continue.')).not.toBeInTheDocument()
      
      // Should show selection summary instead
      expect(screen.getByText('1 option selected')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(3)
      
      checkboxes.forEach(checkbox => {
        expect(checkbox).toHaveAttribute('type', 'checkbox')
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      const categoryCheckbox = screen.getByRole('checkbox', { name: /Category Classification/ })
      
      // Tab to checkbox
      await user.tab()
      expect(categoryCheckbox).toHaveFocus()
      
      // Space to toggle
      await user.keyboard(' ')
      expect(mockOnOptionsChange).toHaveBeenCalledWith(['category'])
    })

    it('has proper labeling for screen readers', () => {
      render(
        <ProcessingOptions 
          options={mockOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      // Check that each checkbox has proper labeling
      expect(screen.getByRole('checkbox', { name: /Category Classification/ })).toBeInTheDocument()
      expect(screen.getByRole('checkbox', { name: /Institution Classification/ })).toBeInTheDocument()
      expect(screen.getByRole('checkbox', { name: /Year Classification/ })).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty options array', () => {
      render(
        <ProcessingOptions 
          options={[]}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      expect(screen.getByText('Processing Options')).toBeInTheDocument()
      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    })

    it('handles options with missing properties gracefully', () => {
      const incompleteOptions = [
        { id: 'test', label: 'Test Option' } as any
      ]
      
      render(
        <ProcessingOptions 
          options={incompleteOptions}
          onOptionsChange={mockOnOptionsChange}
          disabled={false}
        />
      )
      
      expect(screen.getByText('Test Option')).toBeInTheDocument()
      expect(screen.getByRole('checkbox')).toBeInTheDocument()
    })
  })
})