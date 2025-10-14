import React, { useState, useEffect } from 'react';
import { ProcessingOptionsProps } from '../types';

export default function ProcessingOptions({ 
  options, 
  onOptionsChange, 
  disabled 
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
            className={`option-item ${disabled ? 'disabled' : ''}`}
          >
            <input
              type="checkbox"
              checked={selectedOptions.includes(option.id)}
              onChange={(e) => handleOptionChange(option.id, e.target.checked)}
              disabled={disabled}
              className="option-checkbox"
            />
            <div className="option-content">
              <span className="option-label">{option.label}</span>
              <span className="option-description">{option.description}</span>
            </div>
          </label>
        ))}
      </div>
      
      {!disabled && !hasSelectedOptions && (
        <div className="validation-message">
          <span className="warning-icon">⚠️</span>
          Please select at least one processing option to continue.
        </div>
      )}
      
      {!disabled && hasSelectedOptions && (
        <div className="selection-summary">
          <span className="success-icon">✅</span>
          {selectedOptions.length} option{selectedOptions.length > 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
}