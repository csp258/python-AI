# 导入库
import pandas as pd
import numpy as np
import os

# 自动适配文件路径（已修复路径问题）
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, "modeling_new.xlsx")
df = pd.read_excel(file_path)
df_raw = df.copy()

# 2.数据清洗（每8列为一组=1家公司）
def drop_columns(df, pro_columns):
    drop_group = set([i // 8 for i in pro_columns]) 
    del_cols = []
    for i in drop_group:
        del_cols += [df.columns[i * 8 + j] for j in range(8)]
    return df.drop(del_cols, axis=1)

# 2.1 删除含#ERROR的公司分组
error_cols_idx = []
for idx, col in enumerate(df.columns):
    if df[col].astype(str).str.contains('#ERROR', na=False).any():
        error_cols_idx.append(idx)
df = drop_columns(df, error_cols_idx)

# 2.2 删除单列缺失>15的分组
miss_over15_idx = []
miss_count = df.isna().sum(axis=0)
for idx, cnt in enumerate(miss_count):
    if cnt > 15:
        miss_over15_idx.append(idx)
df = drop_columns(df, miss_over15_idx)

# 2.3 转数值+均值填充
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df_filled = df.fillna(df.mean())

# 3.构造因子数据表
companies = df_filled.columns.tolist()[::8]
for i in range(len(companies)):
    companies[i] = companies[i][:companies[i].find(' - ')]

data_list = []
for i in range(len(companies)):
    company = companies[i]
    EV, PER, EPS, DPS, NOS, ROE, TL, TSE = (df_filled.iloc[-1, i * 8 + j] for j in range(8))
    
    EPS_T = EPS
    EPS_T_1 = df_filled.iloc[-13, i * 8 + 2]
    # PEG容错
    if EPS_T_1 == 0 or EPS_T == EPS_T_1:
        PEG = np.inf
    else:
        PEG = PER / (((EPS_T / EPS_T_1) - 1) * 100)
    # DPR、DER容错
    DPR = DPS / EPS if EPS != 0 else np.nan
    DER = TL / TSE if TSE != 0 else np.nan
    
    data_list.append({
        'company': company, 'EV': EV, 'PER': PER, 'EPS': EPS,
        'PEG': PEG,'DPR': DPR, 'ROE': ROE, 'DER': DER
    })
df_new = pd.DataFrame(data_list)

# =========关键修改：放宽选股规则=========
# 原逻辑：所有7个因子取交集，条件太严；修改：每个因子取前50%，或改成「满足过半因子入选即通过」
TOP_N = int(len(df_new)*0.5) # 从30%改成50%，扩大入选池

low_better = ['EV', 'PER', 'PEG', 'DER']
high_better = ['EPS', 'DPR', 'ROE']
stock_sets = []

for fac in low_better:
    top_stock = df_new.sort_values(by=fac, ascending=True).head(TOP_N)['company'].tolist()
    stock_sets.append(set(top_stock))
for fac in high_better:
    top_stock = df_new.sort_values(by=fac, ascending=False).head(TOP_N)['company'].tolist()
    stock_sets.append(set(top_stock))

# 方案A：保留交集（TOP_N=50%大概率出结果）；若仍为空用方案B
good_stocks = set.intersection(*stock_sets)

# 方案B备选：满足≥4个因子入选就选中（取消严格全因子交集，去掉注释启用）
'''
from collections import Counter
all_candidates = []
for s in stock_sets:
    all_candidates.extend(list(s))
cnt = Counter(all_candidates)
# 出现次数≥4（7个因子过半）入选
good_stocks = {k for k,v in cnt.items() if v >=4}
'''

# 结果输出&保存
df_goodStocks = df_new[df_new['company'].isin(good_stocks)]
df_goodStocks.to_excel('goodStocks_new.xlsx', index=False)

print(f"共筛选出优质股票数量：{len(good_stocks)}")
print("入选股票名单：")
print(df_goodStocks[['company']])