#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가설 1: 공영주차장 접근성 기반 맞춤형 정책
전체 분석 실행 스크립트
"""

import os
import sys
import subprocess
import time

def run_script(script_path, description):
    """스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 실행 완료!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ 실행 실패!")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False
    
    return True

def main():
    """메인 실행 함수"""
    print("🎯 가설 1: 공영주차장 접근성 기반 맞춤형 정책")
    print("전체 분석 실행 시작\n")
    
    start_time = time.time()
    
    # 1단계: 데이터 전처리
    if not run_script('../../../3rd../가설1_공영주차장접근성기반맞춤형정책/data/01_데이터전처리.py', '1단계: 데이터 전처리 및 정리'):
        print("❌ 데이터 전처리 실패. 분석을 중단합니다.")
        return
    
    # 2단계: 핵심 분석
    if not run_script('../../../3rd../가설1_공영주차장접근성기반맞춤형정책/analysis/02_공영주차장접근성분석.py', '2단계: 공영주차장 접근성 분석'):
        print("❌ 핵심 분석 실패. 분석을 중단합니다.")
        return
    
    # 3단계: 시각화
    if not run_script('../../../3rd../가설1_공영주차장접근성기반맞춤형정책/visualization/03_시각화.py', '3단계: 결과 시각화 및 리포트 생성'):
        print("❌ 시각화 실패. 분석을 중단합니다.")
        return
    
    # 완료 메시지
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("🎉 가설 1 분석 완료!")
    print(f"{'='*60}")
    print(f"총 실행 시간: {execution_time:.1f}초")
    print("\n📁 생성된 결과물:")
    print("data/")
    print("  ├── 정리된_주차단속데이터.csv")
    print("  ├── 정리된_공영주차장데이터.csv")
    print("  └── 거리매트릭스.csv")
    print("\nresults/")
    print("  ├── 거리별_단속패턴.csv")
    print("  ├── 거리별_시간대패턴.csv")
    print("  ├── 주차장_사각지대.csv")
    print("  ├── 맞춤형_탄력주차정책.csv")
    print("  └── 분석_리포트.md")
    print("\nvisualization/")
    print("  ├── 거리별_분포.png")
    print("  ├── 시간대별_패턴_히트맵.png")
    print("  ├── 정책_제안_분포.png")
    print("  └── 주차장_사각지대_분석.png")
    print("\n📊 주요 분석 결과:")
    print("- 공영주차장 접근성 기반 맞춤형 정책 제안")
    print("- 주차장 사각지대 지역 식별")
    print("- 거리별 맞춤형 유예시간대 제안")
    print("\n🔍 다음 단계:")
    print("- 가설 2: 유동인구 기반 시간대 최적화")
    print("- 가설 3: 통합 주차 수요 지수 개발")

if __name__ == "__main__":
    main()
