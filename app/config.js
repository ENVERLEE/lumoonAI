// API 설정 및 엔드포인트
// Django API 서버 URL (별도로 실행되는 Django 서버)
const API_BASE_URL = 'https://lumoonai-production.up.railway.app';
const API_CONFIG = {
    BASE_URL: `${API_BASE_URL}/api`,
    
    // 인증
    AUTH: {
        REGISTER: `${API_BASE_URL}/api/auth/register/`,
        LOGIN: `${API_BASE_URL}/api/auth/login/`,
        LOGOUT: `${API_BASE_URL}/api/auth/logout/`,
        ME: `${API_BASE_URL}/api/auth/me/`,
        UPDATE: `${API_BASE_URL}/api/auth/update/`,
        VERIFY_EMAIL: `${API_BASE_URL}/api/auth/verify-email/`,
        RESEND_VERIFICATION: `${API_BASE_URL}/api/auth/resend-verification/`,
    },
    
    // 대화
    CONVERSATIONS: `${API_BASE_URL}/api/conversations/`,
    MESSAGES: `${API_BASE_URL}/api/messages/`,
    
    // 핵심 API
    INTENT_PARSE: `${API_BASE_URL}/api/intent/parse/`,
    CONTEXT_QUESTIONS: `${API_BASE_URL}/api/context/questions/`,
    ANSWER_QUESTION: `${API_BASE_URL}/api/context/answer/`,
    PROMPT_SYNTHESIZE: `${API_BASE_URL}/api/prompt/synthesize/`,
    LLM_GENERATE: `${API_BASE_URL}/api/llm/generate/`,
    FEEDBACK: `${API_BASE_URL}/api/feedback/`,
    
    // 구독
    SUBSCRIPTION_PLANS: `${API_BASE_URL}/api/subscription-plans/`,
    SUBSCRIPTIONS: `${API_BASE_URL}/api/subscriptions/`,
    
    // 결제
    PAYMENT_ACCOUNT: `${API_BASE_URL}/api/payment/account/`,
    PAYMENT_REQUEST: `${API_BASE_URL}/api/payment/request/`,
    PAYMENT_DEPOSIT_CONFIRM: `${API_BASE_URL}/api/payment/deposit/confirm/`,
    PAYMENT_STATUS: `${API_BASE_URL}/api/payment/status/`,
    
    // 초대
    INVITE_CREATE: `${API_BASE_URL}/api/invite/create/`,
    INVITE_LIST: `${API_BASE_URL}/api/invite/list/`,
    INVITE_USE: `${API_BASE_URL}/api/invite/use/`,
    INVITE_STATS: `${API_BASE_URL}/api/invite/stats/`,
    
    // 커스텀 지침
    CUSTOM_INSTRUCTIONS: `${API_BASE_URL}/api/custom-instructions/`,
};

// 공통 fetch 헤더 설정
function getFetchOptions(method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // Django 세션 쿠키 포함
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    return options;
}

// API 호출 에러 처리
async function apiCall(url, options) {
    try {
        const response = await fetch(url, options);
        
        // 응답이 JSON이 아닐 수 있음
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`서버 오류: ${text || response.statusText}`);
        }
        
        if (!response.ok) {
            // 에러 응답에 더 자세한 정보가 있을 수 있음
            let errorMessage = data.error || data.detail || data.message || `HTTP error! status: ${response.status}`;
            
            // serializer 오류인 경우 더 자세한 정보 표시
            if (data.non_field_errors) {
                errorMessage = Array.isArray(data.non_field_errors) 
                    ? data.non_field_errors.join(', ') 
                    : data.non_field_errors;
            } else if (typeof data === 'object') {
                // 필드별 오류 정보 수집
                const fieldErrors = Object.entries(data)
                    .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
                    .join('; ');
                if (fieldErrors) {
                    errorMessage += ` (${fieldErrors})`;
                }
            }
            
            console.error('API 오류 응답:', { url, status: response.status, data });
            throw new Error(errorMessage);
        }
        
        return data;
    } catch (error) {
        console.error('API 호출 오류:', { url, error: error.message, stack: error.stack });
        throw error;
    }
}

