#!/bin/bash
# ============================================================
# OpenStack 实例创建脚本
# 创建3台虚拟机实例: vm1, vm2, vm3
# ============================================================

set -e

echo "========================================="
echo "  OpenStack 实例创建脚本"
echo "  创建 vm1, vm2, vm3"
echo "========================================="

# ---------- 配置环境变量 ----------
echo ""
echo "[Step 1/7] 配置 admin 环境变量..."
source /var/snap/microstack/common/etc/microstack/admin-openrc.sh 2>/dev/null || \
source /var/snap/microstack/common/etc/admin-openrc.sh 2>/dev/null || {
    echo "请先运行: source /var/snap/microstack/common/etc/microstack/admin-openrc.sh"
    exit 1
}

# ---------- 检查已有资源 ----------
echo ""
echo "[Step 2/7] 检查现有资源..."
echo "--- 镜像列表 ---"
openstack image list
echo "--- 网络列表 ---"
openstack network list
echo "--- Flavor列表 ---"
openstack flavor list
echo "--- 安全组列表 ---"
openstack security group list

# ---------- 上传 Ubuntu 云镜像（如果没有CirrOS） ----------
echo ""
echo "[Step 3/7] 准备镜像..."
IMAGE_COUNT=$(openstack image list -f value | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "没有可用镜像，正在下载 Ubuntu Cloud Image..."
    wget -O ubuntu-22.04.qcow2 https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img 2>/dev/null || {
        echo "下载Ubuntu镜像失败，尝试下载CirrOS..."
        wget -O cirros.img http://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img
        openstack image create --file cirros.img --disk-format qcow2 --container-format bare --public "cirros-0.6.2"
    }
    if [ -f ubuntu-22.04.qcow2 ]; then
        openstack image create --file ubuntu-22.04.qcow2 --disk-format qcow2 --container-format bare --public "ubuntu-22.04"
    fi
else
    echo "已有镜像，跳过下载。"
fi

# ---------- 确保安全组允许 SSH 和 ICMP ----------
echo ""
echo "[Step 4/7] 配置安全组规则..."
SEC_GROUP=$(openstack security group list --project admin -f value -c ID 2>/dev/null | head -1)
if [ -n "$SEC_GROUP" ]; then
    openstack security group rule create --proto tcp --dst-port 22 "$SEC_GROUP" 2>/dev/null || echo "SSH规则已存在"
    openstack security group rule create --proto icmp "$SEC_GROUP" 2>/dev/null || echo "ICMP规则已存在"
fi

# ---------- 获取网络 ----------
echo ""
echo "[Step 5/7] 检查网络配置..."
# MicroStack默认创建 external 和 internal 网络
EXTERNAL_NET=$(openstack network list --external -f value -c Name 2>/dev/null | head -1)
INTERNAL_NET=$(openstack network list --internal -f value -c Name 2>/dev/null | head -1)

if [ -z "$EXTERNAL_NET" ]; then
    echo "创建外部网络..."
    openstack network create --external --provider-network-type flat --provider-physical-network physnet1 external
    openstack subnet create --network external --subnet-range 10.20.20.0/24 --allocation-pool start=10.20.20.100,end=10.20.20.200 --gateway 10.20.20.1 --dns-nameserver 8.8.8.8 external-subnet
    EXTERNAL_NET="external"
fi

echo "外部网络: $EXTERNAL_NET"
echo "内部网络: $INTERNAL_NET"

# ---------- 获取Flavor ----------
FLAVOR=$(openstack flavor list -f value -c Name 2>/dev/null | head -1)
if [ -z "$FLAVOR" ]; then
    echo "创建默认 Flavor..."
    openstack flavor create --ram 1024 --disk 10 --vcpus 1 m1.small
    FLAVOR="m1.small"
fi
echo "Flavor: $FLAVOR"

# ---------- 创建3台实例 ----------
echo ""
echo "[Step 6/7] 创建3台虚拟机实例..."

IMAGE=$(openstack image list -f value -c Name 2>/dev/null | head -1)
echo "使用镜像: $IMAGE"

for i in 1 2 3; do
    echo "创建 vm${i}..."
    openstack server create \
        --image "$IMAGE" \
        --flavor "$FLAVOR" \
        --nic net-id=$(openstack network list --internal -f value -c ID 2>/dev/null | head -1) \
        --wait \
        vm${i} 2>/dev/null || {
        # 如果内部网络不存在，尝试不使用 --nic 参数
        openstack server create \
            --image "$IMAGE" \
            --flavor "$FLAVOR" \
            --wait \
            vm${i}
    }
    echo "vm${i} 创建完成!"
done

# ---------- 分配浮动IP ----------
echo ""
echo "[Step 7/7] 分配浮动IP并绑定到实例..."

for i in 1 2 3; do
    echo "为 vm${i} 分配浮动IP..."
    FLOATING_IP=$(openstack floating ip create "$EXTERNAL_NET" -f value -c floating_ip_address 2>/dev/null)
    if [ -n "$FLOATING_IP" ]; then
        openstack server add floating ip vm${i} "$FLOATING_IP"
        echo "vm${i} 浮动IP: $FLOATING_IP"
    else
        echo "vm${i}: 无法分配浮动IP，请检查网络配置"
    fi
done

echo ""
echo "========================================="
echo "  实例创建完成!"
echo "========================================="
echo ""
openstack server list
echo ""
echo "查看实例的浮动IP:"
openstack server list --long -c Name -c Networks
echo ""
echo "========================================="
