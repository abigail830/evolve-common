#!/bin/bash
# Nginx调试脚本

# 输出分隔线
echo "=================================================="
echo "Nginx调试脚本"
echo "=================================================="

# 检查Nginx是否安装
echo "检查Nginx安装状态..."
if command -v nginx &> /dev/null; then
    echo "✅ Nginx已安装"
    nginx -v
else
    echo "❌ Nginx未安装"
    exit 1
fi

# 检查Nginx状态
echo -e "\n检查Nginx运行状态..."
if systemctl is-active nginx &> /dev/null || service nginx status &> /dev/null; then
    echo "✅ Nginx正在运行"
else
    echo "❌ Nginx未运行"
    echo "尝试启动Nginx..."
    sudo systemctl start nginx || sudo service nginx start
fi

# 检查配置文件
echo -e "\n查找Nginx配置文件..."
echo "标准配置目录:"
sudo find /etc/nginx -name "*.conf" | sort

# 检查file-processor配置
echo -e "\n检查file-processor配置文件..."
if sudo find /etc/nginx -name "*file-processor*" | grep -q .; then
    echo "✅ 找到file-processor配置文件:"
    sudo find /etc/nginx -name "*file-processor*"
    
    # 显示配置内容
    echo -e "\n配置文件内容:"
    sudo cat $(sudo find /etc/nginx -name "*file-processor*" | head -1)
else
    echo "❌ 未找到file-processor配置文件"
    
    # 查找可能的配置目录
    if [ -d "/etc/nginx/conf.d" ]; then
        NGINX_CONF_DIR="/etc/nginx/conf.d"
    elif [ -d "/etc/nginx/sites-available" ]; then
        NGINX_CONF_DIR="/etc/nginx/sites-available"
    else
        NGINX_CONF_DIR="/etc/nginx/conf.d"
        sudo mkdir -p $NGINX_CONF_DIR
    fi
    
    echo "创建默认配置在 $NGINX_CONF_DIR/file-processor.evolving.team.conf"
    echo 'server { listen 80; server_name file-processor.evolving.team; location / { proxy_pass http://localhost:8000; } }' | sudo tee $NGINX_CONF_DIR/file-processor.evolving.team.conf > /dev/null
    
    # 如果是sites-available目录，创建符号链接
    if [ "$NGINX_CONF_DIR" = "/etc/nginx/sites-available" ]; then
        sudo ln -sf $NGINX_CONF_DIR/file-processor.evolving.team.conf /etc/nginx/sites-enabled/
    fi
fi

# 检查Nginx配置语法
echo -e "\n检查Nginx配置语法..."
if sudo nginx -t; then
    echo "✅ Nginx配置语法正确"
else
    echo "❌ Nginx配置语法错误"
fi

# 检查FastAPI应用状态
echo -e "\n检查FastAPI应用状态..."
docker ps | grep evolve-file-processor-api

# 尝试访问API
echo -e "\n尝试访问API..."
echo "从主机访问:"
curl -v http://localhost:8000/ || echo "无法从主机访问API"

echo -e "\n从容器内部访问:"
docker exec evolve-file-processor-api-1 curl -v http://localhost:8000/ || echo "无法从容器内部访问API"

# 检查网络连接
echo -e "\n检查网络连接..."
echo "检查端口8000:"
sudo netstat -tulpn | grep 8000 || echo "端口8000未被监听"

# 检查Nginx日志
echo -e "\n检查Nginx错误日志..."
sudo tail -n 20 /var/log/nginx/error.log || echo "无法访问Nginx错误日志"

echo -e "\n检查Nginx访问日志..."
sudo tail -n 20 /var/log/nginx/access.log || echo "无法访问Nginx访问日志"

echo -e "\n=================================================="
echo "调试完成"
echo "==================================================" 