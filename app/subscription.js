// 구독 및 결제 API 함수들

/**
 * 구독 플랜 목록 조회
 */
async function getSubscriptionPlans() {
    const url = API_CONFIG.SUBSCRIPTION_PLANS;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 현재 구독 정보 조회
 */
async function getCurrentSubscription() {
    const url = `${API_CONFIG.SUBSCRIPTIONS}current/`;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 사용량 통계 조회
 */
async function getUsageStats() {
    const url = `${API_CONFIG.SUBSCRIPTIONS}usage/`;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 사용 가능한 모델 목록 조회
 */
async function getAvailableModels() {
    const url = `${API_CONFIG.SUBSCRIPTIONS}available_models/`;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 구독 플랜 변경
 */
async function changeSubscription(planId) {
    const url = `${API_CONFIG.SUBSCRIPTIONS}change/`;
    const options = getFetchOptions('POST', {
        plan_id: planId,
    });
    
    return await apiCall(url, options);
}

/**
 * 결제 계좌 정보 조회
 */
async function getAccountInfo() {
    const url = API_CONFIG.PAYMENT_ACCOUNT;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 결제 요청 생성
 */
async function createPaymentRequest(planId) {
    const url = API_CONFIG.PAYMENT_REQUEST;
    const options = getFetchOptions('POST', {
        plan_id: planId,
    });
    
    return await apiCall(url, options);
}

/**
 * 입금 완료 신청
 */
async function confirmDeposit(paymentRequestId) {
    const url = API_CONFIG.PAYMENT_DEPOSIT_CONFIRM;
    const options = getFetchOptions('POST', {
        payment_request_id: paymentRequestId,
    });
    
    return await apiCall(url, options);
}

/**
 * 결제 상태 조회
 */
async function getPaymentStatus() {
    const url = API_CONFIG.PAYMENT_STATUS;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 커스텀 지침 조회
 */
async function getCustomInstructions() {
    const url = API_CONFIG.CUSTOM_INSTRUCTIONS;
    const options = getFetchOptions('GET');
    
    try {
        const data = await apiCall(url, options);
        if (data.length > 0) {
            return data[0]; // 첫 번째 항목 반환
        }
        return null;
    } catch (error) {
        return null;
    }
}

/**
 * 커스텀 지침 저장
 */
async function saveCustomInstructions(instructions, isActive = true) {
    const url = API_CONFIG.CUSTOM_INSTRUCTIONS;
    
    // 기존 지침이 있는지 확인
    const existing = await getCustomInstructions();
    
    if (existing) {
        // 업데이트
        const updateUrl = `${API_CONFIG.CUSTOM_INSTRUCTIONS}${existing.id}/`;
        const options = getFetchOptions('PATCH', {
            instructions,
            is_active: isActive,
        });
        return await apiCall(updateUrl, options);
    } else {
        // 생성
        const options = getFetchOptions('POST', {
            instructions,
            is_active: isActive,
        });
        return await apiCall(url, options);
    }
}

