#!/bin/bash
# 这个脚本用于释放PostgreSQL端口(5432)

echo "===== PostgreSQL端口清理工具 ====="
echo "尝试识别并释放5432端口..."

# 找出所有占用5432端口的进程
PORT_PROCESSES=$(lsof -i :5432 -t || ss -tulpn | grep ':5432' | grep LISTEN | awk '{print $7}' | sed 's/users:((".*",pid=\([0-9]*\).*/\1/g' || true)

if [ -z "$PORT_PROCESSES" ]; then
    echo "✓ 端口5432当前未被占用"
    exit 0
fi

echo "⚠️ 发现以下进程占用PostgreSQL端口5432:"
for pid in $PORT_PROCESSES; do
    # 显示进程详情
    ps -p $pid -o pid,user,command || true
done

echo "---"
echo "尝试终止这些进程..."

for pid in $PORT_PROCESSES; do
    echo "终止进程 $pid"
    kill -15 $pid || true
    sleep 1
    
    # 检查进程是否仍在运行
    if ps -p $pid > /dev/null; then
        echo "进程仍在运行，尝试强制终止"
        kill -9 $pid || true
    fi
done

# 等待一下让系统释放端口
sleep 3

# 检查端口是否已被释放
if lsof -i :5432 > /dev/null 2>&1 || ss -tulpn | grep ':5432' | grep LISTEN > /dev/null 2>&1; then
    echo "❌ 端口释放失败，尝试强制关闭所有连接..."
    
    # 使用ss命令强制关闭连接 (需要root权限)
    if command -v ss > /dev/null && [ $(id -u) -eq 0 ] || sudo -n true 2>/dev/null; then
        sudo ss -K dport = :5432 || true
        echo "已尝试强制关闭所有连接"
        sleep 2
    else
        echo "警告: 没有足够权限执行强制关闭连接操作"
    fi
    
    # 再次检查
    if lsof -i :5432 > /dev/null 2>&1 || ss -tulpn | grep ':5432' | grep LISTEN > /dev/null 2>&1; then
        echo "❌ 端口5432仍被占用，请尝试手动解决或使用不同端口"
        exit 1
    else
        echo "✓ 端口已成功释放"
    fi
else
    echo "✓ 端口已成功释放"
fi

echo "==== 端口清理完成 ===="
exit 0 