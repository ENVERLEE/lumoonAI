// 대화 관리 API 함수들

/**
 * 대화 목록 조회
 */
async function getConversations() {
    const url = API_CONFIG.CONVERSATIONS;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 새 대화 생성
 */
async function createConversation(title = '새로운 대화') {
    const url = API_CONFIG.CONVERSATIONS;
    const options = getFetchOptions('POST', { title });
    
    return await apiCall(url, options);
}

/**
 * 특정 대화의 메시지 목록 조회
 */
async function getMessages(conversationId) {
    const url = `${API_CONFIG.CONVERSATIONS}${conversationId}/messages/`;
    const options = getFetchOptions('GET');
    
    return await apiCall(url, options);
}

/**
 * 대화 이름 변경
 */
async function renameConversation(conversationId, title) {
    const url = `${API_CONFIG.CONVERSATIONS}${conversationId}/rename/`;
    const options = getFetchOptions('PATCH', { title });
    
    return await apiCall(url, options);
}

/**
 * 대화 삭제
 */
async function deleteConversation(conversationId) {
    const url = `${API_CONFIG.CONVERSATIONS}${conversationId}/`;
    const options = getFetchOptions('DELETE');
    
    return await apiCall(url, options);
}

/**
 * 메시지 생성
 */
async function createMessage(conversationId, role, content, metadata = {}) {
    const url = API_CONFIG.MESSAGES;
    const options = getFetchOptions('POST', {
        conversation_id: conversationId,
        role,
        content,
        metadata,
    });
    
    return await apiCall(url, options);
}

