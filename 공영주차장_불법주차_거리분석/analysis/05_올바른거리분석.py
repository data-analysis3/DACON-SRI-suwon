#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가설 1: 공영주차장 접근성 기반 맞춤형 정책
올바른 거리 분석 (최단 거리 기준)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Pretendard 폰트 설정
plt.rcParams['font.family'] = 'Pretendard'
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """데이터 로드"""
    print("올바른 거리 분석을 위한 데이터 로딩 중...")
    
    # 거리 매트릭스 데이터 로드
    distance_df = pd.read_csv('data/거리매트릭스.csv', encoding='utf-8-sig')
    
    # 주차단속 데이터 로드
    violations_df = pd.read_csv('data/정리된_주차단속데이터.csv', encoding='utf-8-sig')
    
    print(f"원본 거리 매트릭스: {len(distance_df):,}건")
    print(f"주차단속 데이터: {len(violations_df):,}건")
    
    return distance_df, violations_df

def calculate_minimum_distances(distance_df):
    """각 단속장소에서 가장 가까운 공영주차장까지의 거리 계산"""
    print("\n=== 📏 최단 거리 계산 ===")
    
    # 각 단속장소별로 가장 가까운 공영주차장 찾기
    min_distances = distance_df.groupby('단속장소').agg({
        '거리_km': 'min',
        '공영주차장': lambda x: x.iloc[x.index.get_loc(x.index[x == x.min()][0])] if len(x) > 0 else None
    }).reset_index()
    
    min_distances.columns = ['단속장소', '최단거리_km', '가장가까운공영주차장']
    
    print(f"고유 단속장소 수: {len(min_distances):,}개")
    print(f"평균 최단 거리: {min_distances['최단거리_km'].mean():.2f}km")
    print(f"중간값 최단 거리: {min_distances['최단거리_km'].median():.2f}km")
    print(f"최대 최단 거리: {min_distances['최단거리_km'].max():.2f}km")
    print(f"최소 최단 거리: {min_distances['최단거리_km'].min():.2f}km")
    
    return min_distances

def analyze_distance_patterns(min_distances):
    """거리 패턴 분석"""
    print("\n=== 📊 거리 패턴 분석 ===")
    
    # 거리 구간별 분석
    min_distances['거리구간'] = pd.cut(min_distances['최단거리_km'], 
                                   bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                   labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    distance_analysis = min_distances.groupby('거리구간').agg({
        '최단거리_km': ['count', 'mean', 'std'],
        '단속장소': 'count'
    }).round(2)
    
    print("\n거리 구간별 분석:")
    print(distance_analysis)
    
    # 사각지대 분석 (2km 이상)
    desert_threshold = 2.0
    parking_deserts = min_distances[min_distances['최단거리_km'] >= desert_threshold]
    
    print(f"\n사각지대 현황 (2km 이상):")
    print(f"사각지대 단속장소: {len(parking_deserts):,}개")
    print(f"전체 대비 비율: {len(parking_deserts)/len(min_distances)*100:.1f}%")
    
    return distance_analysis, parking_deserts

def analyze_violations_by_distance(min_distances, violations_df):
    """거리별 단속 건수 분석"""
    print("\n=== 🔥 거리별 단속 건수 분석 ===")
    
    # 단속장소별 단속 건수 계산
    violation_counts = violations_df['단속장소'].value_counts().reset_index()
    violation_counts.columns = ['단속장소', '단속건수']
    
    # 거리 데이터와 병합
    distance_violations = min_distances.merge(violation_counts, on='단속장소', how='left')
    
    # 거리 구간별 단속 건수 분석
    distance_violations['거리구간'] = pd.cut(distance_violations['최단거리_km'], 
                                         bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                         labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    distance_violation_analysis = distance_violations.groupby('거리구간').agg({
        '단속건수': ['sum', 'mean', 'max'],
        '단속장소': 'count'
    }).round(2)
    
    print("\n거리 구간별 단속 건수 분석:")
    print(distance_violation_analysis)
    
    # 거리와 단속 빈도의 상관관계
    correlation = distance_violations['최단거리_km'].corr(distance_violations['단속건수'])
    print(f"\n거리와 단속 빈도의 상관관계: {correlation:.3f}")
    
    if correlation > 0.1:
        print("→ 거리가 멀수록 단속 빈도가 높음 (공영주차장 접근성 문제)")
    elif correlation < -0.1:
        print("→ 거리가 가까울수록 단속 빈도가 높음 (핫스팟 지역)")
    else:
        print("→ 거리와 단속 빈도 간 상관관계가 약함")
    
    return distance_violations, distance_violation_analysis

def create_corrected_policy(min_distances, distance_violations):
    """올바른 거리 기반 정책 제안"""
    print("\n=== 🎯 올바른 거리 기반 정책 제안 ===")
    
    # 거리 구간별 통계
    distance_violations['거리구간'] = pd.cut(distance_violations['최단거리_km'], 
                                         bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                         labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    distance_stats = distance_violations.groupby('거리구간').agg({
        '단속건수': 'sum',
        '최단거리_km': 'mean',
        '단속장소': 'count'
    }).round(2)
    
    # 정책 매트릭스
    policy_matrix = {
        '0.5km이내': {'유예시간': '30분', '정책근거': '공영주차장 근접, 대안 주차 가능'},
        '0.5-1km': {'유예시간': '45분', '정책근거': '보행 가능 거리, 제한적 주차 허용'},
        '1-2km': {'유예시간': '1시간', '정책근거': '보행 가능하나 불편, 적당한 유예'},
        '2-3km': {'유예시간': '1.5시간', '정책근거': '보행 어려움, 충분한 유예 필요'},
        '3-5km': {'유예시간': '2시간', '정책근거': '보행 매우 어려움, 확대 유예 필요'},
        '5km이상': {'유예시간': '2.5시간', '정책근거': '공영주차장 접근 어려움, 최대 유예'}
    }
    
    print("\n올바른 거리별 맞춤형 정책 매트릭스:")
    print("=" * 100)
    print(f"{'거리구간':<12} {'단속건수':<12} {'평균거리':<10} {'단속장소':<10} {'유예시간':<10} {'정책근거':<30}")
    print("=" * 100)
    
    for distance_range in distance_stats.index:
        violations = distance_stats.loc[distance_range, '단속건수']
        mean_dist = distance_stats.loc[distance_range, '최단거리_km']
        locations = distance_stats.loc[distance_range, '단속장소']
        policy = policy_matrix[distance_range]
        
        print(f"{distance_range:<12} {violations:<12,.0f} {mean_dist:<10.2f} {locations:<10.0f} {policy['유예시간']:<10} {policy['정책근거']:<30}")
    
    print("=" * 100)
    
    return distance_stats, policy_matrix

def create_corrected_visualizations(min_distances, distance_violations):
    """올바른 시각화 생성"""
    print("\n=== 📈 올바른 시각화 생성 ===")
    
    plt.figure(figsize=(15, 10))
    
    # 1. 최단 거리 분포 히스토그램
    plt.subplot(2, 3, 1)
    plt.hist(min_distances['최단거리_km'], bins=30, color='#4A90E2', alpha=0.7, edgecolor='#2E5BBA', linewidth=1)
    plt.title('최단 거리 분포', fontsize=14, fontweight='bold')
    plt.xlabel('최단 거리 (km)', fontsize=12)
    plt.ylabel('단속장소 수', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # 2. 거리 구간별 단속장소 수
    plt.subplot(2, 3, 2)
    distance_violations['거리구간'] = pd.cut(distance_violations['최단거리_km'], 
                                         bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                         labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    location_counts = distance_violations.groupby('거리구간').size()
    location_counts.plot(kind='bar', color='#FF6B6B', edgecolor='darkred', linewidth=1.5)
    plt.title('거리 구간별 단속장소 수', fontsize=14, fontweight='bold')
    plt.xlabel('거리 구간', fontsize=12)
    plt.ylabel('단속장소 수', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 3. 거리 구간별 단속 건수
    plt.subplot(2, 3, 3)
    violation_counts = distance_violations.groupby('거리구간')['단속건수'].sum()
    violation_counts.plot(kind='bar', color='#4ECDC4', edgecolor='darkgreen', linewidth=1.5)
    plt.title('거리 구간별 단속 건수', fontsize=14, fontweight='bold')
    plt.xlabel('거리 구간', fontsize=12)
    plt.ylabel('단속 건수', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 4. 거리와 단속 빈도의 관계
    plt.subplot(2, 3, 4)
    plt.scatter(distance_violations['최단거리_km'], distance_violations['단속건수'], 
                alpha=0.6, color='#FFEAA7', edgecolors='#DDA0DD', s=20)
    plt.title('거리와 단속 빈도의 관계', fontsize=14, fontweight='bold')
    plt.xlabel('최단 거리 (km)', fontsize=12)
    plt.ylabel('단속 건수', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # 5. 거리별 누적 분포
    plt.subplot(2, 3, 5)
    sorted_distances = np.sort(min_distances['최단거리_km'])
    cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances)
    plt.plot(sorted_distances, cumulative, color='#96CEB4', linewidth=2)
    plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50%')
    plt.axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='80%')
    plt.title('거리별 누적 분포', fontsize=14, fontweight='bold')
    plt.xlabel('최단 거리 (km)', fontsize=12)
    plt.ylabel('누적 비율', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 6. 사각지대 분석
    plt.subplot(2, 3, 6)
    desert_threshold = 2.0
    parking_deserts = min_distances[min_distances['최단거리_km'] >= desert_threshold]
    plt.hist(parking_deserts['최단거리_km'], bins=20, color='#FFEAA7', alpha=0.7, edgecolor='#DDA0DD', linewidth=1)
    plt.axvline(x=2.0, color='red', linestyle='--', label='사각지대 기준 (2km)')
    plt.title('사각지대 거리 분포', fontsize=14, fontweight='bold')
    plt.xlabel('최단 거리 (km)', fontsize=12)
    plt.ylabel('단속장소 수', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('visualization/올바른_거리분석.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()

def generate_corrected_report(min_distances, distance_violations, distance_stats, policy_matrix):
    """올바른 종합 리포트 생성"""
    print("\n=== 📋 올바른 거리 분석 종합 리포트 ===")
    
    # 1. 핵심 통계 요약
    print("\n1️⃣ 핵심 통계 요약")
    print("=" * 60)
    print(f"총 단속장소 수: {len(min_distances):,}개")
    print(f"평균 최단 거리: {min_distances['최단거리_km'].mean():.2f}km")
    print(f"중간값 최단 거리: {min_distances['최단거리_km'].median():.2f}km")
    print(f"사각지대 비율: {len(min_distances[min_distances['최단거리_km'] >= 2.0])/len(min_distances)*100:.1f}%")
    
    # 2. 거리별 정책 효과 예측
    print("\n2️⃣ 거리별 정책 효과 예측")
    print("=" * 60)
    print(f"{'거리구간':<12} {'단속장소':<10} {'단속건수':<12} {'유예시간':<10} {'예상감소율':<12}")
    print("-" * 60)
    
    total_violations = distance_violations['단속건수'].sum()
    weighted_reduction = 0
    
    for distance_range in distance_stats.index:
        locations = distance_stats.loc[distance_range, '단속장소']
        violations = distance_stats.loc[distance_range, '단속건수']
        policy = policy_matrix[distance_range]
        
        # 거리에 따른 감소율 예측
        if distance_range == '0.5km이내':
            reduction = 0.1
        elif distance_range == '0.5-1km':
            reduction = 0.15
        elif distance_range == '1-2km':
            reduction = 0.2
        elif distance_range == '2-3km':
            reduction = 0.25
        elif distance_range == '3-5km':
            reduction = 0.3
        else:  # 5km이상
            reduction = 0.35
        
        weight = violations / total_violations
        weighted_reduction += weight * reduction
        
        print(f"{distance_range:<12} {locations:<10.0f} {violations:<12,.0f} {policy['유예시간']:<10} {reduction*100:<11.0f}%")
    
    # 3. 종합 효과 예측
    print("\n3️⃣ 종합 효과 예측")
    print("=" * 60)
    print(f"전체 단속 건수: {total_violations:,}건")
    print(f"가중 평균 감소율: {weighted_reduction*100:.1f}%")
    print(f"예상 감소 건수: {total_violations * weighted_reduction:,.0f}건")
    print(f"예상 절약 비용: {total_violations * weighted_reduction * 10000:,.0f}원 (단속비용 1만원 기준)")
    
    # 4. 정책 우선순위
    print("\n4️⃣ 정책 우선순위")
    print("=" * 60)
    
    # 단속 건수 기준으로 정렬
    sorted_stats = distance_stats.sort_values('단속건수', ascending=False)
    
    for i, (distance_range, row) in enumerate(sorted_stats.iterrows(), 1):
        violations = row['단속건수']
        policy = policy_matrix[distance_range]
        
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}위"
        
        print(f"{medal} {distance_range}")
        print(f"   - 단속장소: {row['단속장소']:.0f}개")
        print(f"   - 단속 건수: {violations:,.0f}건")
        print(f"   - 유예시간: {policy['유예시간']}")
        print()

def main():
    """메인 실행 함수"""
    print("=== 가설 1: 공영주차장 접근성 기반 맞춤형 정책 ===")
    print("올바른 거리 분석 시작\n")
    
    # 데이터 로드
    distance_df, violations_df = load_data()
    
    # 최단 거리 계산
    min_distances = calculate_minimum_distances(distance_df)
    
    # 거리 패턴 분석
    distance_analysis, parking_deserts = analyze_distance_patterns(min_distances)
    
    # 거리별 단속 건수 분석
    distance_violations, distance_violation_analysis = analyze_violations_by_distance(min_distances, violations_df)
    
    # 올바른 정책 제안
    distance_stats, policy_matrix = create_corrected_policy(min_distances, distance_violations)
    
    # 올바른 시각화 생성
    create_corrected_visualizations(min_distances, distance_violations)
    
    # 올바른 종합 리포트 생성
    generate_corrected_report(min_distances, distance_violations, distance_stats, policy_matrix)
    
    print("\n=== ✅ 올바른 거리 분석 완료 ===")
    print("생성된 파일:")
    print("- 올바른_거리분석.png")

if __name__ == "__main__":
    main()
