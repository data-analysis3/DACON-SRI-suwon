import os
import ast
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from libpysal.weights import KNN, W
from esda.getisord import G_Local

# ========= 설정 =========
INPUT_CSV = "경기도골목상권매출_위경도(2).csv"

# 주소 기반 필터가 실패할 때만 쓰는 BBOX(수원 대략 범위) — 필요시 조정
SUWON_BBOX = {"min_lon": 126.95, "max_lon": 127.10, "min_lat": 37.24, "max_lat": 37.35}

# Gi* / KNN
K_NEIGHBORS = 8
PERMUTATIONS = 999
RANDOM_SEED = 1234

# 출력 접두어
OUT_PREFIX = "suwon_hotspots"

# 개별 GeoJSON도 추가로 저장할지
SAVE_SEPARATE_GEOJSON = False
# ========================


def to_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def extract_addr(s):
    """meta 컬럼(str)에서 address_name을 안전하게 파싱."""
    try:
        d = ast.literal_eval(s) if isinstance(s, str) else {}
        return d.get("address_name")
    except Exception:
        return None


def filter_suwon_address_first(df: pd.DataFrame) -> pd.DataFrame:
    """
    1순위: meta.address_name에 '수원시' 포함 행만 필터
    실패(메타 없음/매칭 0건) 시: BBOX 폴백
    """
    addr_filtered = None
    if "meta" in df.columns:
        df["addr_name"] = df["meta"].apply(extract_addr)
        addr_filtered = df[df["addr_name"].str.contains("수원시", na=False)].copy()

    if addr_filtered is not None and len(addr_filtered) > 0:
        return addr_filtered

    # 폴백: BBOX
    print("⚠️ 주소 기반 필터 결과가 없어 BBOX로 필터합니다.")
    return df[
        (df["lon"] >= SUWON_BBOX["min_lon"]) & (df["lon"] <= SUWON_BBOX["max_lon"]) &
        (df["lat"] >= SUWON_BBOX["min_lat"]) & (df["lat"] <= SUWON_BBOX["max_lat"])
    ].copy()


def build_points_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    좌표 라운딩(소수 5자리)으로 같은 지점 묶고, 좌표별 AMT/NOC 합산.
    라운딩 좌표(lon_r, lat_r)를 대표 좌표로 사용.
    """
    # 좌표 라운딩으로 지점 스냅
    df["lat_r"] = df["lat"].round(5)
    df["lon_r"] = df["lon"].round(5)

    grouped = (df.groupby(["lat_r", "lon_r"], as_index=False)
                 .agg(AMT=("AMT", "sum"),
                      NOC=("NOC", "sum")))

    gdf = gpd.GeoDataFrame(
        grouped.rename(columns={"lat_r": "lat", "lon_r": "lon"}),
        geometry=[Point(xy) for xy in zip(grouped["lon_r"], grouped["lat_r"])],
        crs="EPSG:4326"
    )
    return gdf


def knn_bisquare_adaptive(gdf_metric_crs: gpd.GeoDataFrame, k=8, row_standardize=True) -> W:
    """
    - k-최근접 이웃 집합
    - 각 점 i의 k번째 이웃 거리 = 대역폭 h_i
    - bi-square: w_ij = (1 - (d_ij / h_i)^2)^2 (d_ij<=h_i, else 0)
    """
    w_knn = KNN.from_dataframe(gdf_metric_crs, k=k)

    xs = gdf_metric_crs.geometry.x.values
    ys = gdf_metric_crs.geometry.y.values
    coords = np.column_stack([xs, ys])

    neighbors, weights = {}, {}
    for i, ns in w_knn.neighbors.items():
        if len(ns) == 0:
            neighbors[i], weights[i] = [], []
            continue
        d = np.linalg.norm(coords[ns] - coords[i], axis=1)
        h_i = d.max() if len(d) else 0.0
        if h_i == 0.0:
            w = np.ones_like(d, dtype=float)
        else:
            w = (1 - (d / h_i) ** 2) ** 2
            w[d > h_i] = 0.0
        neighbors[i] = list(ns)
        weights[i] = list(w.astype(float))

    w_kernel = W(neighbors=neighbors, weights=weights)
    if row_standardize:
        w_kernel.transform = "R"
    return w_kernel


def run_gi(gdf_in: gpd.GeoDataFrame, value_col: str, w: W, prefix: str,
           permutations=999, seed=1234) -> gpd.GeoDataFrame:
    y = pd.to_numeric(gdf_in[value_col], errors="coerce").fillna(0)\
        .astype("float64").values
    g = G_Local(y, w, star=0.5, permutations=permutations, seed=seed)
    out = gdf_in.copy()
    out[f"{prefix}_z"] = g.Zs
    out[f"{prefix}_p"] = g.p_sim
    out[f"{prefix}_label"] = [
        "Hotspot" if (z > 0 and p <= 0.05) else
        "Coldspot" if (z < 0 and p <= 0.05) else
        "Not significant"
        for z, p in zip(g.Zs, g.p_sim)
    ]
    return out


def main():
    # 1) 로드 & 숫자화 & 좌표 결측 제거
    df = pd.read_csv(INPUT_CSV)
    df = to_numeric(df, ["AMT", "NOC", "lat", "lon"])
    df = df.dropna(subset=["lat", "lon"]).copy()
    if len(df) == 0:
        raise ValueError("위경도 유효 데이터가 없습니다.")

    # 2) 수원시 필터(주소 우선, 폴백 BBOX)
    df = filter_suwon_address_first(df)
    if len(df) == 0:
        raise ValueError("수원시 범위에서 데이터가 없습니다. meta/BBOX를 확인하세요.")

    # 3) 좌표 라운딩 → 좌표별 합산 → GeoDataFrame(WGS84)
    gdf = build_points_gdf(df)

    # 4) 거리 단위용 투영(UTM52N)
    gdf_m = gdf.to_crs(32652)

    # 5) KNN + 적응형(bi-square) 가중치
    w_adaptive = knn_bisquare_adaptive(gdf_m, k=K_NEIGHBORS, row_standardize=True)

    # 6) Gi* (AMT/NOC)
    res_amt = run_gi(gdf_m, "AMT", w_adaptive, "amt",
                     permutations=PERMUTATIONS, seed=RANDOM_SEED)
    res_noc = run_gi(gdf_m, "NOC", w_adaptive, "noc",
                     permutations=PERMUTATIONS, seed=RANDOM_SEED)

    # 7) WGS84 복귀
    res_amt = res_amt.to_crs(4326)
    res_noc = res_noc.to_crs(4326)

    # 8) CSV (Gi 스코어 포함)
    merged_df = res_amt.drop(columns=["geometry"]).merge(
        res_noc.drop(columns=["geometry"]),
        on=["lat", "lon", "AMT", "NOC"],
        suffixes=("", "_noc")
    )
    cols = ["lat", "lon", "AMT", "NOC",
            "amt_z", "amt_p", "amt_label",
            "noc_z", "noc_p", "noc_label"]
    merged_df = merged_df[cols]
    csv_path = f"{OUT_PREFIX}_gi_scores.csv"
    merged_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV 저장 완료: {csv_path}")

    # 9) 통합 GeoJSON (카카오맵 토글용)
    gdf_join = res_amt[["lat", "lon", "AMT", "NOC",
                        "amt_z", "amt_p", "amt_label", "geometry"]].copy()
    gdf_join = gdf_join.merge(
        res_noc[["lat", "lon", "noc_z", "noc_p", "noc_label"]],
        on=["lat", "lon"],
        how="left"
    )
    unified_geojson = f"{OUT_PREFIX}_gi_unified.geojson"
    gdf_join.to_file(unified_geojson, driver="GeoJSON", encoding="utf-8")
    print(f"통합 GeoJSON 저장 완료: {unified_geojson}")

    # (옵션) 개별 GeoJSON도 저장
    if SAVE_SEPARATE_GEOJSON:
        res_amt.to_file(f"{OUT_PREFIX}_amt.geojson", driver="GeoJSON", encoding="utf-8")
        res_noc.to_file(f"{OUT_PREFIX}_noc.geojson", driver="GeoJSON", encoding="utf-8")
        print("개별 GeoJSON 저장 완료.")

    print("✅ 완료! 수원시 Gi* 분석 산출물 생성됨.")


if __name__ == "__main__":
    main()
