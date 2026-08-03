#!/bin/bash
# ============================================================
# OpenStack 安装脚本 - MicroStack (Ubuntu 22.04/24.04)
# 实验16：综合实验-OpenStack安装与集群搭建
# ============================================================

set -e

echo "========================================="
echo "  OpenStack MicroStack 安装脚本"
echo "  实验16 - 综合实验"
echo "========================================="

# ---------- Step 1: 系统更新 ----------
echo ""
echo "[Step 1/5] 更新系统包..."
sudo apt update -y && sudo apt upgrade -y

# ---------- Step 2: 安装必要依赖 ----------
echo ""
echo "[Step 2/5] 安装必要依赖..."
sudo apt install -y curl wget net-tools openssh-server snapd python3-pip

# ---------- Step 3: 安装 MicroStack ----------
echo ""
echo "[Step 3/5] 安装 MicroStack (OpenStack 2023.1/Antelope)..."
sudo snap install microstack --channel=2023.1/stable

# ---------- Step 4: 初始化 MicroStack ----------
echo ""
echo "[Step 4/5] 初始化 MicroStack (这可能需要5-10分钟)..."
echo "请耐心等待..."
sudo microstack init --auto --control

# ---------- Step 5: 获取登录信息 ----------
echo ""
echo "[Step 5/5] 获取 Dashboard 登录信息..."
echo ""
echo "========================================="
echo "  OpenStack 安装完成!"
echo "========================================="
echo ""
echo "Dashboard URL: https://$(hostname -I | awk '{print $1}')/"
echo ""
echo "管理员账号信息:"
ADMIN_PASSWORD=$(sudo snap get microstack config.credentials.keystone-password 2>/dev/null || echo "请手动获取")
echo "  用户名: admin"
echo "  密码: ${ADMIN_PASSWORD}"
echo ""
echo "如果密码未显示，请执行:"
echo "  sudo snap get microstack config.credentials.keystone-password"
echo ""
echo "========================================="
