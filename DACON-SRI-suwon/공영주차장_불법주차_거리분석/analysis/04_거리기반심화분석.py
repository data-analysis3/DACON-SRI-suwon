#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가설 1: 공영주차장 접근성 기반 맞춤형 정책
거리 기반 심화 분석
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
    print("거리 기반 심화 분석을 위한 데이터 로딩 중...")
    
    # 거리 매트릭스 데이터 로드
    distance_df = pd.read_csv('data/거리매트릭스.csv', encoding='utf-8-sig')
    
    # 주차단속 데이터 로드
    violations_df = pd.read_csv('data/정리된_주차단속데이터.csv', encoding='utf-8-sig')
    
    # 공영주차장 위경도 데이터 로드
    parking_coords = pd.read_csv('data/공영주차장_위경도.csv', encoding='utf-8-sig')
    
    print(f"거리 매트릭스: {len(distance_df):,}건")
    print(f"주차단속 데이터: {len(violations_df):,}건")
    print(f"공영주차장 위경도: {len(parking_coords):,}건")
    
    return distance_df, violations_df, parking_coords

def analyze_distance_patterns(distance_df):
    """거리 패턴 심화 분석"""
    print("\n=== 📊 거리 패턴 심화 분석 ===")
    
    # 1. 거리 통계
    distance_stats = distance_df['거리_km'].describe()
    print("\n1️⃣ 거리 통계:")
    print(f"   평균 거리: {distance_stats['mean']:.2f}km")
    print(f"   중간값 거리: {distance_stats['50%']:.2f}km")
    print(f"   표준편차: {distance_stats['std']:.2f}km")
    print(f"   최대 거리: {distance_stats['max']:.2f}km")
    print(f"   최소 거리: {distance_stats['min']:.2f}km")
    
    # 2. 거리 구간별 상세 분석
    print("\n2️⃣ 거리 구간별 상세 분석:")
    distance_df['거리구간'] = pd.cut(distance_df['거리_km'], 
                                  bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                  labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    distance_analysis = distance_df.groupby('거리구간').agg({
        '거리_km': ['count', 'mean', 'std'],
        '단속장소': 'nunique'
    }).round(2)
    
    print(distance_analysis)
    
    # 3. 공영주차장별 접근성 분석
    print("\n3️⃣ 공영주차장별 접근성 분석:")
    parking_analysis = distance_df.groupby('공영주차장').agg({
        '거리_km': ['count', 'mean', 'min', 'max'],
        '단속장소': 'nunique'
    }).round(2)
    
    # 상위 10개 공영주차장 (단속 건수 기준)
    top_parking = parking_analysis[('거리_km', 'count')].sort_values(ascending=False).head(10)
    print("상위 10개 공영주차장 (단속 건수):")
    for parking, count in top_parking.items():
        mean_dist = parking_analysis.loc[parking, ('거리_km', 'mean')]
        unique_locations = parking_analysis.loc[parking, ('단속장소', 'nunique')]
        print(f"   {parking}: {count:,}건 (평균거리: {mean_dist:.2f}km, 단속장소: {unique_locations}개)")
    
    return distance_analysis, parking_analysis

def analyze_hotspots_by_distance(distance_df, violations_df):
    """거리별 핫스팟 분석"""
    print("\n=== 🔥 거리별 핫스팟 분석 ===")
    
    # 단속장소별 단속 건수 계산
    violation_counts = violations_df['단속장소'].value_counts().reset_index()
    violation_counts.columns = ['단속장소', '단속건수']
    
    # 거리 데이터와 병합
    distance_violations = distance_df.merge(violation_counts, on='단속장소', how='left')
    
    # 거리 구간별 핫스팟 분석
    print("\n1️⃣ 거리 구간별 핫스팟:")
    distance_df['거리구간'] = pd.cut(distance_df['거리_km'], 
                                  bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                  labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    hotspot_analysis = distance_violations.groupby('거리구간').agg({
        '단속건수': ['mean', 'max', 'sum'],
        '단속장소': 'nunique'
    }).round(2)
    
    print(hotspot_analysis)
    
    # 2. 거리별 단속 빈도 상관관계
    print("\n2️⃣ 거리와 단속 빈도의 상관관계:")
    correlation = distance_violations['거리_km'].corr(distance_violations['단속건수'])
    print(f"   상관계수: {correlation:.3f}")
    
    if correlation > 0.1:
        print("   → 거리가 멀수록 단속 빈도가 높음 (공영주차장 접근성 문제)")
    elif correlation < -0.1:
        print("   → 거리가 가까울수록 단속 빈도가 높음 (핫스팟 지역)")
    else:
        print("   → 거리와 단속 빈도 간 상관관계가 약함")
    
    return distance_violations, hotspot_analysis

def analyze_parking_deserts(distance_df, parking_coords):
    """주차장 사각지대 분석"""
    print("\n=== 🏜️ 주차장 사각지대 분석 ===")
    
    # 1. 사각지대 정의 (2km 이상)
    desert_threshold = 2.0
    parking_deserts = distance_df[distance_df['거리_km'] >= desert_threshold]
    
    print(f"\n1️⃣ 주차장 사각지대 현황 (2km 이상):")
    print(f"   사각지대 단속 건수: {len(parking_deserts):,}건")
    print(f"   전체 대비 비율: {len(parking_deserts)/len(distance_df)*100:.1f}%")
    
    # 2. 사각지대 거리 분포
    desert_stats = parking_deserts['거리_km'].describe()
    print(f"\n2️⃣ 사각지대 거리 통계:")
    print(f"   평균 거리: {desert_stats['mean']:.2f}km")
    print(f"   중간값 거리: {desert_stats['50%']:.2f}km")
    print(f"   최대 거리: {desert_stats['max']:.2f}km")
    
    # 3. 사각지대 지역별 분포
    print(f"\n3️⃣ 사각지대 지역별 분포:")
    desert_locations = parking_deserts['단속장소'].nunique()
    total_locations = distance_df['단속장소'].nunique()
    print(f"   사각지대 단속장소: {desert_locations:,}개")
    print(f"   전체 단속장소: {total_locations:,}개")
    print(f"   사각지대 비율: {desert_locations/total_locations*100:.1f}%")
    
    return parking_deserts

def create_distance_based_policy(distance_df, violations_df):
    """거리 기반 정책 제안"""
    print("\n=== 🎯 거리 기반 정책 제안 ===")
    
    # 거리 구간별 정책 매트릭스
    distance_policy = {
        '0.5km이내': {
            '유예시간': '30분',
            '정책근거': '공영주차장 근접, 대안 주차 가능',
            '예상효과': '최소한의 주차 편의성 제공',
            '적용대상': '공영주차장 인근 지역'
        },
        '0.5-1km': {
            '유예시간': '45분',
            '정책근거': '보행 가능 거리, 제한적 주차 허용',
            '예상효과': '보행 거리 내 주차 편의성',
            '적용대상': '보행 가능 지역'
        },
        '1-2km': {
            '유예시간': '1시간',
            '정책근거': '보행 가능하나 불편, 적당한 유예',
            '예상효과': '적당한 주차 편의성 제공',
            '적용대상': '보행 가능 지역'
        },
        '2-3km': {
            '유예시간': '1.5시간',
            '정책근거': '보행 어려움, 충분한 유예 필요',
            '예상효과': '충분한 주차 편의성 제공',
            '적용대상': '보행 어려운 지역'
        },
        '3-5km': {
            '유예시간': '2시간',
            '정책근거': '보행 매우 어려움, 확대 유예 필요',
            '예상효과': '대폭적인 주차 편의성 제공',
            '적용대상': '보행 매우 어려운 지역'
        },
        '5km이상': {
            '유예시간': '2.5시간',
            '정책근거': '공영주차장 접근 어려움, 최대 유예',
            '예상효과': '최대한의 주차 편의성 제공',
            '적용대상': '사각지대 지역'
        }
    }
    
    # 거리 구간별 통계
    distance_df['거리구간'] = pd.cut(distance_df['거리_km'], 
                                  bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                  labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    
    distance_stats = distance_df.groupby('거리구간').agg({
        '거리_km': ['count', 'mean'],
        '단속장소': 'nunique'
    }).round(2)
    
    print("\n1️⃣ 거리별 맞춤형 정책 매트릭스:")
    print("=" * 100)
    print(f"{'거리구간':<12} {'단속건수':<10} {'평균거리':<10} {'단속장소':<10} {'유예시간':<10} {'정책근거':<30}")
    print("=" * 100)
    
    for distance_range in distance_stats.index:
        count = distance_stats.loc[distance_range, ('거리_km', 'count')]
        mean_dist = distance_stats.loc[distance_range, ('거리_km', 'mean')]
        locations = distance_stats.loc[distance_range, ('단속장소', 'nunique')]
        policy = distance_policy[distance_range]
        
        print(f"{distance_range:<12} {count:<10,.0f} {mean_dist:<10.2f} {locations:<10.0f} {policy['유예시간']:<10} {policy['정책근거']:<30}")
    
    print("=" * 100)
    
    return distance_policy, distance_stats

def create_enhanced_visualizations(distance_df, distance_violations, parking_deserts):
    """향상된 시각화 생성"""
    print("\n=== 📈 향상된 시각화 생성 ===")
    
    # 1. 거리별 단속 빈도 산점도
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 3, 1)
    plt.scatter(distance_violations['거리_km'], distance_violations['단속건수'], 
                alpha=0.6, color='#4A90E2', s=20)
    plt.title('거리와 단속 빈도의 관계', fontsize=14, fontweight='bold')
    plt.xlabel('거리 (km)', fontsize=12)
    plt.ylabel('단속 건수', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # 2. 거리 구간별 단속 건수 분포
    plt.subplot(2, 3, 2)
    distance_df['거리구간'] = pd.cut(distance_df['거리_km'], 
                                  bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                  labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    distance_counts = distance_df.groupby('거리구간').size()
    distance_counts.plot(kind='bar', color='#FF6B6B', edgecolor='darkred', linewidth=1.5)
    plt.title('거리 구간별 단속 건수', fontsize=14, fontweight='bold')
    plt.xlabel('거리 구간', fontsize=12)
    plt.ylabel('단속 건수', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 3. 거리별 평균 단속 빈도
    plt.subplot(2, 3, 3)
    distance_violations['거리구간'] = pd.cut(distance_violations['거리_km'], 
                                         bins=[0, 0.5, 1, 2, 3, 5, 10], 
                                         labels=['0.5km이내', '0.5-1km', '1-2km', '2-3km', '3-5km', '5km이상'])
    avg_violations = distance_violations.groupby('거리구간')['단속건수'].mean()
    avg_violations.plot(kind='bar', color='#4ECDC4', edgecolor='darkgreen', linewidth=1.5)
    plt.title('거리 구간별 평균 단속 빈도', fontsize=14, fontweight='bold')
    plt.xlabel('거리 구간', fontsize=12)
    plt.ylabel('평균 단속 건수', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # 4. 사각지대 분포
    plt.subplot(2, 3, 4)
    plt.hist(parking_deserts['거리_km'], bins=20, color='#FFEAA7', alpha=0.7, edgecolor='#DDA0DD', linewidth=1)
    plt.axvline(x=2.0, color='red', linestyle='--', label='사각지대 기준 (2km)')
    plt.title('주차장 사각지대 거리 분포', fontsize=14, fontweight='bold')
    plt.xlabel('거리 (km)', fontsize=12)
    plt.ylabel('빈도', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 5. 거리별 누적 분포
    plt.subplot(2, 3, 5)
    sorted_distances = np.sort(distance_df['거리_km'])
    cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances)
    plt.plot(sorted_distances, cumulative, color='#96CEB4', linewidth=2)
    plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50%')
    plt.axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='80%')
    plt.title('거리별 누적 분포', fontsize=14, fontweight='bold')
    plt.xlabel('거리 (km)', fontsize=12)
    plt.ylabel('누적 비율', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 6. 거리 구간별 정책 효과 예측
    plt.subplot(2, 3, 6)
    distance_policy_effect = {
        '0.5km이내': 0.1,    # 10% 감소
        '0.5-1km': 0.15,     # 15% 감소
        '1-2km': 0.2,        # 20% 감소
        '2-3km': 0.25,       # 25% 감소
        '3-5km': 0.3,        # 30% 감소
        '5km이상': 0.35      # 35% 감소
    }
    
    effect_values = [distance_policy_effect.get(x, 0) for x in distance_counts.index]
    plt.bar(range(len(effect_values)), effect_values, color='#FF9999', edgecolor='darkred', linewidth=1.5)
    plt.title('거리별 정책 효과 예측', fontsize=14, fontweight='bold')
    plt.xlabel('거리 구간', fontsize=12)
    plt.ylabel('단속 감소율 예측', fontsize=12)
    plt.xticks(range(len(effect_values)), distance_counts.index, rotation=45, fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('visualization/거리_기반_심화분석.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()

def generate_comprehensive_report(distance_analysis, parking_analysis, hotspot_analysis, 
                                parking_deserts, distance_policy, distance_stats):
    """종합 리포트 생성"""
    print("\n=== 📋 거리 기반 심화 분석 종합 리포트 ===")
    
    # 1. 핵심 통계 요약
    print("\n1️⃣ 핵심 통계 요약")
    print("=" * 60)
    print(f"총 분석 건수: {len(distance_analysis):,}건")
    print(f"평균 접근 거리: {distance_analysis['거리_km']['mean'].mean():.2f}km")
    print(f"사각지대 비율: {len(parking_deserts)/len(distance_analysis)*100:.1f}%")
    print(f"공영주차장 수: {len(parking_analysis)}개")
    
    # 2. 거리별 정책 효과 예측
    print("\n2️⃣ 거리별 정책 효과 예측")
    print("=" * 60)
    print(f"{'거리구간':<12} {'단속건수':<10} {'유예시간':<10} {'예상감소율':<12} {'적용대상':<20}")
    print("-" * 60)
    
    for distance_range in distance_stats.index:
        count = distance_stats.loc[distance_range, ('거리_km', 'count')]
        policy = distance_policy[distance_range]
        
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
        
        print(f"{distance_range:<12} {count:<10,.0f} {policy['유예시간']:<10} {reduction*100:<11.0f}% {policy['적용대상']:<20}")
    
    # 3. 정책 우선순위
    print("\n3️⃣ 정책 우선순위")
    print("=" * 60)
    print("🥇 1순위: 5km 이상 지역 (사각지대)")
    print("   - 단속 건수: {:,}건".format(distance_stats.loc['5km이상', ('거리_km', 'count')]))
    print("   - 유예시간: 2.5시간")
    print("   - 예상 효과: 35% 단속 감소")
    print()
    print("🥈 2순위: 3-5km 지역")
    print("   - 단속 건수: {:,}건".format(distance_stats.loc['3-5km', ('거리_km', 'count')]))
    print("   - 유예시간: 2시간")
    print("   - 예상 효과: 30% 단속 감소")
    print()
    print("🥉 3순위: 2-3km 지역")
    print("   - 단속 건수: {:,}건".format(distance_stats.loc['2-3km', ('거리_km', 'count')]))
    print("   - 유예시간: 1.5시간")
    print("   - 예상 효과: 25% 단속 감소")
    
    # 4. 종합 효과 예측
    print("\n4️⃣ 종합 효과 예측")
    print("=" * 60)
    total_violations = distance_stats[('거리_km', 'count')].sum()
    weighted_reduction = 0
    
    for distance_range in distance_stats.index:
        count = distance_stats.loc[distance_range, ('거리_km', 'count')]
        weight = count / total_violations
        
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
        
        weighted_reduction += weight * reduction
    
    print(f"전체 단속 건수: {total_violations:,}건")
    print(f"가중 평균 감소율: {weighted_reduction*100:.1f}%")
    print(f"예상 감소 건수: {total_violations * weighted_reduction:,.0f}건")
    print(f"예상 절약 비용: {total_violations * weighted_reduction * 10000:,.0f}원 (단속비용 1만원 기준)")

def main():
    """메인 실행 함수"""
    print("=== 가설 1: 공영주차장 접근성 기반 맞춤형 정책 ===")
    print("거리 기반 심화 분석 시작\n")
    
    # 데이터 로드
    distance_df, violations_df, parking_coords = load_data()
    
    # 거리 패턴 분석
    distance_analysis, parking_analysis = analyze_distance_patterns(distance_df)
    
    # 핫스팟 분석
    distance_violations, hotspot_analysis = analyze_hotspots_by_distance(distance_df, violations_df)
    
    # 사각지대 분석
    parking_deserts = analyze_parking_deserts(distance_df, parking_coords)
    
    # 거리 기반 정책 제안
    distance_policy, distance_stats = create_distance_based_policy(distance_df, violations_df)
    
    # 향상된 시각화 생성
    create_enhanced_visualizations(distance_df, distance_violations, parking_deserts)
    
    # 종합 리포트 생성
    generate_comprehensive_report(distance_analysis, parking_analysis, hotspot_analysis, 
                                parking_deserts, distance_policy, distance_stats)
    
    print("\n=== ✅ 거리 기반 심화 분석 완료 ===")
    print("생성된 파일:")
    print("- 거리_기반_심화분석.png")

if __name__ == "__main__":
    main()
