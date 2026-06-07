# Self-Healing MLOps Project - FA23BAI066

## Assigned customization values

- Roll number: `FA23-BAI-066`
- Confidence Threshold: `0.693`
- Stable Model Code: `FB0F`
- Stable model_version Field: `stable-v0-FB0F`
- Webhook Token: `ROLLBACK_ACB434_TOKEN`
- Test Category: `APP`
- Test Text: `This app is incredibly intuitive and has made my daily workflow dramatically more efficient`

## Critical placeholders you must replace before pushing/submitting

Run this from the repository root:

```bash
python3 configure_placeholders.py
```

It will replace:

- `YOUR_DOCKERHUB_USERNAME`
- `YOUR_EC2_PUBLIC_IP`
- `YOUR_JENKINS_USERNAME`
- `YOUR_JENKINS_API_TOKEN`

Do not submit while any of these remain:

```bash
grep -R "YOUR_" . --exclude-dir=.git
```

## GitHub repository

Create a public GitHub repository named exactly:

```text
selfhealing-mlops-FA23BAI066
```

This ZIP already contains a Git repository with two branches:

- `main`
- `stable-fallback`

Push both branches:

```bash
git remote add origin https://github.com/<your-github-username>/selfhealing-mlops-FA23BAI066.git
git branch
git push -u origin main
git push -u origin stable-fallback
```

If Git says remote already exists:

```bash
git remote set-url origin https://github.com/<your-github-username>/selfhealing-mlops-FA23BAI066.git
```

## EC2 Security Group ports

Open inbound TCP ports:

```text
22, 8080, 9090, 9093, 3000, 8000, 32500
```

Use Ubuntu 22.04 on at least `t2.large` or better. Smaller instances will likely fail because DistilBERT + Docker + Minikube + Jenkins is memory-heavy.

## EC2 base setup commands

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release apt-transport-https unzip git python3-pip openjdk-17-jdk

# Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
sudo usermod -aG docker jenkins || true

# Minikube + kubectl
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
minikube start --driver=docker --memory=6144 --cpus=2
kubectl get nodes

# Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# Give Jenkins kubectl/minikube access
sudo mkdir -p /var/lib/jenkins/.kube /var/lib/jenkins/.minikube
sudo cp -r ~/.kube/* /var/lib/jenkins/.kube/ || true
sudo cp -r ~/.minikube/* /var/lib/jenkins/.minikube/ || true
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube /var/lib/jenkins/.minikube
```

Log out/in after Docker group changes or run `newgrp docker`.

## Jenkins setup

1. Open `http://<EC2_PUBLIC_IP>:8080`.
2. Install suggested plugins.
3. Install additional plugin: `Generic Webhook Trigger`.
4. Add DockerHub credential:
   - Kind: Username with password
   - ID: `dockerhub-creds`
5. Create pipeline job exactly named: `sentiment-ci-pipeline`.
   - Pipeline from SCM -> Git -> your repo URL -> branch `main` -> script path `Jenkinsfile`.
6. Create pipeline job exactly named: `rollback-to-stable`.
   - Build Triggers -> Generic Webhook Trigger
   - Token: `ROLLBACK_ACB434_TOKEN`
   - Pipeline from SCM -> Git -> your repo URL -> branch `main` -> script path `Jenkinsfile.rollback`.

## GitHub webhook

Repository Settings -> Webhooks -> Add webhook:

```text
Payload URL: http://<EC2_PUBLIC_IP>:8080/github-webhook/
Content type: application/json
Events: Just the push event
Active: yes
```

## Monitoring setup

Install exporter dependencies and run exporter on EC2:

```bash
cd selfhealing-mlops-FA23BAI066
python3 -m pip install --user prometheus-client==0.20.0 requests==2.32.3
nohup python3 exporter.py >/tmp/sentiment-exporter.log 2>&1 &
curl http://127.0.0.1:8000/metrics | grep prediction_confidence_score
```

Run Alertmanager and Prometheus with host networking so `localhost:8000` and `localhost:9093` work from the containers:

```bash
docker rm -f alertmanager prometheus || true

docker run -d --name alertmanager --network host \
  -v "$PWD/alertmanager.yml:/etc/alertmanager/alertmanager.yml" \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml

docker run -d --name prometheus --network host \
  -v "$PWD/prometheus.yml:/etc/prometheus/prometheus.yml" \
  -v "$PWD/alert.rules.yml:/etc/prometheus/alert.rules.yml" \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml

curl http://127.0.0.1:9090/targets
```

## Grafana setup

```bash
sudo apt-get install -y software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana
sudo systemctl enable --now grafana-server
```

Then open `http://<EC2_PUBLIC_IP>:3000`.

- Data source: Prometheus
- URL: `http://localhost:9090`
- Dashboard name: `MLOps - Sentiment API Health`
- Panel title: `Prediction Confidence Score`
- Query: `prediction_confidence_score`
- Red threshold: `0.693`

## Manual end-to-end validation

```bash
# Blue/unstable should be active
curl http://<EC2_PUBLIC_IP>:32500/health

# Prediction should be confident before drift
curl -X POST http://<EC2_PUBLIC_IP>:32500/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"This app is incredibly intuitive and has made my daily workflow dramatically more efficient"}'

# Inject drift
curl -X POST http://<EC2_PUBLIC_IP>:32500/inject-drift

# Generate a low-confidence prediction
curl -X POST http://<EC2_PUBLIC_IP>:32500/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Great product"}'

# Confirm metric
curl http://<EC2_PUBLIC_IP>:8000/metrics | grep prediction_confidence_score

# Wait about 90 seconds, then confirm the alert and rollback
curl http://<EC2_PUBLIC_IP>:9090/alerts
curl http://<EC2_PUBLIC_IP>:32500/health
```

Final health after rollback must contain:

```json
"model_version": "stable-v0-FB0F"
```

## Google Form submission values

Submit:

1. Full Name and Roll Number: your full name + `FA23BAI066`
2. GitHub Repository URL: your public repo URL
3. AWS EC2 Public IP Address: your EC2 public IPv4
4. DockerHub Username: your DockerHub username
5. Jenkins Username: the username used for grading
6. Jenkins API Token: generated from Jenkins profile
