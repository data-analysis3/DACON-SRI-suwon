// 카카오맵 초기화
const map = new kakao.maps.Map(document.getElementById('map'), {
    center: new kakao.maps.LatLng(37.2636, 127.0286),
    level: 5
  });
  
  let violationCircles = [];
  let facilityCircles = [];
  
  // 색상 매핑
  const typeColors = {
    "고정형": "#666",
    "주행형": "#0080FF",
    "국민신문고": "#FFA500",
    "보행": "#33CC33",
    "주민신고제": "#FF4444"
  };
  
  const categoryColors = {
    "음식점": "red",
    "카페": "orange",
    "병원": "blue",
    "은행": "green",
    "관공서": "purple",
    "주차장": "black"
  };
  
  // 필터 요소 연결
  const typeFilter = document.getElementById('typeFilter');
  const hourSlider = document.getElementById('hourSlider');
  const hourLabel = document.getElementById('hourLabel');
  const categoryFilter = document.getElementById('categoryFilter');
  
  console.log('지도 초기화 완료');
  
  // 데이터 로드
  Promise.all([
    fetch("data/violations.json").then(r => {
      console.log('violations.json 응답:', r.status);
      return r.json();
    }).catch(e => {
      console.error('violations.json 로딩 오류:', e);
      return [];
    }),
    fetch("data/facilities.json").then(r => {
      console.log('facilities.json 응답:', r.status);
      return r.json();
    }).catch(e => {
      console.error('facilities.json 로딩 오류:', e);
      return [];
    })
  ]).then(([violations, facilities]) => {
    console.log('데이터 로딩 완료:', { violations: violations.length, facilities: facilities.length });
    console.log('facilities 샘플:', facilities[0]);
    
    // 렌더 함수 등록
    render(violations, facilities);
  
    // 필터 변경 감지
    typeFilter.addEventListener("change", () => {
      console.log('단속방법 필터 변경');
      render(violations, facilities);
    });
    categoryFilter.addEventListener("change", () => {
      console.log('상권 필터 변경');
      render(violations, facilities);
    });
    hourSlider.addEventListener("input", () => {
      hourLabel.textContent = `${hourSlider.value}시`;
      console.log('시간대 변경:', hourSlider.value);
      render(violations, facilities);
    });
  });
  
  function render(violations, facilities) {
    console.log('렌더링 시작');
    const selectedTypes = Array.from(typeFilter.selectedOptions).map(o => o.value);
    const selectedCats = Array.from(categoryFilter.selectedOptions).map(o => o.value);
    const hour = parseInt(hourSlider.value);
    
    console.log('선택된 필터:', { selectedTypes, selectedCats, hour });
  
    // 이전 마커 제거
    violationCircles.forEach(c => c.setMap(null));
    facilityCircles.forEach(c => c.setMap(null));
    violationCircles = [];
    facilityCircles = [];
  
    // 단속 시각화
    if (violations && violations.length > 0) {
      violations.forEach(d => {
        if (!selectedTypes.includes(d.type)) return;
        if (parseInt(d.hour) !== hour) return;
  
        const intensity = Math.min(1, d.count / 10);  // count 기준 색조절
        const color = typeColors[d.type] || "#999";
        const circle = new kakao.maps.Circle({
          center: new kakao.maps.LatLng(d.lat, d.lon),
          radius: 20 + d.count * 2,
          strokeWeight: 0,
          fillColor: color,
          fillOpacity: 0.3 + intensity * 0.6,
          map: map
        });
        violationCircles.push(circle);
      });
      console.log('단속 마커 생성:', violationCircles.length);
    }
  
    // 상권 시각화 - 데이터 구조에 맞게 수정
    if (facilities && facilities.length > 0) {
      facilities.forEach(d => {
        // 각 카테고리별로 개별 마커 생성
        selectedCats.forEach(category => {
          if (d[category] && d[category] > 0) {
            const color = categoryColors[category] || "gray";
            const circle = new kakao.maps.Circle({
              center: new kakao.maps.LatLng(d.lat, d.lng),
              radius: 10 + Math.min(d[category] / 10, 20), // 개수에 따라 크기 조절
              strokeWeight: 0,
              fillColor: color,
              fillOpacity: 0.4,
              map: map
            });
            facilityCircles.push(circle);
          }
        });
      });
      console.log('상권 마커 생성:', facilityCircles.length);
    }
    
    console.log('렌더링 완료');
  }