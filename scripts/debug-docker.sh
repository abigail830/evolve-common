#!/bin/bash
# Docker网络调试脚本

# 输出分隔线
echo "=================================================="
echo "Docker网络调试脚本"
echo "=================================================="

# 检查Docker是否运行
echo "检查Docker运行状态..."
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装"
    docker --version
else
    echo "❌ Docker未安装"
    exit 1
fi

# 检查Docker服务状态
echo -e "\n检查Docker服务状态..."
if systemctl is-active docker &> /dev/null || service docker status &> /dev/null; then
    echo "✅ Docker服务正在运行"
else
    echo "❌ Docker服务未运行"
    echo "尝试启动Docker服务..."
    sudo systemctl start docker || sudo service docker start
fi

# 检查Docker容器
echo -e "\n检查Docker容器..."
docker ps -a

# 检查API容器状态
echo -e "\n检查API容器状态..."
docker inspect evolve-file-processor-api-1 -f '{{.State.Status}}' || echo "API容器不存在"
docker inspect evolve-file-processor-api-1 -f '{{.State.Health.Status}}' || echo "API容器健康状态不可用"

# 检查API容器日志
echo -e "\n检查API容器日志..."
docker logs evolve-file-processor-api-1 --tail 20 || echo "无法获取API容器日志"

# 检查Docker网络
echo -e "\n检查Docker网络..."
docker network ls
docker network inspect evolve-file-processor_default || echo "默认网络不存在"

# 检查容器IP地址
echo -e "\n检查容器IP地址..."
docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -q) || echo "无法获取容器IP地址"

# 尝试从主机访问API
echo -e "\n尝试从主机访问API..."
API_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' evolve-file-processor-api-1 2>/dev/null)
if [ -n "$API_IP" ]; then
    echo "API容器IP: $API_IP"
    curl -v http://$API_IP:8000/ || echo "无法通过IP访问API"
else
    echo "无法获取API容器IP地址"
fi

# 尝试在API容器内安装curl并测试连接
echo -e "\n尝试在API容器内安装curl并测试连接..."
docker exec evolve-file-processor-api-1 sh -c "apt-get update && apt-get install -y curl && curl -v http://localhost:8000/" || echo "无法在API容器内执行命令"

# 检查Docker Compose配置
echo -e "\n检查Docker Compose配置..."
cat docker-compose.yml || echo "无法读取docker-compose.yml"
cat docker-compose.override.yml || echo "无法读取docker-compose.override.yml"

echo -e "\n=================================================="
echo "调试完成"
echo "==================================================" 