#!/bin/bash
# 安装Git钩子脚本

echo "正在安装Git钩子..."

# 确保脚本目录存在
HOOK_DIR=".git/hooks"
mkdir -p $HOOK_DIR

# 复制pre-commit钩子
cp scripts/pre-commit-check.sh $HOOK_DIR/pre-commit
chmod +x $HOOK_DIR/pre-commit

echo "✅ Git钩子安装完成"
echo "现在每次提交前会自动检查requirements.txt是否包含大型依赖" 