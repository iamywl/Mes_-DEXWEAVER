cd /root/MES_PROJECT
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code \
  --from-file=app.py=./app.py \
  --from-file=database.py=./api_modules/database.py \
  --from-file=mes_logic.py=./api_modules/mes_logic.py \
  --from-file=sys_logic.py=./api_modules/sys_logic.py

kubectl delete deployment mes-api --ignore-not-found
cat <<'K8S' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mes-api
  template:
    metadata:
      labels:
        app: mes-api
    spec:
      containers:
      - name: mes-api
        image: python:3.9-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          mkdir -p /app/api_modules
          cp /mnt/*.py /app/api_modules/
          mv /app/api_modules/app.py /app/app.py
          touch /app/api_modules/__init__.py
          pip install fastapi uvicorn psycopg2-binary kubernetes
          python /app/app.py
        volumeMounts:
        - name: code-volume
          mountPath: /mnt
      volumes:
      - name: code-volume
        configMap:
          name: api-code
K8S
./startup-fix.sh
