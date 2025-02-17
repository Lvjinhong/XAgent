FROM node:lts-alpine AS XAgentWeb
EXPOSE 5173
WORKDIR /app
COPY ./XAgentWeb/package.json ./
RUN npm config set registry https://registry.npmmirror.com/ && npm install
COPY ./XAgentWeb .
RUN npm run build


FROM python:3.10 AS XAgentServer
EXPOSE 8090
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN apt-get update --fix-missing
RUN apt-get install -y nginx systemctl
WORKDIR /app
COPY --from=XAgentWeb /app/dist ./dist/
COPY ./XAgentServer/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./XAgentServer/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN systemctl start nginx
# HEALTHCHECK --interval=5s --timeout=10s --retries=3 CMD ["bash", "-c", "curl -sS 'http://localhost:8090/' > /dev/null || exit 1"]
ENTRYPOINT [ "python", "start_server.py" ]
