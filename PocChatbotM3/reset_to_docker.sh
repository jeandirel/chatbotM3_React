# reset_to_docker.sh
set -euo pipefail

echo "==> 1) Arrêt des services Podman (silencieux si absents)"
systemctl --user stop podman.socket podman.service 2>/dev/null || true
sudo systemctl stop podman.socket 2>/dev/null || true

echo "==> 2) Suppression des paquets Podman et écosystème"
sudo dnf remove -y podman podman-remote podman-plugins podman-compose \
  buildah skopeo conmon crun runc containers-common container-selinux 2>/dev/null || true

echo "==> 3) Nettoyage des alias/wrappers 'docker' qui pointent vers Podman"
# wrapper le plus courant
if [ -x /usr/local/bin/docker ]; then
  sudo mv /usr/local/bin/docker /usr/local/bin/docker.podman.bak.$(date +%s)
fi
# alias shells éventuels
sed -i '/alias docker=/d' ~/.bashrc || true
sudo find /etc/profile.d -maxdepth 1 -type f -name '*podman*' -print -exec sudo sed -i '/alias docker=/d' {} \; 2>/dev/null || true
hash -r || true

echo "==> 4) Purge des répertoires Podman utilisateur (rootless)"
rm -rf ~/.local/share/containers ~/.config/containers ~/.cache/containers 2>/dev/null || true

echo "==> 5) Purge du répertoire global utilisé (/mnt/podman) si existant"
if [ -d /mnt/podman ]; then
  sudo rm -rf /mnt/podman
fi

echo "==> 6) Installation du dépôt Docker CE"
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo

echo "==> 7) Installation de Docker Engine + plugin Compose"
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> 8) Activation du service Docker"
sudo systemctl enable --now docker

echo "==> 9) Ajout de l'utilisateur au groupe docker"
if ! id -nG "$USER" | grep -qw docker; then
  sudo usermod -aG docker "$USER"
  echo ">>> IMPORTANT : déconnecte/reconnecte ta session (ou 'newgrp docker') pour appliquer le groupe."
fi

echo "==> 10) Vérifications"
docker --version
docker compose version
sudo systemctl status docker --no-pager | sed -n '1,5p'

echo "==> 11) (Optionnel) Ouvrir le port 8501 si accès réseau nécessaire"
sudo firewall-cmd --add-port=8501/tcp --permanent || true
sudo firewall-cmd --reload || true

echo "==> Fini. Si 'docker compose version' s'affiche, tout est OK."
