#!/bin/bash
# =========================================================
# KNU MES: Image Build Script (CI Stage)
# =========================================================
PROJECT_DIR="$HOME/MES_PROJECT"
cd $PROJECT_DIR

# 1. 이미지 태그 생성 (시간 기반)
IMAGE_TAG="v$(date +%Y%m%d%H%M)"
IMAGE_NAME="mes-api:$IMAGE_TAG"

echo "🐳 [BUILD] 도커 이미지 빌드 시작: $IMAGE_NAME"

# 2. Dockerfile 자동 생성 (이미지가 없다면 생성)
cat <<DOCKER_EOF > $PROJECT_DIR/Dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary kubernetes pydantic
COPY api_modules/ /app/api_modules/
COPY app.py /app/
ENV PYTHONPATH=/app
CMD ["python", "app.py"]
DOCKER_EOF

# 3. 도커 빌드 실행
docker build -t $IMAGE_NAME .

# 4. 배포 스크립트가 참조할 수 있도록 최신 이미지 명칭 저장
echo "$IMAGE_NAME" > $PROJECT_DIR/.last_image_tag

echo "--------------------------------------------------------"
echo "✅ 빌드 완료: $IMAGE_NAME"
echo "--------------------------------------------------------"
