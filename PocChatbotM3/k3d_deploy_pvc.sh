#!/usr/bin/env bash
set -euo pipefail

########################################
#        PARAMÈTRES À ADAPTER          #
########################################
NS="chatbot"
IMAGE_ACR="acrchatbotm3.azurecr.io/chatbot-poc:v1"
APP_PORT=8501
HOST_HTTP_PORT=8080
CLUSTER_NAME="chatbot"

# Tailles des volumes
DB_SIZE="5Gi"
VECTOR_SIZE="10Gi"

# [OPTIONNEL] Persistance sur l'hôte (true/false)
# Si true, on mappe un dossier local dans le nœud k3d pour stocker /var/lib/rancher/k3s/storage
PERSIST_ON_HOST=false
HOST_STORAGE_DIR="/var/lib/k3d-${CLUSTER_NAME}-storage"   # dossier sur ta VM
########################################

echo "==> 1) Installer kubectl si absent"
if ! command -v kubectl >/dev/null 2>&1; then
  curl -sSL -o /usr/local/bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.29.2/bin/linux/amd64/kubectl
  chmod +x /usr/local/bin/kubectl
fi

echo "==> 2) Installer k3d si absent"
if ! command -v k3d >/dev/null 2>&1; then
  curl -sSL https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
fi

echo "==> 3) Créer le cluster k3d '${CLUSTER_NAME}' (LB -> ${HOST_HTTP_PORT})"
if ! k3d cluster list | grep -q "^${CLUSTER_NAME}\b"; then
  if $PERSIST_ON_HOST; then
    # Prépare le dossier hôte pour stocker le backend local-path
    mkdir -p "${HOST_STORAGE_DIR}"
    # Monte ce dossier vers /var/lib/rancher/k3s/storage du nœud serveur
    k3d cluster create "${CLUSTER_NAME}" \
      -p "${HOST_HTTP_PORT}:80@loadbalancer" \
      --volume "${HOST_STORAGE_DIR}:/var/lib/rancher/k3s/storage@server:0" \
      --wait
  else
    k3d cluster create "${CLUSTER_NAME}" -p "${HOST_HTTP_PORT}:80@loadbalancer" --wait
  fi
else
  echo "   - Cluster '${CLUSTER_NAME}' déjà existant, on continue."
fi

echo "==> 4) kubeconfig (merge + switch)"
k3d kubeconfig merge "${CLUSTER_NAME}" --kubeconfig-merge-default --kubeconfig-switch-context
kubectl cluster-info >/dev/null

echo "==> 5) Namespace"
kubectl get ns "${NS}" >/dev/null 2>&1 || kubectl create ns "${NS}"

echo "==> 6) Secret (MISTRAL_API_KEY)"
if [[ -z "${MISTRAL_API_KEY:-}" ]]; then
  read -s -p "Tape ta MISTRAL_API_KEY (masquée) : " MISTRAL_API_KEY; echo
fi
kubectl -n "${NS}" delete secret chatbot-secret >/dev/null 2>&1 || true
kubectl -n "${NS}" create secret generic chatbot-secret \
  --from-literal=MISTRAL_API_KEY="${MISTRAL_API_KEY}"

echo "==> 7) Import de l'image ACR dans le cluster"
docker pull "${IMAGE_ACR}"
k3d image import "${IMAGE_ACR}" -c "${CLUSTER_NAME}"

echo "==> 8) PVCs (database + vector_db) avec storageClass 'local-path'"
cat <<YAML | kubectl apply -n "${NS}" -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: chatbot-db-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: ${DB_SIZE}
  storageClassName: local-path
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: chatbot-vectordb-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: ${VECTOR_SIZE}
  storageClassName: local-path
YAML

echo "==> 9) Déploiement + Service (LoadBalancer) avec montages de volumes"
cat <<YAML | kubectl apply -n "${NS}" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: chatbot
  template:
    metadata:
      labels:
        app: chatbot
    spec:
      containers:
      - name: chatbot
        image: ${IMAGE_ACR}
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: ${APP_PORT}
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatbot-secret
              key: MISTRAL_API_KEY
        - name: STREAMLIT_SERVER_PORT
          value: "${APP_PORT}"
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        - name: CHROMA_PATH
          value: "/app/vector_db"
        - name: DATABASE_PATH
          value: "/app/database"
        volumeMounts:
        - name: db
          mountPath: /app/database
        - name: vectordb
          mountPath: /app/vector_db
        readinessProbe:
          httpGet: { path: "/", port: ${APP_PORT} }
          initialDelaySeconds: 10
          periodSeconds: 10
        livenessProbe:
          httpGet: { path: "/", port: ${APP_PORT} }
          initialDelaySeconds: 30
          periodSeconds: 20
      volumes:
      - name: db
        persistentVolumeClaim:
          claimName: chatbot-db-pvc
      - name: vectordb
        persistentVolumeClaim:
          claimName: chatbot-vectordb-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: chatbot
spec:
  type: LoadBalancer
  selector:
    app: chatbot
  ports:
  - port: 80
    targetPort: ${APP_PORT}
YAML

echo "==> 10) Attente du déploiement"
kubectl -n "${NS}" rollout status deploy/chatbot

echo "==> 11) URL d'accès"
IP=$(hostname -I | awk '{print $1}')
echo "http://${IP}:${HOST_HTTP_PORT}/"
echo "Ou depuis la VM: http://127.0.0.1:${HOST_HTTP_PORT}/"

echo "✅ Déploiement k3d + PVC terminé."
