# AWS Deployment Plan

## Goal

Deploy the FastAPI UI and recommendation API to one AWS EC2 instance with HTTP access by public IP. The app must use the configured OpenAI API key for query interpretation in AWS, while product retrieval remains scoped to the included Amazon Fashion sample index.

## Target Architecture

```text
Reviewer browser
  -> http://PUBLIC_IP:8000
  -> EC2 instance
     -> FastAPI + static UI
     -> /etc/fashion-recommender.env for server-side secrets
     -> local data/index vector files
     -> OpenAI API for query interpretation and explanations
```

## Free-Tier Guardrails

Keep the deployment limited to:

- One free-tier eligible EC2 instance.
- One small root EBS volume, for example 8 GB.
- The default public IPv4 address assigned to the running instance.
- One security group inbound HTTP/demo port rule.

Avoid these resources for this assignment deployment:

- Application Load Balancer.
- NAT Gateway.
- RDS or any managed database.
- Route 53 hosted zone or domain.
- Elastic IP unless you have verified it stays inside the current free-tier rules for the account.
- AWS Secrets Manager, because a local root-owned environment file is enough here.
- S3, CloudFront, ECS, ECR, Lambda, or API Gateway.

## Deployment Steps

1. Launch an Amazon Linux EC2 instance using a free-tier eligible instance type for the account and region.
2. Set the root EBS volume to a small size, such as 8 GB.
3. Add a security group inbound rule for TCP `8000`.
4. SSH to the instance.
5. Install Python and Git:

```bash
sudo dnf update -y
sudo dnf install -y git python3.11 python3.11-pip
```

6. Clone the repository:

```bash
sudo mkdir -p /opt/fashion-recommender
sudo chown ec2-user:ec2-user /opt/fashion-recommender
git clone https://github.com/javithsherif27/fashion-recommender.git /opt/fashion-recommender
cd /opt/fashion-recommender
```

7. Install Python dependencies:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

8. Create the private secret file:

```bash
sudo tee /etc/fashion-recommender.env >/dev/null <<'EOF'
OPENAI_API_KEY=replace-with-runtime-key
OPENAI_MODEL=gpt-4o-mini
USE_LLM=auto
REQUIRE_OPENAI=true
INDEX_DIR=data/index
EMBEDDING_BACKEND=auto
EOF
sudo chown root:root /etc/fashion-recommender.env
sudo chmod 600 /etc/fashion-recommender.env
```

9. Create the service:

```bash
sudo tee /etc/systemd/system/fashion-recommender.service >/dev/null <<'EOF'
[Unit]
Description=Fashion recommender FastAPI service
After=network-online.target
Wants=network-online.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/fashion-recommender
EnvironmentFile=/etc/fashion-recommender.env
ExecStart=/opt/fashion-recommender/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now fashion-recommender
```

10. Confirm service status:

```bash
sudo systemctl status fashion-recommender --no-pager
curl http://127.0.0.1:8000/health
```

## Acceptance Tests

From a local machine:

```bash
curl http://PUBLIC_IP:8000/health
```

Expected signals:

```json
{
  "status": "ok",
  "llm_configured": true,
  "llm_required": true
}
```

Run a recommendation:

```bash
curl -X POST http://PUBLIC_IP:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query":"what should I wear to a beach wedding","top_k":5,"filters":{"require_price":true}}'
```

Expected signals:

```json
{
  "llm_used": true,
  "llm_provider": "openai"
}
```

The recommendation list should normally contain products for valid fashion requests. It is acceptable for a narrow filtered request to return zero products, but every hosted response must still show `llm_used: true` and `llm_provider: openai` when OpenAI is correctly configured.

## Failure Behavior

With `REQUIRE_OPENAI=true`, the app intentionally does not fall back to local query interpretation. If the key is missing or OpenAI fails, `/recommend` returns HTTP `503` with a clear error. This makes AWS demo misconfiguration visible immediately.

The app still uses local vector search over `data/index`, because searching the Amazon Fashion sample dataset is the assignment requirement.
