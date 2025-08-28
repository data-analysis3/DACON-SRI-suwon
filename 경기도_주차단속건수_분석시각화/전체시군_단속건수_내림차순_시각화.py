import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import numpy as np

# 폰트 설정
plt.rcParams['font.family'] = 'Pretendard'  # Pretendard 폰트 사용
plt.rcParams['axes.unicode_minus'] = False

# API 설정
API_KEY = "5f47a78cf5d7440e98d1bc10c85580e3"
BASE_URL = "https://openapi.gg.go.kr/ParkingPlaceViolationRegulatio"

def fetch_parking_violation_data():
    """경기도 주정차 위반 단속실적 데이터를 가져오는 함수"""
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 1000
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        return None

def parse_data(data):
    """API 응답 데이터를 파싱하여 DataFrame으로 변환"""
    try:
        if 'ParkingPlaceViolationRegulatio' in data:
            items = data['ParkingPlaceViolationRegulatio'][1]['row']
        else:
            for key in data.keys():
                if 'row' in str(data[key]):
                    items = data[key][1]['row']
                    break
            else:
                print("데이터 구조를 찾을 수 없습니다.")
                return None
        
        df = pd.DataFrame(items)
        return df
        
    except Exception as e:
        print(f"데이터 파싱 오류: {e}")
        return None

def visualize_all_sigun_violations(df):
    """모든 시군 단속건수 내림차순 시각화"""
    if df is None or df.empty:
        print("분석할 데이터가 없습니다.")
        return
    
    if 'SIGUN_NM' in df.columns and 'COLLECT_CNT' in df.columns:
        # 시군별 단속건수 집계
        sigun_summary = df.groupby('SIGUN_NM')['COLLECT_CNT'].sum().reset_index()
        sigun_summary.columns = ['시군명', '총단속건수']
        
        # 내림차순 정렬
        sigun_summary = sigun_summary.sort_values('총단속건수', ascending=False).reset_index(drop=True)
        
        # 색상 설정 (수원시: #144193, 나머지: #8B9091)
        colors = []
        for sigun in sigun_summary['시군명']:
            if sigun == '수원시':
                colors.append('#144193')
            else:
                colors.append('#8B9091')
        
        # 시각화
        plt.figure(figsize=(16, 10))
        
        # 막대그래프 생성
        bars = plt.bar(sigun_summary['시군명'], sigun_summary['총단속건수'], 
                      color=colors, alpha=0.8, width=0.7)
        
        # 막대 위에 값 표시
        for i, (bar, value, sigun) in enumerate(zip(bars, sigun_summary['총단속건수'], sigun_summary['시군명'])):
            if sigun == '수원시':
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(sigun_summary['총단속건수'])*0.01,
                        f'{value:,}', ha='center', va='bottom', fontweight='bold', fontsize=10, color='#144193')
            else:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(sigun_summary['총단속건수'])*0.01,
                        f'{value:,}', ha='center', va='bottom', fontweight='bold', fontsize=8, color='#8B9091')
        
        # 축 설정
        plt.xlabel('시군명', fontsize=14, fontweight='bold')
        plt.ylabel('총단속건수', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, fontsize=10)
        plt.yticks(fontsize=12)
        
        # 그리드 설정
        plt.grid(True, axis='y', alpha=0.3)
        
        # 레이아웃 조정
        plt.tight_layout()
        
        # 파일 저장
        plt.savefig('전체시군_단속건수_내림차순.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # CSV 파일로 저장
        sigun_summary.to_csv('전체시군_단속건수_내림차순.csv', index=False, encoding='utf-8-sig')
        
        print("=== 전체 시군 단속건수 (내림차순) ===")
        print(sigun_summary)
        print(f"\n시각화가 '전체시군_단속건수_내림차순.png' 파일로 저장되었습니다.")
        print(f"데이터가 '전체시군_단속건수_내림차순.csv' 파일로 저장되었습니다.")
        
        # 수원시 순위 확인
        suwon_rank = sigun_summary[sigun_summary['시군명'] == '수원시'].index[0] + 1
        print(f"\n수원시 순위: {suwon_rank}위")
        
    else:
        print("필요한 컬럼이 데이터에 없습니다.")
        print("사용 가능한 컬럼:", df.columns.tolist())

def main():
    """메인 실행 함수"""
    print("전체 시군 단속건수 내림차순 시각화를 시작합니다...")
    
    # 1. API에서 데이터 가져오기
    print("1. API에서 데이터를 가져오는 중...")
    data = fetch_parking_violation_data()
    
    if data is None:
        print("데이터를 가져올 수 없습니다.")
        return
    
    # 2. 데이터 파싱
    print("2. 데이터를 파싱하는 중...")
    df = parse_data(data)
    
    if df is None:
        print("데이터 파싱에 실패했습니다.")
        return
    
    # 3. 전체 시군 내림차순 시각화
    print("3. 전체 시군 단속건수 내림차순 시각화를 진행하는 중...")
    visualize_all_sigun_violations(df)
    
    print("분석이 완료되었습니다!")

if __name__ == "__main__":
    main()
