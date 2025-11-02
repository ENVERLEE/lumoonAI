// 초대 코드 API 함수들

/**
 * 초대 코드 생성
 */
async function createInviteCode(expiresInDays = 30) {
    const url = API_CONFIG.INVITE_CREATE;
    const options = getFetchOptions('POST', {
        expires_in_days: expiresInDays,
    });
    
    return await apiCall(url, options);
}

/**
 * 내가 생성한 초대 코드 목록
 */
async function listInviteCodes() {
    const url = API_CONFIG.INVITE_LIST;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 초대 코드 사용
 */
async function useInviteCode(code) {
    const url = API_CONFIG.INVITE_USE;
    const options = getFetchOptions('POST', {
        code: code.toUpperCase().trim(),
    });
    
    return await apiCall(url, options);
}

/**
 * 초대 통계 조회
 */
async function getInviteStats() {
    const url = API_CONFIG.INVITE_STATS;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

