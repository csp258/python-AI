#!/bin/bash
# ============================================================
# 集群配置脚本 - SSH免密登录 & hosts配置
# 在每台实例上执行
# ============================================================

echo "========================================="
echo "  集群配置脚本"
echo "  SSH免密登录 + hosts映射"
echo "========================================="

# ---------- 系统基础配置 ----------
echo ""
echo "[Step 1/5] 更新系统并安装SSH服务..."
sudo apt update -y
sudo apt install -y openssh-server net-tools curl wget vim

# 启��SSH服务
sudo systemctl enable ssh
sudo systemctl start ssh

# ---------- 修改主机名 ----------
echo ""
echo "[Step 2/5] 设置主机名..."
echo "请根据当前虚拟机选择对应的主机名:"
echo "  1) vm1"
echo "  2) vm2"
echo "  3) vm3"
read -p "请选择 (1/2/3): " choice

case $choice in
    1) HOSTNAME="vm1";;
    2) HOSTNAME="vm2";;
    3) HOSTNAME="vm3";;
    *) echo "无效选择"; exit 1;;
esac

sudo hostnamectl set-hostname "$HOSTNAME"
echo "主机名设置为: $HOSTNAME"

# ---------- 获取本机IP ----------
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "本机IP: $LOCAL_IP"

# ---------- 生成SSH密钥 ----------
echo ""
echo "[Step 3/5] 生成SSH密钥对..."
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 2048 -N "" -f ~/.ssh/id_rsa
    echo "SSH密钥对已生成"
else
    echo "SSH密钥对已存在"
fi

# ---------- 配置hosts文件 ----------
echo ""
echo "[Step 4/5] 配置hosts文件..."

# 收集其他节点的IP
read -p "请输入 vm1 的IP地址: " VM1_IP
read -p "请输入 vm2 的IP地址: " VM2_IP
read -p "请输入 vm3 的IP地址: " VM3_IP

echo "添加hosts映射..."
sudo bash -c "cat >> /etc/hosts << EOF

# OpenStack集群节点
${VM1_IP} vm1
${VM2_IP} vm2
${VM3_IP} vm3
EOF"

echo "hosts文件已更新"

# ---------- SSH免密登录配置 ----------
echo ""
echo "[Step 5/5] 配置SSH免密登录..."

# 显示本机公钥（需要复制到其他节点）
echo ""
echo "========================================="
echo "  本机公钥 (复制到其他节点):"
echo "========================================="
cat ~/.ssh/id_rsa.pub
echo ""
echo "========================================="
echo ""
echo "请在其他两台节点上执行以下命令来添加本机公钥:"
echo "  echo '上述公钥内容' >> ~/.ssh/authorized_keys"
echo ""
echo "然后在本机执行以下命令拷贝公钥到其他节点:"
echo "  ssh-copy-id vm1  # (如果当前不是vm1)"
echo "  ssh-copy-id vm2  # (如果当前不是vm2)"
echo "  ssh-copy-id vm3  # (如果当前不是vm3)"
echo ""
echo "测试连接:"
echo "  ssh vm1 hostname"
echo "  ssh vm2 hostname"
echo "  ssh vm3 hostname"
echo "========================================="
