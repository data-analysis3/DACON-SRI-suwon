import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import ast

df = pd.read_csv("경기도골목상권매출_위경도(2).csv")

# 숫자 변환 + 좌표 NaN 제거
for c in ["AMT","NOC","lat","lon"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["lat","lon"]).copy()

# meta에서 address_name 추출
def extract_addr(s):
    try:
        d = ast.literal_eval(s) if isinstance(s, str) else {}
        return d.get("address_name")
    except Exception:
        return None

df["addr_name"] = df["meta"].apply(extract_addr)

# 🚩 여기서 '수원시' 포함된 행만 필터링
df = df[df["addr_name"].str.contains("수원시", na=False)].copy()

# 좌표 반올림으로 같은 지점 묶기
df["lat_r"] = df["lat"].round(5)
df["lon_r"] = df["lon"].round(5)

def make_key(row):
    return row["addr_name"] if pd.notna(row["addr_name"]) else (row["lat_r"], row["lon_r"])
df["addr_key"] = df.apply(make_key, axis=1)

# 주소 기준 집계
agg = (df.groupby("addr_key", as_index=False)
         .agg(AMT_sum=("AMT","sum"),
              AMT_mean=("AMT","mean"),
              NOC_sum=("NOC","sum"),
              NOC_mean=("NOC","mean"),
              n=("AMT","size"),
              lat=("lat","mean"),
              lon=("lon","mean"))
      )

# GeoDataFrame 변환
gdf = gpd.GeoDataFrame(
    agg,
    geometry=[Point(xy) for xy in zip(agg["lon"], agg["lat"])],
    crs="EPSG:4326"
)

# 저장 (수원시 데이터만)
gdf.to_file("sales_suwon_mean.geojson", driver="GeoJSON", encoding="utf-8")
gdf.to_file("sales_suwon_sum.geojson",  driver="GeoJSON", encoding="utf-8")
print("✅ 수원시 필터링 완료, sales_suwon_mean.geojson / sales_suwon_sum.geojson 생성")
