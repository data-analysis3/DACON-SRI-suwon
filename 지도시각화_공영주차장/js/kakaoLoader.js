(function loadKakaoSDK() {
    const showOverlay = (text, color = '#333', bg = '#fffbe6', border = '#ffd666') => {
        const box = document.createElement('div');
        box.style.position = 'absolute';
        box.style.bottom = '12px';
        box.style.right = '12px';
        box.style.background = bg;
        box.style.border = `1px solid ${border}`;
        box.style.padding = '10px 12px';
        box.style.borderRadius = '8px';
        box.style.zIndex = '2000';
        box.style.fontSize = '12px';
        box.style.color = color;
        box.textContent = text;
        document.body.appendChild(box);
        return box;
    };

    if (!window.KAKAO_APP_KEY) {
        console.error('KAKAO_APP_KEY가 config.js에 설정되어야 합니다.');
        showOverlay('config.js에 KAKAO_APP_KEY를 설정하세요.', '#a61b1b', '#ffeded', '#ffa39e');
        return;
    }

    const statusBox = showOverlay('카카오 SDK 로딩 중…');
    const src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${window.KAKAO_APP_KEY}&libraries=services&autoload=false`;
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => {
        statusBox.textContent = '카카오 SDK 로드 완료. 지도 초기화 중…';
        kakao.maps.load(() => {
            statusBox.textContent = '지도 초기화 완료';
            setTimeout(() => statusBox.remove(), 1500);
            if (typeof window.__initKakaoApp === 'function') {
                window.__initKakaoApp();
            }
        });
    };
    script.onerror = () => {
        statusBox.textContent = 'SDK 로드 실패. 네트워크 또는 키 설정 확인';
        statusBox.style.background = '#ffeded';
        statusBox.style.borderColor = '#ffa39e';
        statusBox.style.color = '#a61b1b';
    };
    document.head.appendChild(script);

    // 5초 내 kakao 객체가 없으면 도메인 허용 안내
    setTimeout(() => {
        if (!(window.kakao && window.kakao.maps)) {
            statusBox.textContent = '지도가 표시되지 않습니다. 카카오 콘솔에 http://localhost:8003 도메인 등록이 필요합니다.';
            statusBox.style.background = '#fff1f0';
            statusBox.style.borderColor = '#ffa39e';
            statusBox.style.color = '#a8071a';
        }
    }, 5000);
})();

