#!/bin/bash
# 首问责任平台服务器安装脚本(Ubuntu 24.04;由 _setup_server.py 上传执行)
set -e
cd /home/userspl
echo "== 解压部署包 =="
rm -rf shouwen
mkdir -p shouwen
tar -xzf deploy_bundle.tar.gz -C shouwen --strip-components=1
ls shouwen

echo "== Python venv =="
echo 123456 | sudo -S DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv 2>&1 | tail -1
cd shouwen
python3 -m venv venv
./venv/bin/pip install -q -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip 2>&1 | tail -1
./venv/bin/pip install -q -i https://mirrors.aliyun.com/pypi/simple/ \
  -r agent-service/requirements.txt fastembed psycopg2-binary "python-jose[cryptography]" \
  bcrypt python-multipart 2>&1 | tail -2
echo "venv ok"

echo "== 恢复数据库 =="
source /home/userspl/.pg_env   # 提供 PGPASSWORD(由上传方生成,不入日志)
echo 123456 | sudo -S -u postgres psql -qc "ALTER USER postgres PASSWORD '$PGPASSWORD'"
echo 123456 | sudo -S -u postgres psql -qc "DROP DATABASE IF EXISTS shouwenzeren_agent"
echo 123456 | sudo -S -u postgres psql -qc "CREATE DATABASE shouwenzeren_agent"
echo 123456 | sudo -S -u postgres psql -q -d shouwenzeren_agent \
  -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;"
PGPASSWORD=$PGPASSWORD pg_restore -h 127.0.0.1 -U postgres -d shouwenzeren_agent \
  --no-owner --no-privileges shouwenzeren_agent.dump 2>&1 | tail -3 || true
PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U postgres -d shouwenzeren_agent -tAc \
  "SELECT (SELECT count(*) FROM public.people), (SELECT count(*) FROM rag.rag_chunks)"

echo "== systemd 服务 =="
echo 123456 | sudo -S tee /etc/systemd/system/shouwen-backend.service > /dev/null <<'EOF'
[Unit]
Description=shouwen backend (FastAPI CRUD)
After=network.target postgresql.service

[Service]
User=userspl
WorkingDirectory=/home/userspl/shouwen/backend
ExecStart=/home/userspl/shouwen/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
echo 123456 | sudo -S tee /etc/systemd/system/shouwen-agent.service > /dev/null <<'EOF'
[Unit]
Description=shouwen agent-service (AGUI/Agent/RAG)
After=network.target postgresql.service

[Service]
User=userspl
WorkingDirectory=/home/userspl/shouwen/agent-service
Environment=FASTEMBED_CACHE_PATH=/home/userspl/shouwen/fastembed_cache
ExecStart=/home/userspl/shouwen/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
echo 123456 | sudo -S systemctl daemon-reload
echo 123456 | sudo -S systemctl enable --now shouwen-backend shouwen-agent

echo "== nginx =="
echo 123456 | sudo -S tee /etc/nginx/sites-available/shouwen > /dev/null <<'EOF'
server {
    listen 80 default_server;
    server_name _;
    root /home/userspl/shouwen/frontend/dist;
    index index.html;

    location /api/v1/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /api/agui/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
    location / {
        try_files $uri /index.html;
    }
}
EOF
echo 123456 | sudo -S rm -f /etc/nginx/sites-enabled/default
echo 123456 | sudo -S ln -sf /etc/nginx/sites-available/shouwen /etc/nginx/sites-enabled/shouwen
echo 123456 | sudo -S nginx -t
echo 123456 | sudo -S systemctl restart nginx

sleep 3
echo "== 自检 =="
curl -s http://127.0.0.1:8001/health
echo
curl -s http://127.0.0.1:8100/health
echo
curl -s -o /dev/null -w "frontend: %{http_code}\n" http://127.0.0.1/
echo "SETUP_DONE"
