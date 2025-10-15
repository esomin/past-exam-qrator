import { ProcessingOption, ProcessingResult } from '../types'

// Test data factories
export const createMockFile = (
  name: string = 'test.json',
  type: string = 'application/json',
  content: string = '{"test": "data"}'
): File => {
  const blob = new Blob([content], { type })
  return new File([blob], name, { type })
}

export const createMockProcessingOptions = (): ProcessingOption[] => [
  {
    id: 'category',
    label: 'Category Classification',
    description: 'Group by question categories with similarity detection'
  },
  {
    id: 'institution',
    label: 'Institution Classification', 
    description: 'Group by institution extracted from solve field'
  },
  {
    id: 'year',
    label: 'Year Classification',
    description: 'Group by year extracted from solve field'
  }
]

export const createMockProcessingResults = (): ProcessingResult[] => [
  {
    id: 'result-1',
    type: 'category',
    filename: 'category_classification.json',
    data: {
      '지방행정': {
        '지방자치권': [
          { id: 1, question: 'Test question 1', answer: 'Test answer 1' }
        ]
      }
    }
  },
  {
    id: 'result-2', 
    type: 'institution',
    filename: 'institution_classification.json',
    data: {
      '지방직 7급': [
        { id: 1, question: 'Test question 1', answer: 'Test answer 1' }
      ]
    }
  }
]

export const createMockDragEvent = (files: File[]): DragEvent => {
  const mockDataTransfer = {
    files: files as any as FileList,
    items: files.map(file => ({ kind: 'file', type: file.type, getAsFile: () => file })) as any,
    types: ['Files']
  }
  
  return {
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
    dataTransfer: mockDataTransfer
  } as any as DragEvent
}

export const createMockChangeEvent = (files: File[]): React.ChangeEvent<HTMLInputElement> => {
  return {
    target: {
      files: files as any as FileList
    }
  } as React.ChangeEvent<HTMLInputElement>
}

// Mock API responses
export const mockApiResponse = {
  success: {
    success: true,
    results: [
      {
        type: 'category',
        filename: 'category_classification.json',
        download_id: 'download-123'
      }
    ],
    processed_items: 10,
    original_questions: 5
  },
  error: {
    success: false,
    error: {
      code: 'PROCESSING_ERROR',
      message: 'Processing failed',
      details: 'Invalid file format'
    }
  }
}

// Test JSON data
export const validTestJsonData = [
  {
    id: 51596,
    title: 'Test question 1',
    solve: '지방직 7급 / 2022',
    categoryTitle: '1) Test Category',
    answerSet: [
      {
        id: 189210,
        title: 'Test answer 1',
        answerKind: 'O'
      }
    ]
  }
]

export const invalidTestJsonData = 'invalid json content'

// Helper to wait for async operations
export const waitFor = (ms: number = 0) => new Promise(resolve => setTimeout(resolve, ms))