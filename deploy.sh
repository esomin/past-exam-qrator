#!/bin/bash

# Google Cloud Compute Engine 배포 스크립트
# Ubuntu 22.04 LTS 및 Debian 12(Bookworm) 환경에서 실행 가능

set -e

echo "🚀 Qrator 애플리케이션 배포 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 업데이트
log_info "시스템 패키지 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# Docker 설치
if ! command -v docker &> /dev/null; then
    log_info "Docker 설치 중..."
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

    # OS 감지 (Ubuntu / Debian)
    if grep -qi debian /etc/os-release; then
        DISTRO="debian"
    else
        DISTRO="ubuntu"
    fi

    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${DISTRO}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/${DISTRO} $(lsb_release -cs) stable" \
      | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    sudo usermod -aG docker $USER
    log_info "Docker 설치 완료"
else
    log_info "Docker가 이미 설치되어 있습니다"
fi

# Docker Compose 설치 (별도 바이너리 버전)
if ! command -v docker-compose &> /dev/null; then
    log_info "Docker Compose 설치 중..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose 설치 완료"
else
    log_info "Docker Compose가 이미 설치되어 있습니다"
fi

# 필요한 디렉토리 생성
log_info "필요한 디렉토리 생성 중..."
mkdir -p data temp ssl

# 방화벽 설정
log_info "방화벽 규칙 설정 중..."
if ! command -v ufw &> /dev/null; then
    log_warn "ufw가 설치되어 있지 않습니다. 설치 중..."
    sudo apt-get install -y ufw
fi

sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5001/tcp  # Flask 개발 포트
sudo ufw --force enable

# SSL 인증서 생성 (자체 서명, 프로덕션에서는 Let's Encrypt 권장)
if [ ! -f ssl/cert.pem ]; then
    log_info "자체 서명 SSL 인증서 생성 중..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=KR/ST=Seoul/L=Seoul/O=Qrator/CN=localhost"
    log_warn "프로덕션 환경에서는 Let's Encrypt 인증서 사용을 권장합니다"
fi

# Docker 이미지 빌드
log_info "Docker 이미지 빌드 중..."
docker-compose build

# 기존 컨테이너 중지 및 제거
log_info "기존 컨테이너 정리 중..."
docker-compose down --remove-orphans

# 애플리케이션 시작
log_info "애플리케이션 시작 중..."
docker-compose up -d

# 헬스 체크
log_info "애플리케이션 상태 확인 중..."
sleep 30

if curl -f http://localhost:5001/api/health > /dev/null 2>&1; then
    log_info "✅ 애플리케이션이 성공적으로 시작되었습니다!"
    echo ""
    echo "🌐 접속 정보:"
    echo "   - HTTP: http://$(curl -s ifconfig.me):80"
    echo "   - HTTPS: https://$(curl -s ifconfig.me):443"
    echo "   - 직접 접속: http://$(curl -s ifconfig.me):5001"
    echo ""
    echo "📊 상태 확인:"
    echo "   - 헬스 체크: curl http://localhost:5001/api/health"
    echo "   - 로그 확인: docker-compose logs -f"
    echo "   - 컨테이너 상태: docker-compose ps"
else
    log_error "❌ 애플리케이션 시작에 실패했습니다"
    echo "로그를 확인하세요: docker-compose logs"
    exit 1
fi

# 시스템 정보 출력
echo ""
echo "💻 시스템 정보:"
echo "   - OS: $(lsb_release -d | cut -f2)"
echo "   - Docker: $(docker --version)"
echo "   - Docker Compose: $(docker-compose --version)"
echo "   - 메모리: $(free -h | grep Mem | awk '{print $2}')"
echo "   - 디스크: $(df -h / | tail -1 | awk '{print $4}') 사용 가능"

log_info "배포 완료! 🎉"
