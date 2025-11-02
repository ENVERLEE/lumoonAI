// 핵심 API 함수들 (Intent, 질문, LLM 생성)

/**
 * Intent 파싱
 */
async function parseIntent(userInput, sessionId = null, history = []) {
    const url = API_CONFIG.INTENT_PARSE;
    const body = {
        user_input: userInput,
    };
    
    // session_id가 있을 때만 추가
    if (sessionId) {
        body.session_id = sessionId;
    }
    
    // history가 있을 때만 추가
    if (history && history.length > 0) {
        body.history = history;
    }
    
    const options = getFetchOptions('POST', body);
    return await apiCall(url, options);
}

/**
 * 컨텍스트 질문 생성
 */
async function generateQuestions(sessionId, intentId = null) {
    const url = API_CONFIG.CONTEXT_QUESTIONS;
    const body = {
        session_id: sessionId,
    };
    
    // intent_id가 있으면 추가
    if (intentId) {
        body.intent_id = intentId;
    }
    
    const options = getFetchOptions('POST', body);
    
    return await apiCall(url, options);
}

/**
 * 질문 답변
 */
async function answerQuestion(sessionId, questionText, answer) {
    const url = API_CONFIG.ANSWER_QUESTION;
    const options = getFetchOptions('POST', {
        session_id: sessionId,
        question_text: questionText,
        answer,
    });
    
    return await apiCall(url, options);
}

/**
 * 프롬프트 합성
 */
async function synthesizePrompt(sessionId, userInput = null, outputFormat = null) {
    const url = API_CONFIG.PROMPT_SYNTHESIZE;
    const options = getFetchOptions('POST', {
        session_id: sessionId,
        user_input: userInput,
        output_format: outputFormat,
    });
    
    return await apiCall(url, options);
}

/**
 * LLM 응답 생성
 */
async function generateLLMResponse(sessionId, options = {}) {
    if (!sessionId) {
        throw new Error('세션 ID가 필요합니다.');
    }
    
    const {
        prompt = null,
        userInput = null,
        quality = 'balanced',
        temperature = null,
        maxTokens = null,
        internetMode = false,
        specificityLevel = '매우 구체적',
        preferredModel = null,
    } = options;
    
    const url = API_CONFIG.LLM_GENERATE;
    const body = {
        session_id: sessionId,
        quality: quality || 'balanced',
        internet_mode: internetMode || false,
        specificity_level: specificityLevel || '매우 구체적',
    };
    
    // 선택적 필드 추가
    if (prompt) {
        body.prompt = prompt;
    }
    if (userInput) {
        body.user_input = userInput;
    }
    if (temperature !== null && temperature !== undefined) {
        body.temperature = temperature;
    }
    if (maxTokens !== null && maxTokens !== undefined) {
        body.max_tokens = maxTokens;
    }
    if (preferredModel) {
        body.preferred_model = preferredModel;
    }
    
    const requestOptions = getFetchOptions('POST', body);
    return await apiCall(url, requestOptions);
}

/**
 * 피드백 제출
 */
async function submitFeedback(sessionId, feedbackText, sentiment = 'neutral', promptHistoryId = null) {
    const url = API_CONFIG.FEEDBACK;
    const options = getFetchOptions('POST', {
        session_id: sessionId,
        feedback_text: feedbackText,
        sentiment,
        prompt_history_id: promptHistoryId,
    });
    
    return await apiCall(url, options);
}

