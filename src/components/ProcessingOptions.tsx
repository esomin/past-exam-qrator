import { useState } from 'react';
import type { ProcessingOptionsProps } from '../types';

export default function ProcessingOptions({ 
  options, 
  onOptionsChange, 
  disabled,
  isProcessing = false
}: ProcessingOptionsProps) {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  const handleOptionChange = (optionId: string, checked: boolean) => {
    let newSelectedOptions: string[];
    
    if (checked) {
      newSelectedOptions = [...selectedOptions, optionId];
    } else {
      newSelectedOptions = selectedOptions.filter(id => id !== optionId);
    }
    
    setSelectedOptions(newSelectedOptions);
    onOptionsChange(newSelectedOptions);
  };

  const hasSelectedOptions = selectedOptions.length > 0;

  return (
    <div className="processing-options-container">
      <h3>Processing Options</h3>
      <p className="options-description">
        Select one or more classification types to process your data:
      </p>
      
      <div className="options-list">
        {options.map((option) => (
          <label 
            key={option.id} 
            className={`option-item ${disabled || isProcessing ? 'disabled' : ''}`}
          >
            <input
              type="checkbox"
              checked={selectedOptions.includes(option.id)}
              onChange={(e) => handleOptionChange(option.id, e.target.checked)}
              disabled={disabled || isProcessing}
              className="option-checkbox"
            />
            <div className="option-content">
              <span className="option-label">
                {option.label}
                {isProcessing && selectedOptions.includes(option.id) && (
                  <span className="processing-indicator">
                    <div className="mini-spinner"></div>
                  </span>
                )}
              </span>
              <span className="option-description">{option.description}</span>
            </div>
          </label>
        ))}
      </div>
      
      {!disabled && !isProcessing && !hasSelectedOptions && (
        <div className="validation-message">
          <span className="warning-icon">⚠️</span>
          Please select at least one processing option to continue.
        </div>
      )}
      
      {!disabled && hasSelectedOptions && !isProcessing && (
        <div className="selection-summary">
          <span className="success-icon">✅</span>
          {selectedOptions.length} option{selectedOptions.length > 1 ? 's' : ''} selected
        </div>
      )}

      {isProcessing && hasSelectedOptions && (
        <div className="processing-message">
          <div className="processing-spinner"></div>
          <span>Processing {selectedOptions.length} classification{selectedOptions.length > 1 ? 's' : ''}...</span>
        </div>
      )}
    </div>
  );
}