# Q&A Data Processor

TypeScript + Python을 사용한 Q&A 데이터 처리 도구

## 프로젝트 구조
```
project/
├── src/                    # TypeScript 소스 코드
│   ├── types/             # 타입 정의
│   ├── processors/        # 데이터 처리 모듈
│   ├── utils/            # 유틸리티 함수
│   └── app.ts            # 메인 애플리케이션
├── python/               # Python 스크래핑 코드
│   ├── requirements.txt
│   └── *.ipynb
├── data/                 # 입출력 데이터
├── scripts/              # 실행 스크립트
└── dist/                 # 컴파일된 JavaScript
```

## 환경 설정

### Node.js + TypeScript 환경
```bash
nvm use 22
npm install
```

### Python 환경 (스크래핑용)
```bash
cd python
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

## 사용법

### 전체 파이프라인 실행
```bash
./scripts/run.sh
```

### 개발 모드 (watch)
```bash
npm run dev
```

### 개별 실행
```bash
# TypeScript 빌드
npm run build

# 전체 파이프라인
npm start

# 타입 체크만
npm run type-check
```

## 주요 기능
- **타입 안전성**: TypeScript로 데이터 구조 보장
- **모듈화**: 기능별 분리된 프로세서
- **HTML 정리**: 태그 제거 및 텍스트 정리
- **자동화**: 스크립트를 통한 일괄 처리

## 출력 파일
- `data/questions.json`: 추출된 질문 목록
- `data/answers.json`: 추출된 답변 목록  
- `data/qna-pairs.json`: Q&A 쌍 데이터