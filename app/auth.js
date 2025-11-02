// 인증 관련 API 함수들

/**
 * 회원가입
 */
async function register(username, email, password, bio = '') {
    const url = API_CONFIG.AUTH.REGISTER;
    const options = getFetchOptions('POST', {
        username,
        email,
        password,
        bio,
    });
    
    return await apiCall(url, options);
}

/**
 * 로그인
 */
async function login(username, password) {
    const url = API_CONFIG.AUTH.LOGIN;
    const options = getFetchOptions('POST', {
        username,
        password,
    });
    
    return await apiCall(url, options);
}

/**
 * 로그아웃
 */
async function logout() {
    const url = API_CONFIG.AUTH.LOGOUT;
    const options = getFetchOptions('POST');
    
    return await apiCall(url, options);
}

/**
 * 현재 사용자 정보 조회
 */
async function getCurrentUser() {
    const url = API_CONFIG.AUTH.ME;
    const options = getFetchOptions('GET');
    
    try {
        const data = await apiCall(url, options);
        // 인증되지 않은 사용자는 null 반환
        if (data.message && data.message.includes('인증되지 않은')) {
            return null;
        }
        return data;
    } catch (error) {
        return null;
    }
}

/**
 * 사용자 정보 업데이트
 */
async function updateUser(updates) {
    const url = API_CONFIG.AUTH.UPDATE;
    const options = getFetchOptions('PATCH', updates);
    
    return await apiCall(url, options);
}

/**
 * 이메일 인증
 */
async function verifyEmail(token) {
    const url = `${API_CONFIG.AUTH.VERIFY_EMAIL}?token=${token}`;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 인증 이메일 재발송
 */
async function resendVerification() {
    const url = API_CONFIG.AUTH.RESEND_VERIFICATION;
    const options = getFetchOptions('POST');
    
    return await apiCall(url, options);
}

