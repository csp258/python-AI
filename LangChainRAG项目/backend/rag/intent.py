"""
Intent recognition for e-commerce Q&A.

Classifies user questions into predefined categories using regex pattern
matching. This information is used for analytics and routing decisions.
"""

import re

# Mapping from intent categories to Chinese keyword regex patterns.
# Each pattern is tested against the user's question; the first match wins.
INTENT_PATTERNS = {
    "售后维权": [r"退[货款]", r"换[货新]", r"保修", r"维修", r"碎屏", r"坏了", r"赔偿"],
    "物流配送": [r"快递", r"物流", r"发货", r"配送", r"送货", r"运费", r"包邮", r"几天到", r"什么时候到"],
    "支付与价格": [r"支付", r"付款", r"分期", r"降价", r"优惠", r"便宜", r"折扣", r"免息"],
    "商品咨询": [r"配置", r"参数", r"内存", r"处理器", r"屏幕", r"电池", r"摄像头", r"推荐"],
    "会员与账户": [r"会员", r"积分", r"账户", r"密码", r"注册", r"登录", r"等级"],
}


def classify_intent(question: str) -> str:
    """
    Classify a user question into one of the predefined e-commerce intent
    categories using regex keyword matching.

    Returns the matching category name (e.g., "售后维权"), or "通用咨询"
    if no pattern matches.
    """
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, question):
                return intent
    return "通用咨询"
