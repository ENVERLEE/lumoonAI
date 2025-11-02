// 메인 애플리케이션 로직

// 전역 상태
const AppState = {
    currentUser: null,
    currentConversation: null,
    currentSessionId: null,
    conversations: [],
    messages: [],
    pendingQuestions: [],
    currentQuestionIndex: 0,
    session: null,  // 세션 정보 (컨텍스트 추적용)
    hasAnsweredQuestions: false,  // 질문에 답변했는지 여부
};

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    await init();
});

async function init() {
    // 현재 사용자 확인
    const user = await getCurrentUser();
    if (user) {
        AppState.currentUser = user;
        updateUIForUser(user);
    }
    
    // 대화 목록 로드
    if (user) {
        await loadConversations();
    }
    
    // 이벤트 리스너 설정
    setupEventListeners();
}

function setupEventListeners() {
    // 메시지 전송
    const messageInput = document.getElementById('messageInput');
    const btnSend = document.getElementById('btnSend');
    
    btnSend.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // 입력창 자동 높이 조정
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    
    // 새 대화 버튼
    document.getElementById('btnNewChat').addEventListener('click', handleNewConversation);
    
    // 인증 모달
    const authModal = document.getElementById('authModal');
    document.getElementById('authModalClose').addEventListener('click', () => hideModal('authModal'));
    
    // 인증 탭 전환
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tabName}Form`).classList.add('active');
        });
    });
    
    // 로그인 폼
    document.getElementById('loginFormElement').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        await handleLogin(username, password);
    });
    
    // 회원가입 폼
    document.getElementById('registerFormElement').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const bio = document.getElementById('registerBio').value;
        await handleRegister(username, email, password, bio);
    });
    
    // 프로필 버튼
    document.getElementById('btnProfile').addEventListener('click', () => {
        if (AppState.currentUser) {
            showProfileModal();
        } else {
            showModal('authModal');
        }
    });
    
    // 설정 버튼
    document.getElementById('btnSettings').addEventListener('click', () => {
        if (AppState.currentUser) {
            showSettingsModal();
        } else {
            showModal('authModal');
        }
    });
    
    // 구독 버튼
    document.getElementById('btnSubscription').addEventListener('click', () => {
        if (AppState.currentUser) {
            showSubscriptionModal();
        } else {
            showModal('authModal');
        }
    });
    
    document.getElementById('btnSubscriptionHeader').addEventListener('click', () => {
        if (AppState.currentUser) {
            showSubscriptionModal();
        } else {
            showModal('authModal');
        }
    });
    
    // 예시 질문 클릭
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('suggestion-chip')) {
            const suggestion = e.target.dataset.suggestion;
            messageInput.value = suggestion;
            messageInput.focus();
            setTimeout(() => handleSendMessage(), 100);
        }
        
        // 피드백 버튼
        if (e.target.classList.contains('btn-feedback')) {
            const sentiment = e.target.dataset.sentiment;
            const historyId = e.target.dataset.historyId;
            handleFeedback(sentiment, historyId);
        }
    });
    
    // 모달 닫기 (외부 클릭)
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal.id);
            }
        });
    });
}

// 메시지 전송 처리
async function handleSendMessage() {
    const messageInput = document.getElementById('messageInput');
    const input = messageInput.value.trim();
    
    if (!input) return;
    
    // 사용자 인증 확인
    if (!AppState.currentUser) {
        showModal('authModal');
        return;
    }
    
    // 대화가 없으면 생성
    if (!AppState.currentConversation) {
        const conv = await createConversation();
        AppState.currentConversation = conv.id;
        await loadConversations();
    }
    
    // 사용자 메시지 표시
    const userMessage = {
        role: 'user',
        content: input,
    };
    renderMessage(userMessage, document.getElementById('messagesContainer'));
    await createMessage(AppState.currentConversation, 'user', input);
    
    // 입력 필드 초기화
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // 환영 화면 숨김
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) {
        welcomeScreen.remove();
    }
    
    // 채팅 플로우 시작
    await processChatFlow(input);
}

// 채팅 플로우 처리
async function processChatFlow(userInput) {
    try {
        showLoading('AI가 분석 중입니다...');
        
        // 1. Intent 파싱
        const intentResult = await parseIntent(userInput, AppState.currentSessionId);
        AppState.currentSessionId = intentResult.session_id;
        
        // session_id 유효성 확인
        if (!intentResult.session_id) {
            throw new Error('세션 ID를 받지 못했습니다.');
        }
        
        console.log('Intent 파싱 결과:', { 
            session_id: intentResult.session_id, 
            needs_clarification: intentResult.needs_clarification,
            confidence: intentResult.intent?.confidence,
            completeness: intentResult.intent?.completeness,
            specificity: intentResult.intent?.specificity
        });
        
        // 2. 질문 생성 및 답변 수집
        // 핵심 기능: 대부분의 경우 질문을 생성하여 더 나은 답변을 위한 정보 수집
        // 첫 대화이거나 세션이 새로 생성된 경우 항상 질문 생성
        const completeness = intentResult.intent?.completeness;
        const specificity = intentResult.intent?.specificity;
        const confidence = intentResult.intent?.confidence || 0;
        
        // 질문 생성 조건 개선:
        // 1. 이전에 질문에 답변하지 않은 경우 (첫 메시지)
        // 2. needs_clarification이 true인 경우
        // 3. completeness가 COMPLETE가 아닌 경우
        // 4. specificity가 HIGH가 아닌 경우 (더 구체적인 정보 필요)
        // 5. confidence가 낮은 경우 (< 0.85)
        // 핵심: 첫 메시지이거나 정보가 불완전한 경우 질문 생성
        const isFirstMessage = !AppState.hasAnsweredQuestions;
        
        const shouldAskQuestions = isFirstMessage || 
                                   intentResult.needs_clarification || 
                                   completeness !== 'COMPLETE' ||
                                   specificity !== 'HIGH' ||
                                   confidence < 0.85;
        
        if (shouldAskQuestions) {
            console.log('질문 생성 시작...', { 
                isFirstMessage,
                needs_clarification: intentResult.needs_clarification, 
                completeness, 
                specificity, 
                confidence
            });
            
            try {
                // Intent ID 전달 (질문 생성 시 사용)
                const intentId = intentResult.intent?.id || null;
                
                if (!intentId) {
                    console.warn('Intent ID가 없어 질문 생성을 건너뜁니다.');
                } else {
                    console.log('질문 생성 요청:', { session_id: intentResult.session_id, intent_id: intentId });
                    const questionsResult = await generateQuestions(intentResult.session_id, intentId);
                    
                    if (questionsResult.questions && questionsResult.questions.length > 0) {
                        console.log(`${questionsResult.questions.length}개의 질문 생성됨:`, questionsResult.questions.map(q => q.text));
                        AppState.pendingQuestions = questionsResult.questions;
                        AppState.currentQuestionIndex = 0;
                        
                        hideLoading();
                        await processQuestions();
                        return;
                    } else {
                        console.warn('생성된 질문이 없어 LLM 응답으로 진행');
                    }
                }
            } catch (error) {
                console.error('질문 생성 실패:', error);
                const errorMessage = error.message || '질문 생성 중 오류가 발생했습니다.';
                console.error('질문 생성 오류 상세:', {
                    message: errorMessage,
                    session_id: intentResult.session_id,
                    intent_id: intentResult.intent?.id,
                    error: error
                });
                showNotification(`질문 생성 중 오류가 발생했습니다: ${errorMessage}. 바로 답변을 생성합니다.`, 'warning');
                // 질문 생성 실패해도 LLM 응답으로 진행
            }
        } else {
            console.log('질문 생성 건너뛰기 - 매우 명확한 요청', { completeness, specificity, confidence });
        }
        
        // 3. LLM 응답 생성
        hideLoading();
        showLoading('AI가 응답을 생성하는 중입니다...');
        
        const internetMode = document.getElementById('internetMode').checked;
        const specificityLevel = document.getElementById('specificityLevel').value;
        
        console.log('LLM 생성 요청:', { session_id: intentResult.session_id, userInput, internetMode, specificityLevel });
        
        const llmResult = await generateLLMResponse(intentResult.session_id, {
            userInput,
            internetMode,
            specificityLevel,
        });
        
        hideLoading();
        
        // AI 메시지 표시
        const aiMessage = {
            role: 'assistant',
            content: llmResult.response,
            references: llmResult.references || [],
            metadata: {
                prompt_history_id: llmResult.prompt_history_id,
                model_used: llmResult.model_used,
                tokens_used: llmResult.tokens_used,
            },
        };
        
        renderMessage(aiMessage, document.getElementById('messagesContainer'));
        await createMessage(AppState.currentConversation, 'assistant', llmResult.response, aiMessage.metadata);
        
    } catch (error) {
        hideLoading();
        showNotification(error.message || '오류가 발생했습니다.', 'error');
        console.error('채팅 플로우 오류:', error);
    }
}

// 질문 처리
async function processQuestions() {
    if (AppState.currentQuestionIndex >= AppState.pendingQuestions.length) {
        // 모든 질문 답변 완료, LLM 생성
        showLoading('AI가 응답을 생성하는 중입니다...');
        
        const internetMode = document.getElementById('internetMode').checked;
        const specificityLevel = document.getElementById('specificityLevel').value;
        
        const llmResult = await generateLLMResponse(AppState.currentSessionId, {
            internetMode,
            specificityLevel,
        });
        
        hideLoading();
        
        const aiMessage = {
            role: 'assistant',
            content: llmResult.response,
            references: llmResult.references || [],
            metadata: {
                prompt_history_id: llmResult.prompt_history_id,
                model_used: llmResult.model_used,
                tokens_used: llmResult.tokens_used,
            },
        };
        
        renderMessage(aiMessage, document.getElementById('messagesContainer'));
        await createMessage(AppState.currentConversation, 'assistant', llmResult.response, aiMessage.metadata);
        
        return;
    }
    
    const question = AppState.pendingQuestions[AppState.currentQuestionIndex];
    
    renderQuestion(question, document.getElementById('messagesContainer'), async (questionText, answer) => {
        await answerQuestion(AppState.currentSessionId, questionText, answer);
        AppState.hasAnsweredQuestions = true;  // 질문에 답변했음을 표시
        AppState.currentQuestionIndex++;
        await processQuestions();
    });
}

// 대화 관리
async function loadConversations() {
    try {
        const conversations = await getConversations();
        AppState.conversations = conversations;
        renderConversationList(
            conversations,
            document.getElementById('conversationList'),
            handleConversationSelect,
            handleConversationDelete
        );
    } catch (error) {
        console.error('대화 목록 로드 오류:', error);
    }
}

async function handleNewConversation() {
    AppState.currentConversation = null;
    AppState.currentSessionId = null;
    AppState.messages = [];
    AppState.pendingQuestions = [];
    AppState.currentQuestionIndex = 0;
    AppState.hasAnsweredQuestions = false;  // 새 대화 시작 시 초기화
    AppState.session = null;
    
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = '';
    renderWelcomeScreen(messagesContainer);
    
    // 활성 대화 표시 제거
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
}

async function handleConversationSelect(conversationId) {
    AppState.currentConversation = conversationId;
    
    // 활성 대화 표시
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.toggle('active', item.dataset.conversationId === conversationId);
    });
    
    // 메시지 로드
    try {
        const messages = await getMessages(conversationId);
        AppState.messages = messages;
        
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '';
        
        if (messages.length === 0) {
            renderWelcomeScreen(messagesContainer);
        } else {
            messages.forEach(msg => {
                const messageObj = {
                    role: msg.role,
                    content: msg.content,
                    metadata: msg.metadata,
                };
                if (msg.metadata && msg.metadata.references) {
                    messageObj.references = msg.metadata.references;
                }
                renderMessage(messageObj, messagesContainer);
            });
        }
    } catch (error) {
        console.error('메시지 로드 오류:', error);
        showNotification('대화를 불러오는 중 오류가 발생했습니다.', 'error');
    }
}

async function handleConversationDelete(conversationId) {
    try {
        await deleteConversation(conversationId);
        await loadConversations();
        
        if (AppState.currentConversation === conversationId) {
            handleNewConversation();
        }
        
        showNotification('대화가 삭제되었습니다.', 'success');
    } catch (error) {
        console.error('대화 삭제 오류:', error);
        showNotification('대화 삭제 중 오류가 발생했습니다.', 'error');
    }
}

// 인증 처리
async function handleLogin(username, password) {
    try {
        showLoading('로그인 중...');
        const user = await login(username, password);
        hideLoading();
        
        AppState.currentUser = user;
        updateUIForUser(user);
        hideModal('authModal');
        showNotification('로그인되었습니다.', 'success');
        
        await loadConversations();
    } catch (error) {
        hideLoading();
        showNotification(error.message || '로그인에 실패했습니다.', 'error');
    }
}

async function handleRegister(username, email, password, bio) {
    try {
        showLoading('회원가입 중...');
        const user = await register(username, email, password, bio);
        hideLoading();
        
        AppState.currentUser = user;
        updateUIForUser(user);
        hideModal('authModal');
        showNotification('회원가입이 완료되었습니다.', 'success');
        
        await loadConversations();
    } catch (error) {
        hideLoading();
        showNotification(error.message || '회원가입에 실패했습니다.', 'error');
    }
}

function updateUIForUser(user) {
    // 프로필 버튼 업데이트
    const btnProfile = document.getElementById('btnProfile');
    if (btnProfile) {
        btnProfile.innerHTML = `<span>👤</span> ${user.username}`;
    }
}

// 모달 표시 함수들
async function showProfileModal() {
    const modal = document.getElementById('profileModal');
    const content = document.getElementById('profileContent');
    
    if (!AppState.currentUser) {
        showModal('authModal');
        return;
    }
    
    const user = AppState.currentUser;
    content.innerHTML = `
        <div class="profile-section">
            <div class="profile-field">
                <label>사용자명</label>
                <input type="text" id="profileUsername" value="${escapeHtml(user.username || '')}" readonly>
            </div>
            <div class="profile-field">
                <label>이메일</label>
                <input type="email" id="profileEmail" value="${escapeHtml(user.email || '')}" readonly>
            </div>
            <div class="profile-field">
                <label>소개</label>
                <textarea id="profileBio" rows="4">${escapeHtml(user.bio || '')}</textarea>
            </div>
            <div class="profile-field">
                <label>프로필 이미지 URL</label>
                <input type="url" id="profileAvatar" value="${escapeHtml(user.avatar || '')}" placeholder="https://...">
            </div>
            <div class="profile-field">
                <label>이메일 인증</label>
                <div class="email-verification-status">
                    ${user.email_verified ? '<span class="status-badge success">✓ 인증 완료</span>' : '<span class="status-badge error">✗ 미인증</span>'}
                    ${!user.email_verified ? '<button class="btn-resend-verification btn-primary">인증 이메일 재발송</button>' : ''}
                </div>
            </div>
            <div class="profile-actions">
                <button class="btn-primary" id="btnSaveProfile">저장</button>
                <button class="btn-logout btn-secondary" id="btnLogout">로그아웃</button>
            </div>
        </div>
    `;
    
    // 저장 버튼
    document.getElementById('btnSaveProfile').addEventListener('click', async () => {
        const bio = document.getElementById('profileBio').value;
        const avatar = document.getElementById('profileAvatar').value;
        
        try {
            showLoading('저장 중...');
            const updated = await updateUser({ bio, avatar });
            AppState.currentUser = updated;
            hideLoading();
            hideModal('profileModal');
            showNotification('프로필이 업데이트되었습니다.', 'success');
        } catch (error) {
            hideLoading();
            showNotification(error.message || '저장에 실패했습니다.', 'error');
        }
    });
    
    // 재발송 버튼
    const resendBtn = document.querySelector('.btn-resend-verification');
    if (resendBtn) {
        resendBtn.addEventListener('click', async () => {
            try {
                showLoading('이메일 발송 중...');
                await resendVerification();
                hideLoading();
                showNotification('인증 이메일이 재발송되었습니다.', 'success');
            } catch (error) {
                hideLoading();
                showNotification(error.message || '이메일 발송에 실패했습니다.', 'error');
            }
        });
    }
    
    // 로그아웃 버튼
    document.getElementById('btnLogout').addEventListener('click', async () => {
        try {
            await logout();
            AppState.currentUser = null;
            AppState.currentConversation = null;
            AppState.conversations = [];
            updateUIForUser(null);
            hideModal('profileModal');
            showNotification('로그아웃되었습니다.', 'success');
            await handleNewConversation();
        } catch (error) {
            showNotification(error.message || '로그아웃에 실패했습니다.', 'error');
        }
    });
    
    // 모달 닫기
    document.getElementById('profileModalClose').addEventListener('click', () => {
        hideModal('profileModal');
    });
    
    showModal('profileModal');
}

async function showSettingsModal() {
    const modal = document.getElementById('settingsModal');
    
    if (!AppState.currentUser) {
        showModal('authModal');
        return;
    }
    
    // 커스텀 지침 로드
    try {
        const instructions = await getCustomInstructions();
        const instructionsTextarea = document.getElementById('customInstructions');
        const instructionsActive = document.getElementById('customInstructionsActive');
        
        if (instructions) {
            instructionsTextarea.value = instructions.instructions || '';
            instructionsActive.checked = instructions.is_active || false;
        } else {
            instructionsTextarea.value = '';
            instructionsActive.checked = false;
        }
    } catch (error) {
        console.error('커스텀 지침 로드 오류:', error);
    }
    
    // 저장 버튼
    document.getElementById('btnSaveCustomInstructions').addEventListener('click', async () => {
        const instructions = document.getElementById('customInstructions').value;
        const isActive = document.getElementById('customInstructionsActive').checked;
        
        try {
            showLoading('저장 중...');
            await saveCustomInstructions(instructions, isActive);
            hideLoading();
            hideModal('settingsModal');
            showNotification('커스텀 지침이 저장되었습니다.', 'success');
        } catch (error) {
            hideLoading();
            showNotification(error.message || '저장에 실패했습니다.', 'error');
        }
    });
    
    // 모달 닫기
    document.getElementById('settingsModalClose').addEventListener('click', () => {
        hideModal('settingsModal');
    });
    
    showModal('settingsModal');
}

async function showSubscriptionModal() {
    const modal = document.getElementById('subscriptionModal');
    
    if (!AppState.currentUser) {
        showModal('authModal');
        return;
    }
    
    // 탭 전환
    document.querySelectorAll('.subscription-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            document.querySelectorAll('.subscription-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.subscription-content').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tabName}Tab`).classList.add('active');
            
            // 탭별 콘텐츠 로드
            if (tabName === 'plans') loadPlansTab();
            else if (tabName === 'usage') loadUsageTab();
            else if (tabName === 'invite') loadInviteTab();
            else if (tabName === 'payment') loadPaymentTab();
        });
    });
    
    // 초기 탭 로드
    loadPlansTab();
    
    // 모달 닫기
    document.getElementById('subscriptionModalClose').addEventListener('click', () => {
        hideModal('subscriptionModal');
    });
    
    showModal('subscriptionModal');
}

// 구독 모달 탭별 로드 함수들
async function loadPlansTab() {
    const container = document.getElementById('subscriptionPlansList');
    
    try {
        showLoading('플랜 로드 중...');
        const plansResponse = await getSubscriptionPlans();
        // DRF 페이지네이션 응답 형식 처리
        const plans = plansResponse.results || plansResponse;
        
        // 현재 구독 정보 가져오기 (로그인한 경우만)
        let currentSub = null;
        try {
            if (AppState.currentUser) {
                currentSub = await getCurrentSubscription();
            }
        } catch (error) {
            console.warn('현재 구독 정보 로드 실패:', error);
            // 구독 정보 없이 계속 진행
        }
        
        hideLoading();
        
        if (!plans || plans.length === 0) {
            container.innerHTML = '<div class="error-message">사용 가능한 플랜이 없습니다.</div>';
            return;
        }
        
        container.innerHTML = plans.map(plan => {
            const isSelected = currentSub && currentSub.plan.id === plan.id;
            return `
                <div class="plan-card ${isSelected ? 'selected' : ''}" data-plan-id="${plan.id}">
                    <div class="plan-name">${escapeHtml(plan.display_name)}</div>
                    <div class="plan-price">$${parseFloat(plan.price).toFixed(2)}<span style="font-size: 0.75rem;">/월</span></div>
                    <div class="plan-description">${escapeHtml(plan.description || '')}</div>
                    <ul class="plan-features">
                        <li>월 ${(plan.monthly_limit / 1000).toFixed(0)}K 토큰</li>
                        <li>모델: ${plan.allowed_models.join(', ')}</li>
                    </ul>
                    ${!isSelected && plan.plan_type !== 'free' ? 
                        `<button class="btn-select-plan btn-primary" data-plan-id="${plan.id}">선택</button>` : 
                        isSelected ? '<div class="plan-selected">현재 플랜</div>' : ''}
                </div>
            `;
        }).join('');
        
        // 플랜 선택 버튼
        container.querySelectorAll('.btn-select-plan').forEach(btn => {
            btn.addEventListener('click', async () => {
                const planId = btn.dataset.planId;
                try {
                    showLoading('플랜 변경 중...');
                    await changeSubscription(planId);
                    hideLoading();
                    showNotification('플랜 변경을 위해 결제가 필요합니다. 결제 탭으로 이동하세요.', 'info');
                } catch (error) {
                    hideLoading();
                    if (error.message.includes('결제')) {
                        showNotification('유료 플랜은 결제가 필요합니다. 결제 탭으로 이동하세요.', 'info');
                    } else {
                        showNotification(error.message || '플랜 변경에 실패했습니다.', 'error');
                    }
                }
            });
        });
    } catch (error) {
        hideLoading();
        console.error('플랜 로드 오류:', error);
        const errorMsg = error.message || '플랜을 불러오는 중 오류가 발생했습니다.';
        container.innerHTML = `<div class="error-message">${escapeHtml(errorMsg)}</div>`;
    }
}

async function loadUsageTab() {
    const container = document.getElementById('usageStats');
    
    try {
        showLoading('사용량 로드 중...');
        const stats = await getUsageStats();
        hideLoading();
        
        const usagePercent = stats.usage_percentage || 0;
        const progressColor = usagePercent > 80 ? 'var(--error)' : usagePercent > 60 ? 'var(--warning)' : 'var(--success)';
        
        container.innerHTML = `
            <div class="usage-card">
                <div class="usage-item">
                    <label>사용한 토큰</label>
                    <div class="usage-value">${(stats.current_usage / 1000).toFixed(0)}K / ${(stats.monthly_limit / 1000).toFixed(0)}K</div>
                </div>
                <div class="usage-progress">
                    <div class="usage-progress-bar" style="width: ${usagePercent}%; background: ${progressColor}"></div>
                </div>
                <div class="usage-item">
                    <label>남은 토큰</label>
                    <div class="usage-value">${(stats.remaining / 1000).toFixed(0)}K</div>
                </div>
                <div class="usage-item">
                    <label>보너스 토큰</label>
                    <div class="usage-value">${(stats.bonus_tokens / 1000).toFixed(0)}K</div>
                </div>
            </div>
        `;
    } catch (error) {
        hideLoading();
        container.innerHTML = '<div class="error-message">사용량을 불러오는 중 오류가 발생했습니다.</div>';
    }
}

async function loadInviteTab() {
    const container = document.getElementById('inviteContent');
    
    try {
        showLoading('초대 정보 로드 중...');
        const [codes, stats] = await Promise.all([
            listInviteCodes(),
            getInviteStats(),
        ]);
        hideLoading();
        
        container.innerHTML = `
            <div class="invite-section">
                <h3>초대 코드 생성</h3>
                <button class="btn-create-invite btn-primary">새 초대 코드 생성</button>
                <div id="newInviteCode" style="margin-top: 1rem; display: none;">
                    <div class="invite-code-display">
                        <input type="text" id="generatedInviteCode" readonly>
                        <button class="btn-copy-invite">복사</button>
                    </div>
                </div>
            </div>
            
            <div class="invite-section">
                <h3>초대 통계</h3>
                <div class="invite-stats">
                    <div class="stat-item">
                        <label>전체 초대</label>
                        <div class="stat-value">${stats.total_invites}</div>
                    </div>
                    <div class="stat-item">
                        <label>사용된 초대</label>
                        <div class="stat-value">${stats.used_invites}</div>
                    </div>
                    <div class="stat-item">
                        <label>대기 중인 초대</label>
                        <div class="stat-value">${stats.pending_invites}</div>
                    </div>
                </div>
            </div>
            
            <div class="invite-section">
                <h3>초대 코드 사용</h3>
                <div class="invite-use-form">
                    <input type="text" id="inviteCodeInput" placeholder="초대 코드 입력">
                    <button class="btn-use-invite btn-primary">사용</button>
                </div>
            </div>
            
            <div class="invite-section">
                <h3>내가 생성한 초대 코드</h3>
                <div id="inviteCodesList">
                    ${codes.length === 0 ? '<p>생성한 초대 코드가 없습니다.</p>' : ''}
                    ${codes.map(code => `
                        <div class="invite-code-item">
                            <div class="invite-code-text">${escapeHtml(code.code)}</div>
                            <div class="invite-code-status">${code.is_used ? '✓ 사용됨' : '○ 사용 가능'}</div>
                            ${code.used_at ? `<div class="invite-code-date">${new Date(code.used_at).toLocaleDateString('ko-KR')}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // 초대 코드 생성
        document.querySelector('.btn-create-invite').addEventListener('click', async () => {
            try {
                showLoading('초대 코드 생성 중...');
                const code = await createInviteCode();
                hideLoading();
                
                const newCodeDiv = document.getElementById('newInviteCode');
                document.getElementById('generatedInviteCode').value = code.code;
                newCodeDiv.style.display = 'block';
                showNotification('초대 코드가 생성되었습니다.', 'success');
            } catch (error) {
                hideLoading();
                showNotification(error.message || '초대 코드 생성에 실패했습니다.', 'error');
            }
        });
        
        // 초대 코드 복사
        const copyBtn = document.querySelector('.btn-copy-invite');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                const codeInput = document.getElementById('generatedInviteCode');
                codeInput.select();
                document.execCommand('copy');
                showNotification('초대 코드가 복사되었습니다.', 'success');
            });
        }
        
        // 초대 코드 사용
        document.querySelector('.btn-use-invite').addEventListener('click', async () => {
            const code = document.getElementById('inviteCodeInput').value.trim();
            if (!code) {
                showNotification('초대 코드를 입력하세요.', 'error');
                return;
            }
            
            try {
                showLoading('초대 코드 사용 중...');
                const result = await useInviteCode(code);
                hideLoading();
                document.getElementById('inviteCodeInput').value = '';
                showNotification(result.message || '초대 코드가 사용되었습니다.', 'success');
                await loadUsageTab(); // 사용량 새로고침
            } catch (error) {
                hideLoading();
                showNotification(error.message || '초대 코드 사용에 실패했습니다.', 'error');
            }
        });
    } catch (error) {
        hideLoading();
        container.innerHTML = '<div class="error-message">초대 정보를 불러오는 중 오류가 발생했습니다.</div>';
    }
}

async function loadPaymentTab() {
    const container = document.getElementById('paymentContent');
    
    try {
        showLoading('결제 정보 로드 중...');
        const [accountInfo, paymentStatus] = await Promise.all([
            getAccountInfo(),
            getPaymentStatus(),
        ]);
        hideLoading();
        
        container.innerHTML = `
            <div class="payment-section">
                <h3>계좌 정보</h3>
                <div class="account-info">
                    <div class="account-item">
                        <label>은행명</label>
                        <div>${escapeHtml(accountInfo.bank_name)}</div>
                    </div>
                    <div class="account-item">
                        <label>계좌번호</label>
                        <div>${escapeHtml(accountInfo.account_number)}</div>
                    </div>
                    <div class="account-item">
                        <label>예금주</label>
                        <div>${escapeHtml(accountInfo.account_holder)}</div>
                    </div>
                </div>
            </div>
            
            <div class="payment-section">
                <h3>결제 요청 생성</h3>
                <p>플랜을 선택한 후 입금 완료 신청을 해주세요.</p>
            </div>
            
            <div class="payment-section">
                <h3>결제 내역</h3>
                <div id="paymentHistory">
                    ${paymentStatus.length === 0 ? '<p>결제 내역이 없습니다.</p>' : ''}
                    ${paymentStatus.map(payment => `
                        <div class="payment-item">
                            <div class="payment-plan">${escapeHtml(payment.plan?.display_name || '')}</div>
                            <div class="payment-status status-${payment.status}">${getPaymentStatusText(payment.status)}</div>
                            ${payment.status === 'pending' && !payment.deposit_confirmed ? 
                                `<button class="btn-confirm-deposit btn-primary" data-payment-id="${payment.id}">입금 완료 신청</button>` : ''}
                            <div class="payment-date">${new Date(payment.requested_at).toLocaleDateString('ko-KR')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // 입금 완료 신청 버튼
        container.querySelectorAll('.btn-confirm-deposit').forEach(btn => {
            btn.addEventListener('click', async () => {
                const paymentId = btn.dataset.paymentId;
                if (!confirm('입금 완료 신청을 하시겠습니까?')) return;
                
                try {
                    showLoading('입금 완료 신청 중...');
                    await confirmDeposit(paymentId);
                    hideLoading();
                    showNotification('입금 완료 신청이 처리되었습니다. 관리자 승인을 기다려주세요.', 'success');
                    await loadPaymentTab(); // 새로고침
                } catch (error) {
                    hideLoading();
                    showNotification(error.message || '입금 완료 신청에 실패했습니다.', 'error');
                }
            });
        });
    } catch (error) {
        hideLoading();
        container.innerHTML = '<div class="error-message">결제 정보를 불러오는 중 오류가 발생했습니다.</div>';
    }
}

function getPaymentStatusText(status) {
    const statusMap = {
        'pending': '대기중',
        'deposit_confirmed': '입금 완료 신청',
        'approved': '승인됨',
        'rejected': '거부됨',
    };
    return statusMap[status] || status;
}

// 피드백 처리
async function handleFeedback(sentiment, promptHistoryId) {
    if (!AppState.currentSessionId) {
        showNotification('세션이 없습니다.', 'error');
        return;
    }
    
    const feedbackText = sentiment === 'positive' ? '좋아요' : '아쉬워요';
    
    try {
        await submitFeedback(AppState.currentSessionId, feedbackText, sentiment, promptHistoryId);
        showNotification('피드백이 전송되었습니다.', 'success');
    } catch (error) {
        showNotification(error.message || '피드백 전송에 실패했습니다.', 'error');
    }
}

