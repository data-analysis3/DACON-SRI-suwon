// 전역 상태
let map;
let violationMarkers = [];
let facilityMarkers = [];
let parkingMarkers = [];
let placesService;
let parkingEnabled = true;

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

// UI 요소
const typeFilter = () => Array.from(document.querySelectorAll('input[name="typeFilter"]')).filter(c => c.checked).map(c => c.value);
const categoryFilter = () => Array.from(document.querySelectorAll('input[name="categoryFilter"]')).filter(c => c.checked).map(c => c.value);
const hourSlider = document.getElementById('hourSlider');
const hourLabel = document.getElementById('hourLabel');
const toggleParking = document.getElementById('toggleParking');

// 드래그 가능한 컨트롤
(function enableDrag() {
    const controls = document.getElementById('controls');
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    controls.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'LABEL') return;
        isDragging = true;
        controls.classList.add('dragging');
        const rect = controls.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const x = e.clientX - dragOffset.x;
        const y = e.clientY - dragOffset.y;
        const maxX = window.innerWidth - controls.offsetWidth;
        const maxY = window.innerHeight - controls.offsetHeight;
        controls.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
        controls.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
    });
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            controls.classList.remove('dragging');
        }
    });
})();

// 카카오맵 초기화 콜백 (kakaoLoader에서 호출)
window.__initKakaoApp = function __initKakaoApp() {
    map = new kakao.maps.Map(document.getElementById('map'), {
        center: new kakao.maps.LatLng(37.2636, 127.0286),
        level: 6
    });

    placesService = new kakao.maps.services.Places(map);

    // 데이터 로드
    Promise.all([
        fetch("./data/violations.json").then(r => r.ok ? r.json() : []).catch(() => []),
        fetch("./data/facilities.json").then(r => r.ok ? r.json() : []).catch(() => [])
    ]).then(([violations, facilities]) => {
        const render = () => renderAll(violations, facilities);

        // 이벤트
        document.querySelectorAll('input[name="typeFilter"]').forEach(cb => cb.addEventListener('change', render));
        document.querySelectorAll('input[name="categoryFilter"]').forEach(cb => cb.addEventListener('change', render));
        hourSlider.addEventListener('input', () => { hourLabel.textContent = `${hourSlider.value}시`; render(); });
        toggleParking.addEventListener('change', () => { parkingEnabled = toggleParking.checked; fetchAndRenderParking(); });

        kakao.maps.event.addListener(map, 'dragend', () => fetchAndRenderParking());
        kakao.maps.event.addListener(map, 'zoom_changed', () => fetchAndRenderParking());

        render();
        fetchAndRenderParking();
    });
}

function clearMarkers(list) {
    list.forEach(m => m.setMap && m.setMap(null));
    return [];
}

function renderAll(violations, facilities) {
    violationMarkers = clearMarkers(violationMarkers);
    facilityMarkers = clearMarkers(facilityMarkers);

    const selectedTypes = typeFilter();
    const selectedCats = categoryFilter();
    const hour = parseInt(hourSlider.value);

    // 단속
    violations.forEach(d => {
        if (!selectedTypes.includes(d.type)) return;
        if (parseInt(d.hour) !== hour) return;
        const color = typeColors[d.type] || '#999';
        const circle = new kakao.maps.Circle({
            center: new kakao.maps.LatLng(d.lat, d.lon),
            radius: 100,
            strokeWeight: 1,
            strokeColor: color,
            strokeOpacity: 0.9,
            fillColor: color,
            fillOpacity: 0.25,
            map
        });
        violationMarkers.push(circle);
    });

    // 상권
    facilities.forEach(d => {
        selectedCats.forEach(category => {
            if (d[category] && d[category] > 0) {
                const color = categoryColors[category] || 'gray';
                const circle = new kakao.maps.Circle({
                    center: new kakao.maps.LatLng(d.lat, d.lng),
                    radius: 50 + Math.min(d[category] / 10, 20),
                    strokeWeight: 0,
                    fillColor: color,
                    fillOpacity: 0.4,
                    map
                });
                facilityMarkers.push(circle);
            }
        });
    });
}

function fetchAndRenderParking() {
    parkingMarkers = clearMarkers(parkingMarkers);
    if (!parkingEnabled) return;
    if (!placesService) return;

    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    // 카카오 장소검색: 키워드 "공영주차장"
    const query = '공영주차장';

    // 영역 내 페이징 처리
    let page = 1;
    const perPage = 15; // 카카오 기본 페이지 크기

    const search = () => {
        placesService.keywordSearch(query, (results, status, pagination) => {
            if (status !== kakao.maps.services.Status.OK) {
                return;
            }

            results.forEach(place => {
                const marker = new kakao.maps.Marker({
                    position: new kakao.maps.LatLng(Number(place.y), Number(place.x)),
                    map
                });
                const iw = new kakao.maps.InfoWindow({
                    content: `<div style="padding:6px 10px; font-size:12px;">${place.place_name}</div>`
                });
                kakao.maps.event.addListener(marker, 'click', () => iw.open(map, marker));
                parkingMarkers.push(marker);
            });

            if (pagination && page < pagination.last) {
                page += 1;
                pagination.gotoPage(page);
            }
        }, { bounds: new kakao.maps.LatLngBounds(sw, ne), page });
    };

    search();
}

