import '@testing-library/jest-dom'

// Mock window.URL.createObjectURL
Object.defineProperty(window, 'URL', {
  value: {
    createObjectURL: vi.fn(() => 'mocked-url'),
    revokeObjectURL: vi.fn(),
  },
})

// Mock fetch for API tests
global.fetch = vi.fn()

// Mock file reader
Object.defineProperty(window, 'FileReader', {
  value: class MockFileReader {
    result: string | ArrayBuffer | null = null
    error: any = null
    readyState: number = 0
    
    onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
    onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
    
    readAsText(file: Blob) {
      setTimeout(() => {
        this.readyState = 2
        this.result = '{"test": "data"}'
        if (this.onload) {
          this.onload({} as ProgressEvent<FileReader>)
        }
      }, 0)
    }
    
    readAsDataURL(file: Blob) {
      setTimeout(() => {
        this.readyState = 2
        this.result = 'data:application/json;base64,eyJ0ZXN0IjoiZGF0YSJ9'
        if (this.onload) {
          this.onload({} as ProgressEvent<FileReader>)
        }
      }, 0)
    }
    
    abort() {}
    addEventListener() {}
    removeEventListener() {}
    dispatchEvent() { return true }
  }
})

// Mock drag and drop events
Object.defineProperty(window, 'DataTransfer', {
  value: class MockDataTransfer {
    files: FileList
    
    constructor() {
      this.files = [] as any
    }
  }
})