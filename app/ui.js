// UI 컴포넌트 렌더링 함수들

/**
 * 메시지 렌더링 (사용자/AI)
 */
function renderMessage(message, container) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${message.role}`;
    
    if (message.role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                ${escapeHtml(message.content)}
            </div>
        `;
    } else if (message.role === 'assistant') {
        const referencesHtml = message.references && message.references.length > 0
            ? renderReferences(message.references)
            : '';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formatMarkdown(message.content)}
                ${referencesHtml}
            </div>
            <div class="message-actions">
                <button class="btn-feedback" data-sentiment="positive" data-history-id="${message.metadata?.prompt_history_id || ''}">
                    👍 좋아요
                </button>
                <button class="btn-feedback" data-sentiment="negative" data-history-id="${message.metadata?.prompt_history_id || ''}">
                    👎 아쉬워요
                </button>
            </div>
        `;
    }
    
    container.appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/**
 * 참고자료 렌더링
 */
function renderReferences(references) {
    if (!references || references.length === 0) return '';
    
    let html = '<div class="references-container"><h4>📚 참고자료</h4><div class="references-list">';
    
    references.forEach(ref => {
        html += `
            <a href="${escapeHtml(ref.url)}" target="_blank" rel="noopener noreferrer" class="reference-card">
                <div class="reference-title">${escapeHtml(ref.title || ref.url)}</div>
                <div class="reference-url">${escapeHtml(new URL(ref.url).hostname)}</div>
            </a>
        `;
    });
    
    html += '</div></div>';
    return html;
}

/**
 * 질문 UI 렌더링
 */
function renderQuestion(question, container, onAnswer) {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-message';
    
    let optionsHtml = '';
    if (question.options && question.options.length > 0) {
        optionsHtml = '<div class="question-options">';
        question.options.forEach((option, index) => {
            optionsHtml += `<button class="question-option" data-answer="${escapeHtml(option)}">${index + 1}. ${escapeHtml(option)}</button>`;
        });
        optionsHtml += '</div>';
    } else {
        optionsHtml = '<textarea class="question-input" placeholder="답변을 입력하세요..."></textarea>';
    }
    
    questionDiv.innerHTML = `
        <div class="question-content">
            <div class="question-text">${escapeHtml(question.text)}</div>
            ${question.rationale ? `<div class="question-rationale">💡 ${escapeHtml(question.rationale)}</div>` : ''}
            ${optionsHtml}
            <div class="question-actions">
                ${question.options && question.options.length > 0 
                    ? '' 
                    : '<button class="btn-skip-question">건너뛰기</button>'}
            </div>
        </div>
    `;
    
    container.appendChild(questionDiv);
    questionDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
    // 이벤트 리스너
    if (question.options && question.options.length > 0) {
        questionDiv.querySelectorAll('.question-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const answer = btn.dataset.answer;
                onAnswer(question.text, answer);
                questionDiv.remove();
            });
        });
    } else {
        const input = questionDiv.querySelector('.question-input');
        const skipBtn = questionDiv.querySelector('.btn-skip-question');
        
        const submitAnswer = () => {
            const answer = input.value.trim();
            if (answer) {
                onAnswer(question.text, answer);
                questionDiv.remove();
            }
        };
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitAnswer();
            }
        });
        
        questionDiv.querySelector('.question-actions').insertAdjacentHTML('afterbegin', 
            '<button class="btn-submit-answer">답변 제출</button>'
        );
        
        questionDiv.querySelector('.btn-submit-answer').addEventListener('click', submitAnswer);
        skipBtn.addEventListener('click', () => {
            onAnswer(question.text, question.default || '');
            questionDiv.remove();
        });
    }
}

/**
 * 대화 목록 렌더링
 */
function renderConversationList(conversations, container, onSelect, onDelete) {
    container.innerHTML = '';
    
    if (!conversations || conversations.length === 0) {
        container.innerHTML = '<div class="empty-conversation-list">대화가 없습니다</div>';
        return;
    }
    
    conversations.forEach(conv => {
        const convItem = document.createElement('div');
        convItem.className = 'conversation-item';
        convItem.dataset.conversationId = conv.id;
        
        const title = escapeHtml(conv.title || '새로운 대화');
        const date = new Date(conv.last_message_at || conv.created_at).toLocaleDateString('ko-KR');
        
        convItem.innerHTML = `
            <div class="conversation-title">${title}</div>
            <div class="conversation-date">${date}</div>
            <button class="btn-delete-conversation" data-conversation-id="${conv.id}">🗑️</button>
        `;
        
        convItem.addEventListener('click', (e) => {
            if (!e.target.closest('.btn-delete-conversation')) {
                onSelect(conv.id);
            }
        });
        
        const deleteBtn = convItem.querySelector('.btn-delete-conversation');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('이 대화를 삭제하시겠습니까?')) {
                onDelete(conv.id);
            }
        });
        
        container.appendChild(convItem);
    });
}

/**
 * 초기 환영 화면 렌더링
 */
function renderWelcomeScreen(container) {
    container.innerHTML = `
        <div class="welcome-screen">
            <h2>안녕하세요! 무엇을 도와드릴까요?</h2>
            <div class="suggestions">
                <button class="suggestion-chip" data-suggestion="파이썬으로 웹 크롤러 만들기">파이썬으로 웹 크롤러 만들기</button>
                <button class="suggestion-chip" data-suggestion="Django REST API 튜토리얼">Django REST API 튜토리얼</button>
                <button class="suggestion-chip" data-suggestion="React 컴포넌트 설계">React 컴포넌트 설계</button>
                <button class="suggestion-chip" data-suggestion="머신러닝 모델 평가 방법">머신러닝 모델 평가 방법</button>
            </div>
        </div>
    `;
}

/**
 * 로딩 인디케이터 표시/숨김
 */
function showLoading(message = '처리 중...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.querySelector('p').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * 모달 표시/숨김
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * 유틸리티 함수들
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // 간단한 마크다운 포맷팅
    let html = escapeHtml(text);
    
    // 코드 블록
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // 인라인 코드
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 볼드
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // 기울임
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // 줄바꿈
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

/**
 * 알림 메시지 표시
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

