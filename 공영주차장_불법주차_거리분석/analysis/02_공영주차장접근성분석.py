#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가설 1: 공영주차장 접근성 기반 맞춤형 정책
공영주차장 접근성 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_cleaned_data():
    """정리된 데이터 로드"""
    print("정리된 데이터 로딩 중...")
    
    violations_df = pd.read_csv('../data/정리된_주차단속데이터.csv', encoding='utf-8-sig')
    parking_df = pd.read_csv('../data/정리된_공영주차장데이터.csv', encoding='utf-8-sig')
    distance_df = pd.read_csv('../data/거리매트릭스.csv', encoding='utf-8-sig')
    
    print(f"주차단속 데이터: {len(violations_df):,}건")
    print(f"공영주차장 데이터: {len(parking_df):,}건")
    print(f"거리매트릭스: {len(distance_df):,}건")
    
    return violations_df, parking_df, distance_df

def analyze_parking_accessibility(distance_df):
    """공영주차장 접근성 분석"""
    print("\n=== 공영주차장 접근성 분석 ===")
    
    # 거리별 분포 분석
    print("거리별 분포:")
    print(distance_df['거리_km'].describe())
    
    # 거리 구간별 분류
    distance_df['거리구간'] = pd.cut(distance_df['거리_km'], 
                                   bins=[0, 0.5, 1.0, 2.0, 5.0], 
                                   labels=['0.5km이내', '0.5~1km', '1~2km', '2km이상'])
    
    # 거리 구간별 단속 건수
    distance_distribution = distance_df['거리구간'].value_counts().sort_index()
    print("\n거리 구간별 단속 건수:")
    print(distance_distribution)
    
    return distance_df

def analyze_hotspots_by_distance(violations_df, distance_df):
    """거리별 핫스팟 분석"""
    print("\n=== 거리별 핫스팟 분석 ===")
    
    # 거리별 단속 빈도 분석
    distance_violations = distance_df.groupby('거리구간').agg({
        '거리_km': 'count',
        '주차구획수': 'mean',
        '기본요금': 'mean'
    }).rename(columns={'거리_km': '단속건수'})
    
    print("거리별 단속 패턴:")
    print(distance_violations)
    
    # 거리와 단속 빈도의 상관관계
    correlation = distance_df['거리_km'].corr(distance_df['주차구획수'])
    print(f"\n거리와 주차구획수의 상관계수: {correlation:.3f}")
    
    return distance_violations

def analyze_time_patterns_by_distance(violations_df, distance_df):
    """거리별 시간대 패턴 분석"""
    print("\n=== 거리별 시간대 패턴 분석 ===")
    
    # 거리와 시간대 결합 분석
    time_distance_analysis = violations_df.merge(
        distance_df[['단속장소', '거리구간']], 
        on='단속장소', 
        how='inner'
    )
    
    # 거리 구간별 시간대 패턴
    time_patterns = time_distance_analysis.groupby(['거리구간', 'hour']).size().unstack(fill_value=0)
    
    print("거리 구간별 시간대 패턴:")
    print(time_patterns)
    
    return time_patterns

def identify_parking_deserts(distance_df, threshold=2.0):
    """주차장 사각지대 식별"""
    print(f"\n=== 주차장 사각지대 식별 (기준: {threshold}km) ===")
    
    # 사각지대 지역 식별
    parking_deserts = distance_df[distance_df['거리_km'] >= threshold]
    
    print(f"주차장 사각지대 지역: {len(parking_deserts):,}건")
    print(f"전체 대비 비율: {len(parking_deserts)/len(distance_df)*100:.1f}%")
    
    # 사각지대 지역의 특성
    desert_stats = parking_deserts.describe()
    print("\n사각지대 지역 통계:")
    print(desert_stats)
    
    return parking_deserts

def generate_policy_recommendations(distance_df, parking_deserts):
    """정책 제안 생성"""
    print("\n=== 맞춤형 탄력주차 정책 제안 ===")
    
    # 거리별 정책 유형 분류
    policy_recommendations = []
    
    for _, row in distance_df.iterrows():
        if row['거리_km'] <= 0.5:
            policy = "제한적 유예 (1시간)"
            reason = "공영주차장 매우 가까움"
        elif row['거리_km'] <= 1.0:
            policy = "보통 유예 (1.5시간)"
            reason = "공영주차장 가까움"
        elif row['거리_km'] <= 2.0:
            policy = "확대 유예 (2시간)"
            reason = "공영주차장 보통 거리"
        else:
            policy = "특별 유예 (2.5시간)"
            reason = "주차장 사각지대"
        
        policy_recommendations.append({
            '단속장소': row['단속장소'],
            '공영주차장': row['공영주차장'],
            '거리_km': row['거리_km'],
            '거리구간': row['거리구간'],
            '권장정책': policy,
            '정책근거': reason
        })
    
    policy_df = pd.DataFrame(policy_recommendations)
    
    # 정책별 통계
    policy_stats = policy_df['권장정책'].value_counts()
    print("권장 정책별 건수:")
    print(policy_stats)
    
    return policy_df

def save_results(distance_violations, time_patterns, parking_deserts, policy_df):
    """분석 결과 저장"""
    print("\n=== 분석 결과 저장 ===")
    
    # 결과 저장
    distance_violations.to_csv('../results/거리별_단속패턴.csv', encoding='utf-8-sig')
    time_patterns.to_csv('../results/거리별_시간대패턴.csv', encoding='utf-8-sig')
    parking_deserts.to_csv('../results/주차장_사각지대.csv', encoding='utf-8-sig')
    policy_df.to_csv('../results/맞춤형_탄력주차정책.csv', encoding='utf-8-sig')
    
    print("저장된 파일:")
    print("- 거리별_단속패턴.csv")
    print("- 거리별_시간대패턴.csv")
    print("- 주차장_사각지대.csv")
    print("- 맞춤형_탄력주차정책.csv")

def main():
    """메인 실행 함수"""
    print("=== 가설 1: 공영주차장 접근성 기반 맞춤형 정책 ===")
    print("공영주차장 접근성 분석 시작\n")
    
    # 데이터 로드
    violations_df, parking_df, distance_df = load_cleaned_data()
    
    # 공영주차장 접근성 분석
    distance_df = analyze_parking_accessibility(distance_df)
    
    # 거리별 핫스팟 분석
    distance_violations = analyze_hotspots_by_distance(violations_df, distance_df)
    
    # 거리별 시간대 패턴 분석
    time_patterns = analyze_time_patterns_by_distance(violations_df, distance_df)
    
    # 주차장 사각지대 식별
    parking_deserts = identify_parking_deserts(distance_df)
    
    # 맞춤형 정책 제안
    policy_df = generate_policy_recommendations(distance_df, parking_deserts)
    
    # 결과 저장
    save_results(distance_violations, time_patterns, parking_deserts, policy_df)
    
    print("\n공영주차장 접근성 분석 완료!")

if __name__ == "__main__":
    main()
