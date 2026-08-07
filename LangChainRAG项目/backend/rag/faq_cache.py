"""FAQ semantic cache for high-frequency e-commerce questions."""
import json
import hashlib
from typing import Optional, Tuple, List

FAQ_QA = {
    "退货": "您可以在订单详情中申请退货。7天内无理由退换（商品完好），15天内质量问题免费换新。退货流程：申请退货→审核→寄回→退款，审核通过后1-3个工作日退款到原支付方式。",
    "退款": "退货退款在仓库签收后1-3个工作日内到账。退款原路返回（微信/支付宝/银行卡）。如果超过3个工作日未到账，请联系客服查询。",
    "物流": "默认使用顺丰快递，全国包邮。一线城市次日达，二三线城市2-3天，偏远地区3-5天。下单后可登录账号查看订单物流详情。",
    "快递": "默认使用顺丰快递，全国包邮。一线城市次日达，二三线城市2-3天。可在「我的订单」中查看物流信息。",
    "发货": "下单后48小时内发货，顺丰快递全国包邮。发货后会短信通知快递单号。一线城市次日达。",
    "保修": "手机/平板全国联保1年，笔记本主要部件保修2年，耳机/音箱保修1年。Apple产品支持全国联保+Apple Store官方售后。人为损坏不在保修范围内。",
    "碎屏": "碎屏属于人为损坏，不在免费保修范围内。如购买了碎屏险（99元/年），可免费更换一次屏幕。自费维修价格500-3000元不等。",
    "分期": "支持花呗3/6/12期免息分期、信用卡分期、京东白条3/6/12/24期。部分爆款商品有限时免息活动。",
    "降价": "购买后7天内如发现同款商品降价，可联系客服申请退差价。差价以优惠券形式返还到您的账户。",
    "会员": "会员分为普通/银卡(年消费3000)/金卡(年消费10000)/钻石(年消费30000)。高级会员享受积分加倍、专属客服、优先发货、免费延保等权益。",
    "支付": "支持微信支付、支付宝、银联、花呗分期、京东白条、信用卡分期。部分地区支持货到付款。",
    "配送": "顺丰快递全国包邮。支持送货上门、快递柜代收、菜鸟驿站代收。贵重物品（>3000元）建议本人签收当面验货。",
    "海外": "目前只支持中国大陆及港澳台地区配送。港澳台运费另计，清关税费由买家承担。海外用户可通过转运仓下单。",
}


def _keyword_match(question: str) -> Optional[str]:
    """
    Simple keyword-in-question matching against the FAQ dictionary.
    Returns the answer text if any FAQ keyword is found in the user's question,
    or None if no keywords match.
    """
    for keyword, answer in FAQ_QA.items():
        if keyword in question:
            return answer
    return None


def try_faq(question: str) -> Optional[Tuple[str, List[dict]]]:
    """
    Attempt to answer a question from the FAQ cache to avoid expensive LLM calls
    for common e-commerce queries (returns, shipping, payments, etc.).

    Returns (answer, sources) if a cached answer exists, or None to indicate
    the question should go through the full RAG pipeline.
    """
    answer = _keyword_match(question)
    if answer:
        sources = [{"filename": "FAQ知识库", "content": answer[:200], "score": 1.0}]
        return (answer, sources)
    return None
