import { useState } from 'react';
import { FiAlertTriangle, FiCheckCircle, FiLoader } from 'react-icons/fi';
import type { ProcessingOptionsProps } from '../types';

export default function ProcessingOptions({ 
  options, 
  onOptionsChange, 
  disabled,
  isProcessing = false
}: ProcessingOptionsProps) {
  const [selectedClassifications, setSelectedClassifications] = useState<string[]>([]);
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['json']); // Default to JSON

  const handleClassificationChange = (optionId: string, checked: boolean) => {
    let newSelectedClassifications: string[];
    
    if (checked) {
      newSelectedClassifications = [...selectedClassifications, optionId];
    } else {
      newSelectedClassifications = selectedClassifications.filter(id => id !== optionId);
    }
    
    setSelectedClassifications(newSelectedClassifications);
    updateOptions(newSelectedClassifications, selectedFormats);
  };

  const handleFormatChange = (formatId: string, checked: boolean) => {
    let newSelectedFormats: string[];
    
    if (checked) {
      newSelectedFormats = [...selectedFormats, formatId];
    } else {
      newSelectedFormats = selectedFormats.filter(id => id !== formatId);
    }
    
    // Ensure at least one format is selected
    if (newSelectedFormats.length === 0) {
      newSelectedFormats = ['json'];
    }
    
    setSelectedFormats(newSelectedFormats);
    updateOptions(selectedClassifications, newSelectedFormats);
  };

  const updateOptions = (classifications: string[], formats: string[]) => {
    // Combine classifications and formats
    const allOptions = [...classifications, ...formats];
    onOptionsChange(allOptions);
  };

  const hasSelectedClassifications = selectedClassifications.length > 0;
  const hasSelectedFormats = selectedFormats.length > 0;

  return (
    <div className="processing-options-container">
      <h3>Processing Options</h3>
      <p className="options-description">
        Select classification types and output formats for your data:
      </p>
      
      {/* Classification Options */}
      <div className="options-section">
        <h4 className="section-title">분류 옵션 (Classification Options)</h4>
        <div className="options-list">
          {options.map((option) => (
            <label 
              key={option.id} 
              className={`option-item ${disabled || isProcessing || option.disabled ? 'disabled' : ''}`}
            >
              <input
                type="checkbox"
                checked={selectedClassifications.includes(option.id)}
                onChange={(e) => handleClassificationChange(option.id, e.target.checked)}
                disabled={disabled || isProcessing || option.disabled}
                className="option-checkbox"
              />
              <div className="option-content">
                <span className="option-label">
                  {option.label}
                  {option.disabled && (
                    <span className="disabled-indicator" title="This option is temporarily disabled">
                      (Disabled)
                    </span>
                  )}
                  {isProcessing && selectedClassifications.includes(option.id) && (
                    <span className="processing-indicator">
                      <FiLoader className="mini-spinner" />
                    </span>
                  )}
                </span>
                <span className="option-description">
                  {option.description}
                  {option.disabled && (
                    <span className="disabled-note"> - Currently unavailable</span>
                  )}
                </span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Output Format Options */}
      <div className="options-section">
        <h4 className="section-title">출력 형식 (Output Format)</h4>
        <div className="options-list">
          <label className={`option-item ${disabled || isProcessing ? 'disabled' : ''}`}>
            <input
              type="checkbox"
              checked={selectedFormats.includes('json')}
              onChange={(e) => handleFormatChange('json', e.target.checked)}
              disabled={disabled || isProcessing}
              className="option-checkbox"
            />
            <div className="option-content">
              <span className="option-label">JSON</span>
              <span className="option-description">Standard JSON format for data processing</span>
            </div>
          </label>
          
          <label className={`option-item ${disabled || isProcessing ? 'disabled' : ''}`}>
            <input
              type="checkbox"
              checked={selectedFormats.includes('markdown')}
              onChange={(e) => handleFormatChange('markdown', e.target.checked)}
              disabled={disabled || isProcessing}
              className="option-checkbox"
            />
            <div className="option-content">
              <span className="option-label">Markdown</span>
              <span className="option-description">Table format for easy viewing and documentation</span>
            </div>
          </label>
        </div>
      </div>
      
      {!disabled && !isProcessing && !hasSelectedClassifications && (
        <div className="validation-message">
          <FiAlertTriangle className="warning-icon" />
          Please select at least one classification option to continue.
        </div>
      )}
      
      {!disabled && hasSelectedClassifications && hasSelectedFormats && !isProcessing && (
        <div className="selection-summary">
          <FiCheckCircle className="success-icon" />
          {selectedClassifications.length} classification{selectedClassifications.length > 1 ? 's' : ''} and {selectedFormats.length} format{selectedFormats.length > 1 ? 's' : ''} selected
        </div>
      )}

      {isProcessing && hasSelectedClassifications && (
        <div className="processing-message">
          <FiLoader className="processing-spinner" />
          <span>Processing {selectedClassifications.length} classification{selectedClassifications.length > 1 ? 's' : ''} in {selectedFormats.length} format{selectedFormats.length > 1 ? 's' : ''}...</span>
        </div>
      )}
    </div>
  );
}