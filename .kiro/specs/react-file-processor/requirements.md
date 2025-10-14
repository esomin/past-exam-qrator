# Requirements Document

## Introduction

This feature involves creating a Vite React application that allows users to upload JSON files via drag-and-drop, process them using an enhanced Python backend with multiple classification options, and download the processed results. The Python backend will be enhanced to parse "solve" fields and provide multiple classification options including category-based, institution-based, and year-based grouping.

## Requirements

### Requirement 1

**User Story:** As a user, I want to upload a JSON file through a drag-and-drop interface, so that I can process my data without manually navigating file systems.

#### Acceptance Criteria

1. WHEN a user drags a JSON file over the upload area THEN the system SHALL highlight the drop zone
2. WHEN a user drops a JSON file THEN the system SHALL validate the file type and display the filename
3. WHEN a user drops a non-JSON file THEN the system SHALL display an error message
4. WHEN a file is successfully uploaded THEN the system SHALL enable the processing options

### Requirement 2

**User Story:** As a user, I want to select multiple processing options via checkboxes, so that I can get different classifications of my data simultaneously.

#### Acceptance Criteria

1. WHEN a file is uploaded THEN the system SHALL display three checkbox options: Category, Institution, and Year
2. WHEN no checkboxes are selected THEN the system SHALL disable the process button
3. WHEN at least one checkbox is selected THEN the system SHALL enable the process button
4. WHEN multiple checkboxes are selected THEN the system SHALL process all selected classifications

### Requirement 3

**User Story:** As a user, I want the Python backend to parse "solve" fields and extract institution and year information, so that I can classify data by these attributes.

#### Acceptance Criteria

1. WHEN the backend processes data with "solve" fields THEN the system SHALL split the solve string by "/" delimiter
2. WHEN a solve field contains "지방직 7급 / 2022" THEN the system SHALL extract "지방직 7급" as institution and "2022" as year
3. WHEN a solve field contains "서울시 7급 / 2021" THEN the system SHALL extract "서울시 7급" as institution and "2021" as year
4. WHEN a solve field is missing or malformed THEN the system SHALL handle gracefully with default values
5. WHEN processing institution classification THEN the system SHALL group data by extracted institution values
6. WHEN processing year classification THEN the system SHALL group data by extracted year values

### Requirement 4

**User Story:** As a user, I want to download the processed results as JSON files, so that I can use the classified data in other applications.

#### Acceptance Criteria

1. WHEN processing is complete THEN the system SHALL display download buttons for each selected classification
2. WHEN a user clicks a download button THEN the system SHALL trigger a file download with appropriate filename
3. WHEN category classification is selected THEN the system SHALL generate a file named "category_classification.json"
4. WHEN institution classification is selected THEN the system SHALL generate a file named "institution_classification.json"
5. WHEN year classification is selected THEN the system SHALL generate a file named "year_classification.json"

### Requirement 5

**User Story:** As a developer, I want the React app to communicate with the Python backend via API endpoints, so that file processing is handled server-side.

#### Acceptance Criteria

1. WHEN a user uploads a file THEN the system SHALL send the file data to the Python backend via POST request
2. WHEN processing options are selected THEN the system SHALL include the selected options in the API request
3. WHEN the backend completes processing THEN the system SHALL return the processed data in JSON format
4. WHEN an error occurs during processing THEN the system SHALL return appropriate error messages
5. WHEN the API response is received THEN the system SHALL update the UI with results or error messages

### Requirement 6

**User Story:** As a user, I want a responsive and intuitive user interface, so that I can easily navigate and use the application.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL display a clean, modern interface with clear instructions
2. WHEN processing is in progress THEN the system SHALL show a loading indicator
3. WHEN processing is complete THEN the system SHALL display success messages and download options
4. WHEN errors occur THEN the system SHALL display user-friendly error messages
5. WHEN the interface is viewed on different screen sizes THEN the system SHALL maintain usability and readability