/**
 * Loomon AI - Main Application Logic
 * Modern & Innovative UI Version
 */

class LoomonAIApp {
    constructor() {
        this.sessionId = null;
        this.currentQuestions = [];
        this.answeredQuestions = new Map();
        this.currentPromptHistoryId = null;
        this.conversationHistory = [];
        this.selectedGoal = null;
        this.currentUser = null;
        this.currentConversation = null;
        this.conversations = [];
        
        // Icon helper function - Simple line icons
        this.getIconSVG = (iconName, size = 20) => {
            const strokeWidth = size <= 16 ? 1.5 : 2;
            const icons = {
                'brain': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-3 3"/><path d="M12 5a3 3 0 1 1 3 3"/><path d="M12 19a3 3 0 1 0-3-3"/><path d="M12 19a3 3 0 1 1 3-3"/><path d="M5 12a3 3 0 1 0 3 3"/><path d="M19 12a3 3 0 1 1-3 3"/></svg>`,
                'lightning': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
                'palette': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12c0 5 4 9 9 9 4.1 0 7.5-2.8 8.8-6.5"/><path d="M2 2h20v20"/></svg>`,
                'book': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
                'search': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`,
                'chart': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
                'lightbulb': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="21" x2="15" y2="21"/><path d="M12 3a6 6 0 0 0-3 11.2v3.8a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-3.8A6 6 0 0 0 12 3z"/></svg>`,
                'bug': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4"/><path d="M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83"/><path d="M2 12h4M18 12h4"/><path d="M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>`,
                'settings': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M1 12h6m6 0h6"/></svg>`,
                'wrench': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
                'rocket': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>`,
                'code': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
                'file-text': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
                'layers': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
                'book-open': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
                'edit': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
                'target': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
                'map': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>`,
                'thinking': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
                'message': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
                'question': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
                'star': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9 17 13.14 18.18 20.02 12 16.77 5.82 20.02 7 13.14 2 9 8.91 8.26 12 2"/></svg>`,
                'skip': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>`,
                'thumbs-up': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/></svg>`,
                'thumbs-down': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/></svg>`,
                'robot': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2"/><path d="M12 8V4H8"/><circle cx="12" cy="15" r="1"/><path d="M7 11h10"/></svg>`,
                'link': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
                'trash': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
                'user': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
                'check': `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
            };
            return icons[iconName] || '';
        };
        
        // DOM Elements
        this.elements = {
            // Onboarding
            onboardingScreen: document.getElementById('onboardingScreen'),
            goalCards: document.querySelectorAll('.goal-card'),
            skipOnboarding: document.getElementById('skipOnboarding'),
            
            // Main App
            appContainer: document.getElementById('appContainer'),
            chatArea: document.getElementById('chatArea'),
            mainContainer: document.getElementById('mainContainer'),
            
            // Sidebar
            sidebar: document.getElementById('sidebar'),
            menuToggle: document.getElementById('menuToggle'),
            sessionList: document.getElementById('sessionList'),
            profileAvatar: document.getElementById('profileAvatar'),
            profileName: document.getElementById('profileName'),
            logoutBtn: document.getElementById('logoutBtn'),
            
            // App Bar
            subscriptionBtn: document.getElementById('subscriptionBtn'),
            
            // Chat
            welcomeScreen: document.getElementById('welcomeScreen'),
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            
            // UI Elements
            newSessionBtn: document.getElementById('newSessionBtn'),
            chatTitle: document.getElementById('chatTitle'),
            toast: document.getElementById('toast'),
            
            // Goal UI
            goalBadge: document.getElementById('goalBadge'),
            goalIcon: document.getElementById('goalIcon'),
            goalText: document.getElementById('goalText'),
            quickActions: document.getElementById('quickActions'),
            actionButtons: document.getElementById('actionButtons'),
            suggestionChipsContainer: document.getElementById('suggestionChipsContainer'),
            settingsBtn: document.getElementById('settingsBtn'),
            
            // Generation Controls
            internetModeToggle: document.getElementById('internetModeToggle'),
            modelSelect: document.getElementById('modelSelect'),
            specificityLevel: document.getElementById('specificityLevel'),
            
            // Suggestion chips
            suggestionChips: document.querySelectorAll('.suggestion-chip'),
            
            // Auth Modal
            authModal: document.getElementById('authModal'),
            authModalClose: document.getElementById('authModalClose'),
            authModalTitle: document.getElementById('authModalTitle'),
            loginForm: document.getElementById('loginForm'),
            registerForm: document.getElementById('registerForm'),
            showRegister: document.getElementById('showRegister'),
            showLogin: document.getElementById('showLogin'),
            logoutBtn: document.getElementById('logoutBtn'),
            
            // Settings Modal
            settingsModal: document.getElementById('settingsModal'),
            settingsModalClose: document.getElementById('settingsModalClose'),
            customInstructionsText: document.getElementById('customInstructionsText'),
            customInstructionsActive: document.getElementById('customInstructionsActive'),
            saveCustomInstructions: document.getElementById('saveCustomInstructions'),
            profileUsername: document.getElementById('profileUsername'),
            profileEmail: document.getElementById('profileEmail'),
            profileBio: document.getElementById('profileBio'),
            profileAvatar: document.getElementById('profileAvatar'),
            saveProfile: document.getElementById('saveProfile'),

            // Subscription UI (in conversations modal)
            subscriptionCard: document.getElementById('subscriptionCard'),
            subscriptionPlan: document.getElementById('subscriptionPlan'),
            subscriptionUsage: document.getElementById('subscriptionUsage'),
            usageProgressFill: document.getElementById('usageProgressFill'),
            subscriptionSettingsBtn: document.getElementById('subscriptionSettingsBtn'),

            // Subscription Modal
            subscriptionModal: document.getElementById('subscriptionModal'),
            subscriptionModalClose: document.getElementById('subscriptionModalClose'),
            plansGrid: document.getElementById('plansGrid'),
            usageDetails: document.getElementById('usageDetails'),
            inviteStats: document.getElementById('inviteStats'),
            createInviteBtn: document.getElementById('createInviteBtn'),
            inviteCodes: document.getElementById('inviteCodes'),
            inviteCodeInput: document.getElementById('inviteCodeInput'),
            useInviteBtn: document.getElementById('useInviteBtn'),
            paymentSection: document.getElementById('paymentSection'),
        };

        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        // Check for email verification token in URL
        const urlParams = new URLSearchParams(window.location.search);
        const verificationToken = urlParams.get('token');
        if (verificationToken) {
            try {
                await AuthAPI.verifyEmail(verificationToken);
                this.showToast('이메일 인증이 완료되었습니다!', 'success');
                // Remove token from URL
                window.history.replaceState({}, document.title, window.location.pathname);
                // Refresh user data
                await this.checkAuth();
            } catch (error) {
                this.showToast(error.message, 'error');
            }
        }
        
        // Check authentication status FIRST (login-first approach)
        await this.checkAuth();
        
        // If not logged in, show login modal immediately
        if (!this.currentUser) {
            // Hide onboarding and app container
            if (this.elements.onboardingScreen) {
                this.elements.onboardingScreen.style.display = 'none';
            }
            if (this.elements.appContainer) {
                this.elements.appContainer.classList.add('hidden');
            }
            
            // Show login modal
            this.showAuthModal('login');
            
            // Setup event listeners for auth
            this.setupEventListeners();
            return;
        }
        
        // User is logged in - proceed with normal flow
        // Check if user has completed onboarding
        const hasCompletedOnboarding = localStorage.getItem('loomon_ai_onboarding_completed');
        
        if (hasCompletedOnboarding) {
            this.skipOnboarding();
        }

        // Load session from localStorage
        this.loadSession();

        // Setup event listeners
        this.setupEventListeners();

        // Auto-resize textarea
        this.setupTextareaAutoResize();
        
        // Load conversations
        await this.loadConversations();
    }
    
    /**
     * Check authentication status
     */
    async checkAuth() {
        try {
            const user = await AuthAPI.getCurrentUser();
            if (user) {
                this.currentUser = user;
                this.updateUIForAuthenticatedUser();
            } else {
                this.updateUIForAnonymousUser();
            }
        } catch (error) {
            console.error('Auth check error:', error);
            this.updateUIForAnonymousUser();
        }
    }
    
    /**
     * Update UI for authenticated user
     */
    updateUIForAuthenticatedUser() {
        // Update profile display in sidebar
        if (this.elements.profileName) {
            this.elements.profileName.textContent = this.currentUser.username;
            this.elements.profileName.style.cursor = 'pointer';
        }
        
        // Show logout button
        if (this.elements.logoutBtn) {
            this.elements.logoutBtn.classList.remove('hidden');
        }
        
        // Show user avatar if available
        if (this.elements.profileAvatar) {
            if (this.currentUser.avatar) {
                this.elements.profileAvatar.textContent = '';
                this.elements.profileAvatar.style.backgroundImage = `url(${this.currentUser.avatar})`;
                this.elements.profileAvatar.style.backgroundSize = 'cover';
                this.elements.profileAvatar.style.backgroundPosition = 'center';
            } else {
                this.elements.profileAvatar.innerHTML = this.getIconSVG('user', 20);
                this.elements.profileAvatar.style.backgroundImage = '';
            }
        }

        // Update subscription UI
        this.updateSubscriptionUI();
    }
    
    /**
     * Handle logout
     */
    async handleLogout() {
        if (!confirm('로그아웃하시겠습니까?')) {
            return;
        }
        
        try {
            await AuthAPI.logout();
            this.currentUser = null;
            this.currentConversation = null;
            this.conversations = [];
            
            // Reset UI
            this.updateUIForAnonymousUser();
            await this.loadConversations();
            
            // Clear session
            this.sessionId = null;
            this.conversationHistory = [];
            this.elements.messages.innerHTML = '';
            this.elements.welcomeScreen.classList.remove('hidden');
            this.elements.messages.classList.add('hidden');
            
            this.showToast('로그아웃되었습니다', 'success');
        } catch (error) {
            console.error('Logout error:', error);
            this.showToast('로그아웃 실패: ' + error.message, 'error');
        }
    }
    
    /**
     * Update UI for anonymous user
     */
    updateUIForAnonymousUser() {
        // Update profile display in sidebar
        if (this.elements.profileName) {
            this.elements.profileName.textContent = '로그인';
            this.elements.profileName.style.cursor = 'pointer';
        }
        
        // Hide logout button
        if (this.elements.logoutBtn) {
            this.elements.logoutBtn.classList.add('hidden');
        }
        
        // Reset avatar
        if (this.elements.profileAvatar) {
            this.elements.profileAvatar.innerHTML = this.getIconSVG('user', 20);
            this.elements.profileAvatar.style.backgroundImage = '';
        }
        
        // Anonymous users can still use the app, but show login option
        // Don't auto-show modal, let them choose
    }
    
    /**
     * Show auth modal
     */
    showAuthModal(mode = 'login') {
        console.log('showAuthModal called with mode:', mode);
        
        // Try to find modal if not in elements
        let authModal = this.elements.authModal;
        if (!authModal) {
            authModal = document.getElementById('authModal');
            console.log('Modal found via getElementById:', authModal);
        }
        
        if (!authModal) {
            console.error('Auth modal not found in DOM');
            return;
        }
        
        // Remove hidden class and force display
        authModal.classList.remove('hidden');
        authModal.style.display = 'flex';
        authModal.style.visibility = 'visible';
        authModal.style.opacity = '1';
        authModal.style.zIndex = '10000';
        authModal.style.position = 'fixed';
        
        console.log('Modal display set, checking forms...');
        
        const loginForm = this.elements.loginForm || document.getElementById('loginForm');
        const registerForm = this.elements.registerForm || document.getElementById('registerForm');
        const modalTitle = this.elements.authModalTitle || document.getElementById('authModalTitle');
        
        if (mode === 'login') {
            if (loginForm) {
                loginForm.classList.remove('hidden');
                loginForm.style.display = 'block';
                console.log('Login form shown');
            }
            if (registerForm) {
                registerForm.classList.add('hidden');
                registerForm.style.display = 'none';
            }
            if (modalTitle) {
                modalTitle.textContent = '로그인';
            }
        } else {
            if (loginForm) {
                loginForm.classList.add('hidden');
                loginForm.style.display = 'none';
            }
            if (registerForm) {
                registerForm.classList.remove('hidden');
                registerForm.style.display = 'block';
                console.log('Register form shown');
            }
            if (modalTitle) {
                modalTitle.textContent = '회원가입';
            }
        }
        
        console.log('Modal should be visible now');
    }
    
    /**
     * Hide auth modal
     */
    hideAuthModal() {
        const authModal = this.elements.authModal || document.getElementById('authModal');
        if (authModal) {
            authModal.classList.add('hidden');
            authModal.style.display = 'none';
        }
    }
    
    /**
     * Show profile modal
     */
    async showProfileModal() {
        if (!this.currentUser) {
            this.showAuthModal('login');
            return;
        }
        
        this.elements.profileModal.classList.remove('hidden');
        
        // Load user data
        const user = this.currentUser;
        this.elements.profileModalName.textContent = user.username;
        this.elements.profileModalUsername.value = user.username;
        this.elements.profileModalEmail.value = user.email || '';
        this.elements.profileModalBio.value = user.bio || '';
        this.elements.profileModalAvatarUrl.value = user.avatar || '';
        
        // Update avatar
        const avatarElement = this.elements.profileModalAvatar;
        if (user.avatar) {
            avatarElement.style.backgroundImage = `url(${user.avatar})`;
            avatarElement.style.backgroundSize = 'cover';
            avatarElement.style.backgroundPosition = 'center';
            avatarElement.innerHTML = '';
        } else {
            avatarElement.style.backgroundImage = '';
            avatarElement.innerHTML = `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
        }
        
        // Update email verification status
        const emailVerified = user.email_verified || false;
        if (emailVerified) {
            this.elements.emailVerifiedBadge.style.display = 'inline-flex';
            this.elements.emailUnverifiedBadge.style.display = 'none';
            this.elements.resendVerificationSection.style.display = 'none';
        } else {
            this.elements.emailVerifiedBadge.style.display = 'none';
            this.elements.emailUnverifiedBadge.style.display = 'inline-flex';
            this.elements.resendVerificationSection.style.display = 'block';
        }
    }
    
    /**
     * Hide profile modal
     */
    hideProfileModal() {
        this.elements.profileModal.classList.add('hidden');
    }
    
    /**
     * Show settings modal
     */
    async showSettingsModal() {
        this.elements.settingsModal.classList.remove('hidden');
        
        // Load custom instructions
        if (this.currentUser) {
            try {
                const instructions = await CustomInstructionsAPI.getInstructions();
                if (instructions) {
                    this.elements.customInstructionsText.value = instructions.instructions;
                    this.elements.customInstructionsActive.checked = instructions.is_active;
                }
            } catch (error) {
                console.error('Load instructions error:', error);
            }
        }
    }
    
    /**
     * Hide settings modal
     */
    hideSettingsModal() {
        this.elements.settingsModal.classList.add('hidden');
    }
    
    /**
     * Load conversations
     */
    async loadConversations() {
        if (!this.currentUser) {
            // 익명 사용자는 대화 목록 로드 안 함
            if (this.elements.sessionList) {
                this.elements.sessionList.innerHTML = '<div class="empty-conversations">로그인 후 대화 기록을 볼 수 있습니다</div>';
            }
            return;
        }
        
        try {
            const response = await ConversationAPI.getConversations();
            this.conversations = response.results || [];
            this.renderConversationList();
        } catch (error) {
            console.error('Load conversations error:', error);
            if (this.elements.sessionList) {
                this.elements.sessionList.innerHTML = '<div class="empty-conversations" style="color: #EF4444;">대화 목록을 불러올 수 없습니다</div>';
            }
        }
    }
    
    /**
     * Render conversation list
     */
    renderConversationList() {
        if (!this.elements.sessionList) {
            console.warn('sessionList element not found');
            return;
        }
        
        this.elements.sessionList.innerHTML = '';
        
        if (this.conversations.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'empty-conversations';
            emptyMsg.textContent = '대화 기록이 없습니다';
            this.elements.sessionList.appendChild(emptyMsg);
            return;
        }
        
        this.conversations.forEach(conversation => {
            const item = document.createElement('div');
            item.className = 'session-item';
            if (this.currentConversation === conversation.id) {
                item.classList.add('active');
            }
            
            const title = conversation.title || '제목 없음';
            const date = new Date(conversation.last_message_at || conversation.created_at);
            const dateStr = date.toLocaleDateString('ko-KR', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            item.innerHTML = `
                <div class="session-item-content">
                    <div class="session-title">${title}</div>
                    <div class="session-date">${dateStr}</div>
                </div>
                <button class="session-delete-btn" data-conversation-id="${conversation.id}" title="삭제">${this.getIconSVG('trash', 14)}</button>
            `;
            
            // 클릭 시 대화 로드
            item.querySelector('.session-item-content').addEventListener('click', () => {
                this.loadConversation(conversation.id);
                // Mobile에서 사이드바 닫기
                if (window.innerWidth <= 768) {
                    this.elements.sidebar.classList.remove('open');
                }
            });
            
            // 삭제 버튼
            const deleteBtn = item.querySelector('.session-delete-btn');
            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm('이 대화를 삭제하시겠습니까?')) {
                    await this.deleteConversation(conversation.id);
                }
            });
            
            this.elements.sessionList.appendChild(item);
        });
    }
    
    /**
     * Delete a conversation
     */
    async deleteConversation(conversationId) {
        try {
            await ConversationAPI.deleteConversation(conversationId);
            
            // 현재 대화이면 초기화
            if (this.currentConversation === conversationId) {
                this.currentConversation = null;
                this.startNewSession();
            }
            
            // 목록 새로고침
            await this.loadConversations();
            this.showToast('대화가 삭제되었습니다', 'success');
        } catch (error) {
            console.error('Delete conversation error:', error);
            this.showToast('대화 삭제 실패: ' + error.message, 'error');
        }
    }
    
    /**
     * Load a conversation
     */
    async loadConversation(conversationId) {
        try {
            const conversation = await ConversationAPI.getConversation(conversationId);
            const messages = await ConversationAPI.getMessages(conversationId);
            
            this.currentConversation = conversationId;
            this.conversationHistory = [];
            
            // Clear current messages
            this.elements.messages.innerHTML = '';
            this.elements.messages.classList.remove('hidden');
            this.elements.welcomeScreen.classList.add('hidden');
            
            // Update title
            this.elements.chatTitle.textContent = conversation.title || '대화';
            
            // Render messages
            messages.forEach(message => {
                this.addMessage(message.content, message.role);
                // Conversation history에도 추가
                this.conversationHistory.push({
                    role: message.role,
                    content: message.content
                });
            });
            
            // 대화 목록 새로고침 (active 상태 업데이트)
            await this.loadConversations();
            
            this.scrollToBottom();
            this.showToast('대화가 로드되었습니다', 'success');
        } catch (error) {
            console.error('Load conversation error:', error);
            this.showToast('대화를 불러올 수 없습니다: ' + error.message, 'error');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Onboarding - Goal cards
        this.elements.goalCards.forEach(card => {
            card.addEventListener('click', () => this.selectGoal(card));
        });

        // Skip onboarding
        this.elements.skipOnboarding?.addEventListener('click', () => {
            this.skipOnboarding();
        });

        // Sidebar toggle (mobile)
        this.elements.menuToggle?.addEventListener('click', () => {
            this.elements.sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside (mobile)
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (this.elements.sidebar && this.elements.sidebar.classList.contains('open')) {
                    if (!this.elements.sidebar.contains(e.target) && 
                        !this.elements.menuToggle.contains(e.target)) {
                        this.elements.sidebar.classList.remove('open');
                    }
                }
            }
        });

        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.handleSendMessage());

        // Enter key to send (Shift+Enter for new line)
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        // Enable/disable send button based on input
        this.elements.messageInput.addEventListener('input', () => {
            const hasText = this.elements.messageInput.value.trim().length > 0;
            this.elements.sendBtn.disabled = !hasText;
        });

        // New session button
        this.elements.newSessionBtn?.addEventListener('click', () => this.startNewSession());

        // Suggestion chips
        this.elements.suggestionChips.forEach(chip => {
            chip.addEventListener('click', () => {
                this.elements.messageInput.value = chip.textContent;
                this.elements.sendBtn.disabled = false;
                this.handleSendMessage();
            });
        });

        
        // Auth Modal - setup after DOM is ready
        setTimeout(() => {
            const authModalClose = document.getElementById('authModalClose');
            const showRegister = document.getElementById('showRegister');
            const showLogin = document.getElementById('showLogin');
            
            authModalClose?.addEventListener('click', () => this.hideAuthModal());
            
            showRegister?.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showAuthModal('register');
            });
            
            showLogin?.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showAuthModal('login');
            });
            
            // Click outside modal to close
            const authModal = document.getElementById('authModal');
            authModal?.addEventListener('click', (e) => {
                if (e.target === authModal) {
                    this.hideAuthModal();
                }
            });
            
            // Profile name click to show login or profile modal
            if (this.elements.profileName) {
                this.elements.profileName.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.currentUser) {
                        this.showAuthModal('login');
                    } else {
                        this.showProfileModal();
                    }
                });
            }

            // User profile clickable
            const userProfile = document.getElementById('userProfile');
            if (userProfile) {
                userProfile.style.cursor = 'pointer';
                userProfile.addEventListener('click', (e) => {
                    if (e.target.closest('.logout-btn')) {
                        return;
                    }
                    if (e.target === userProfile || e.target.closest('.profile-info')) {
                        e.preventDefault();
                        e.stopPropagation();
                        if (!this.currentUser) {
                            this.showAuthModal('login');
                        } else {
                            this.showProfileModal();
                        }
                    }
                });
            }

            // Logout button
            if (this.elements.logoutBtn) {
                this.elements.logoutBtn.addEventListener('click', () => this.handleLogout());
            }
        }, 100);
        
        this.elements.loginForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        this.elements.registerForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
        
        // Profile Modal
        this.elements.profileModalClose?.addEventListener('click', () => this.hideProfileModal());
        this.elements.resendVerificationBtn?.addEventListener('click', () => this.handleResendVerification());
        this.elements.saveProfileModal?.addEventListener('click', () => this.saveProfileFromModal());
        
        // Click outside modal to close
        this.elements.profileModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.profileModal) {
                this.hideProfileModal();
            }
        });
        
        // Settings Modal
        this.elements.settingsBtn?.addEventListener('click', () => this.showSettingsModal());
        this.elements.settingsModalClose?.addEventListener('click', () => this.hideSettingsModal());
        
        this.elements.saveCustomInstructions?.addEventListener('click', () => this.saveCustomInstructions());

        // Subscription UI
        this.elements.subscriptionBtn?.addEventListener('click', () => this.showSubscriptionModal());
        this.elements.subscriptionSettingsBtn?.addEventListener('click', () => this.showSubscriptionModal());
        this.elements.subscriptionModalClose?.addEventListener('click', () => this.hideSubscriptionModal());

        // Subscription Modal Tabs
        document.querySelectorAll('#subscriptionModal .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;

                // Update active button
                document.querySelectorAll('#subscriptionModal .tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Update active tab
                document.querySelectorAll('#subscriptionModal .tab-content').forEach(t => t.classList.remove('active'));
                document.getElementById(`${targetTab}-tab`)?.classList.add('active');

                // Load tab content
                this.loadSubscriptionTabContent(targetTab);
            });
        });

        // Subscription Modal Actions
        this.elements.createInviteBtn?.addEventListener('click', () => this.handleCreateInviteCode());
        this.elements.useInviteBtn?.addEventListener('click', () => this.handleUseInviteBtn());
        
        // Settings Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                
                // Update active button
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update active tab
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                document.getElementById(`${targetTab}-tab`)?.classList.add('active');
            });
        });
    }
    
    /**
     * Handle login
     */
    async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const user = await AuthAPI.login(username, password);
            this.currentUser = user;
            this.hideAuthModal();
            this.updateUIForAuthenticatedUser();
            
            // Show app container after login
            if (this.elements.appContainer) {
                this.elements.appContainer.classList.remove('hidden');
            }
            if (this.elements.onboardingScreen) {
                this.elements.onboardingScreen.style.display = 'none';
            }
            
            // Check if user has completed onboarding
            const hasCompletedOnboarding = localStorage.getItem('loomon_ai_onboarding_completed');
            if (hasCompletedOnboarding) {
                this.skipOnboarding();
            }
            // If not completed, onboarding screen will show
            
            // Load session and conversations
            this.loadSession();
            await this.loadConversations();
            
            this.showToast('로그인 성공!', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }
    
    /**
     * Handle register
     */
    async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const bio = document.getElementById('registerBio').value;
        
        try {
            const user = await AuthAPI.register(username, email, password, bio);
            this.currentUser = user;
            this.hideAuthModal();
            this.updateUIForAuthenticatedUser();
            
            // Show app container after registration
            if (this.elements.appContainer) {
                this.elements.appContainer.classList.remove('hidden');
            }
            if (this.elements.onboardingScreen) {
                this.elements.onboardingScreen.style.display = 'none';
            }
            
            // Check if user has completed onboarding
            const hasCompletedOnboarding = localStorage.getItem('loomon_ai_onboarding_completed');
            if (hasCompletedOnboarding) {
                this.skipOnboarding();
            }
            // If not completed, onboarding screen will show
            
            // Load session and conversations
            this.loadSession();
            await this.loadConversations();
            
            // TODO: Show email verification prompt after registration
            // For now, just show success message
            this.showToast('회원가입 성공! 이메일 인증을 완료해주세요.', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }
    
    /**
     * Save custom instructions
     */
    async saveCustomInstructions() {
        const instructions = this.elements.customInstructionsText.value;
        const isActive = this.elements.customInstructionsActive.checked;
        
        try {
            await CustomInstructionsAPI.saveInstructions(instructions, isActive);
            this.showToast('커스텀 지침이 저장되었습니다', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }
    
    /**
     * Save profile from profile modal
     */
    async saveProfileFromModal() {
        const bio = this.elements.profileModalBio.value;
        const avatar = this.elements.profileModalAvatarUrl.value;
        
        try {
            const user = await AuthAPI.updateUser({ bio, avatar });
            this.currentUser = user;
            this.updateUIForAuthenticatedUser();
            // Reload profile modal to update verification status
            await this.showProfileModal();
            this.showToast('프로필이 업데이트되었습니다', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }
    
    /**
     * Handle resend verification email
     */
    async handleResendVerification() {
        try {
            await AuthAPI.resendVerification();
            this.showToast('인증 이메일이 재발송되었습니다. 이메일을 확인해주세요.', 'success');
            // Refresh user data to get updated status
            const user = await AuthAPI.getCurrentUser();
            if (user) {
                this.currentUser = user;
                // Update profile modal to reflect changes
                await this.showProfileModal();
            }
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    /**
     * Setup textarea auto-resize
     */
    setupTextareaAutoResize() {
        this.elements.messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    }

    /**
     * Select a goal from onboarding
     */
    async selectGoal(card) {
        const goal = card.getAttribute('data-goal');
        this.selectedGoal = goal;
        
        // Visual feedback
        card.style.transform = 'scale(1.1)';
        card.style.opacity = '0.7';
        
        try {
            // Create a new session if needed
            if (!this.sessionId) {
                // Parse a dummy intent to create session
                const result = await LoomonAIAPI.parseIntent(`목표: ${goal}`, null, []);
                this.sessionId = result.session_id;
                this.saveSession();
            }
            
            // Set the goal for this session
            await LoomonAIAPI.setGoal(this.sessionId, goal);
            
            setTimeout(() => {
                this.completeOnboarding(goal);
            }, 300);
            
        } catch (error) {
            console.error('Error setting goal:', error);
            // Still complete onboarding even if goal setting fails
            setTimeout(() => {
                this.completeOnboarding(goal);
            }, 300);
        }
    }

    /**
     * Complete onboarding and transition to main app
     */
    completeOnboarding(goal) {
        localStorage.setItem('loomon_ai_onboarding_completed', 'true');
        if (goal) {
            localStorage.setItem('loomon_ai_user_goal', goal);
        }
        
        // Fade out onboarding
        this.elements.onboardingScreen.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        this.elements.onboardingScreen.style.opacity = '0';
        this.elements.onboardingScreen.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            this.elements.onboardingScreen.style.display = 'none';
            this.elements.appContainer.classList.remove('hidden');
            
            // Setup goal-based UI
            if (goal) {
                this.setupGoalBasedUI(goal);
            }
            
            this.showToast(`환영합니다! 무엇이든 물어보세요.`, 'success');
        }, 500);
    }

    /**
     * Setup goal-based UI customization
     */
    setupGoalBasedUI(goal) {
        const goalConfig = {
            '알기': {
                icon: 'brain',
                subtitle: '정보를 찾고 이해하는 것을 도와드릴게요',
                actions: [
                    { icon: 'search', text: '검색', prompt: '에 대해 알려줘' },
                    { icon: 'chart', text: '비교', prompt: '와/과 의 차이점을 설명해줘' },
                    { icon: 'lightbulb', text: '설명', prompt: '는/은 무엇인가요?' },
                    { icon: 'book', text: '요약', prompt: '를/을 간단히 요약해줘' },
                ],
                suggestions: [
                    'Python과 JavaScript의 차이점',
                    'REST API란 무엇인가요?',
                    '딥러닝의 기본 개념 설명',
                    'Docker와 Kubernetes 비교',
                ]
            },
            '하기': {
                icon: 'lightning',
                subtitle: '문제를 해결하고 실행하는 것을 도와드릴게요',
                actions: [
                    { icon: 'bug', text: '디버깅', prompt: ' 에러를 해결해줘' },
                    { icon: 'settings', text: '최적화', prompt: '를/을 최적화해줘' },
                    { icon: 'wrench', text: '수정', prompt: '를/을 고쳐줘' },
                    { icon: 'rocket', text: '배포', prompt: '배포 방법 알려줘' },
                ],
                suggestions: [
                    'React 렌더링 최적화 방법',
                    'Django ORM N+1 문제 해결',
                    'Git merge conflict 해결',
                    'API 응답 속도 개선',
                ]
            },
            '만들기': {
                icon: 'palette',
                subtitle: '새로운 것을 만드는 것을 도와드릴게요',
                actions: [
                    { icon: 'code', text: '코드', prompt: '코드를 작성해줘' },
                    { icon: 'palette', text: '디자인', prompt: 'UI를 디자인해줘' },
                    { icon: 'file-text', text: '문서', prompt: '문서를 작성해줘' },
                    { icon: 'layers', text: '구조', prompt: '아키텍처를 설계해줘' },
                ],
                suggestions: [
                    'React 로그인 컴포넌트 만들기',
                    'REST API CRUD 구현',
                    'PostgreSQL 데이터베이스 스키마 설계',
                    '반응형 네비게이션 바 만들기',
                ]
            },
            '배우기': {
                icon: 'book',
                subtitle: '새로운 것을 배우는 것을 도와드릴게요',
                actions: [
                    { icon: 'book-open', text: '튜토리얼', prompt: ' 튜토리얼을 알려줘' },
                    { icon: 'edit', text: '연습', prompt: ' 연습 문제를 내줘' },
                    { icon: 'target', text: '예제', prompt: ' 예제를 보여줘' },
                    { icon: 'map', text: '로드맵', prompt: ' 학습 로드맵을 알려줘' },
                ],
                suggestions: [
                    'TypeScript 기초 배우기',
                    'Django 시작하기 튜토리얼',
                    'GraphQL 개념과 실습',
                    '알고리즘 학습 로드맵',
                ]
            }
        };

        const config = goalConfig[goal];
        if (!config) return;

        // Update goal badge
        this.elements.goalBadge.classList.remove('hidden');
        this.elements.goalIcon.innerHTML = this.getIconSVG(config.icon, 16);
        this.elements.goalText.textContent = goal;

        // Update subtitle
        this.elements.chatSubtitle.textContent = config.subtitle;

        // Setup quick actions
        this.elements.quickActions.classList.remove('hidden');
        this.elements.actionButtons.innerHTML = '';
        config.actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.innerHTML = `
                <span class="action-btn-icon">${this.getIconSVG(action.icon, 24)}</span>
                <span class="action-btn-text">${action.text}</span>
            `;
            btn.addEventListener('click', () => {
                this.elements.messageInput.value = action.prompt;
                this.elements.messageInput.focus();
                this.elements.sendBtn.disabled = false;
            });
            this.elements.actionButtons.appendChild(btn);
        });

        // Update suggestion chips
        this.elements.suggestionChipsContainer.innerHTML = '';
        config.suggestions.forEach(suggestion => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                this.elements.messageInput.value = suggestion;
                this.elements.sendBtn.disabled = false;
                this.handleSendMessage();
            });
            this.elements.suggestionChipsContainer.appendChild(chip);
        });
    }

    /**
     * Skip onboarding
     */
    skipOnboarding() {
        localStorage.setItem('loomon_ai_onboarding_completed', 'true');
        this.elements.onboardingScreen.style.display = 'none';
        this.elements.appContainer.classList.remove('hidden');
        
        // Check if user has a saved goal
        const savedGoal = localStorage.getItem('loomon_ai_user_goal');
        if (savedGoal) {
            this.setupGoalBasedUI(savedGoal);
        }
    }

    /**
     * Load session from localStorage
     */
    loadSession() {
        const savedSessionId = localStorage.getItem('loomon_ai_session_id');
        if (savedSessionId) {
            this.sessionId = savedSessionId;
            this.updateSessionInfo();
        }
    }

    /**
     * Save session to localStorage
     */
    saveSession() {
        if (this.sessionId) {
            localStorage.setItem('loomon_ai_session_id', this.sessionId);
            this.updateSessionInfo();
        }
    }

    /**
     * Update session info display (removed - no longer needed)
     */
    updateSessionInfo() {
        // Session info no longer displayed in new layout
    }

    /**
     * Start a new session
     */
    startNewSession() {
        this.sessionId = null;
        this.currentQuestions = [];
        this.answeredQuestions.clear();
        this.currentPromptHistoryId = null;
        this.conversationHistory = [];
        
        localStorage.removeItem('loomon_ai_session_id');
        
        // Clear messages
        this.elements.messages.innerHTML = '';
        this.elements.messages.classList.add('hidden');
        this.elements.welcomeScreen.classList.remove('hidden');
        
        // Reset chat title
        this.elements.chatTitle.textContent = '새로운 대화';
        
        this.updateSessionInfo();
        this.showToast('새 세션이 시작되었습니다', 'success');
    }

    /**
     * Handle sending a message
     */
    async handleSendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        // Clear input
        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.elements.sendBtn.disabled = true;

        // Hide welcome screen, show messages
        this.elements.welcomeScreen.classList.add('hidden');
        this.elements.messages.classList.remove('hidden');

        // Add user message to UI
        this.addMessage(message, 'user');

        // Update chat title with first message
        if (this.conversationHistory.length === 0) {
            const title = message.substring(0, 50) + (message.length > 50 ? '...' : '');
            this.elements.chatTitle.textContent = title;
            
            // 로그인한 사용자는 대화 생성
            if (this.currentUser && !this.currentConversation) {
                try {
                    const conversation = await ConversationAPI.createConversation(title);
                    this.currentConversation = conversation.id;
                } catch (error) {
                    console.error('Failed to create conversation:', error);
                }
            }
        }

        // Scroll to bottom
        this.scrollToBottom();

        try {
            // Show loading
            this.showLoading();

            // Step 1: Parse Intent
            const intentResult = await LoomonAIAPI.parseIntent(
                message,
                this.sessionId,
                this.conversationHistory
            );

            // Save session ID
            if (!this.sessionId) {
                this.sessionId = intentResult.session_id;
                this.saveSession();
            }

            // Add to conversation history
            this.conversationHistory.push({
                role: 'user',
                content: message,
            });

            // Step 2: Get questions if needed
            if (intentResult.needs_clarification || !this.currentQuestions.length) {
                // Show AI is analyzing
                this.addSystemMessage('AI가 추가 정보가 필요한지 확인하고 있습니다...', 'thinking');
                
                const questionsResult = await LoomonAIAPI.getQuestions(this.sessionId);
                
                if (questionsResult.questions && questionsResult.questions.length > 0) {
                    this.currentQuestions = questionsResult.questions;
                    this.hideLoading();
                    
                    // Add explanation message
                    this.addSystemMessage(
                        `더 정확한 답변을 위해 ${questionsResult.questions.length}가지 질문을 드릴게요!`,
                        'message'
                    );
                    
                    // Display questions one by one
                    await this.displayQuestions();
                    return;
                }
            }

            // Step 3: Generate LLM response directly if no questions
            await this.generateResponse();
            
            // 대화 목록 새로고침 (로그인한 사용자)
            if (this.currentUser) {
                await this.loadConversations();
            }

        } catch (error) {
            console.error('Error handling message:', error);
            this.hideLoading();
            this.showToast(`오류: ${error.message}`, 'error');
            this.addMessage('죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.', 'system');
        }
    }

    /**
     * Display context questions
     */
    async displayQuestions() {
        for (const question of this.currentQuestions) {
            await this.displaySingleQuestion(question);
        }

        // After all questions answered, generate response
        await this.generateResponse();
        
        // 대화 목록 새로고침 (로그인한 사용자)
        if (this.currentUser) {
            await this.loadConversations();
        }
    }

    /**
     * Display a single question with options
     */
    displaySingleQuestion(question) {
        return new Promise((resolve) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question-message';
            
            // Priority indicator
            const priorityBadge = document.createElement('div');
            priorityBadge.className = 'question-priority';
            const priorityCount = Math.min(question.priority || 3, 5);
            const priorityStars = this.getIconSVG('star', 14).repeat(priorityCount);
            priorityBadge.innerHTML = `<span class="priority-label">중요도</span> ${priorityStars}`;
            questionDiv.appendChild(priorityBadge);

            // Question text with icon
            const questionHeader = document.createElement('div');
            questionHeader.className = 'question-header';
            questionHeader.innerHTML = `
                <span class="question-icon">${this.getIconSVG('question', 24)}</span>
                <span class="question-text">${question.text}</span>
            `;
            questionDiv.appendChild(questionHeader);

            // Rationale (if exists)
            if (question.rationale) {
                const rationale = document.createElement('div');
                rationale.className = 'question-rationale';
                rationale.innerHTML = `
                    <span class="rationale-icon">${this.getIconSVG('lightbulb', 20)}</span>
                    <span class="rationale-text">${question.rationale}</span>
                `;
                questionDiv.appendChild(rationale);
            }

            // Options
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'question-options';

            const options = question.options || ['예', '아니오', '잘 모르겠어요'];
            
            options.forEach((option, index) => {
                const button = document.createElement('button');
                button.className = 'option-btn';
                button.innerHTML = `
                    <span class="option-number">${index + 1}</span>
                    <span class="option-text">${option}</span>
                `;
                
                button.addEventListener('click', async () => {
                    // Mark as selected
                    optionsDiv.querySelectorAll('.option-btn').forEach(btn => {
                        btn.classList.remove('selected');
                        btn.disabled = true;
                    });
                    button.classList.add('selected');

                    // Save answer
                    this.answeredQuestions.set(question.text, option);

                    try {
                        // Send answer to backend
                        await LoomonAIAPI.answerQuestion(
                            this.sessionId,
                            question.text,
                            option
                        );

                        // Add user's answer as message with context
                        setTimeout(() => {
                            this.addMessage(`${this.getIconSVG('check', 16)} ${option}`, 'user');
                            resolve();
                        }, 300);

                    } catch (error) {
                        console.error('Error answering question:', error);
                        this.showToast('답변 저장 실패', 'error');
                        resolve();
                    }
                });

                optionsDiv.appendChild(button);
            });

            questionDiv.appendChild(optionsDiv);
            
            // Add skip option
            const skipBtn = document.createElement('button');
            skipBtn.className = 'skip-question-btn';
            skipBtn.innerHTML = `${this.getIconSVG('skip', 16)} 건너뛰기`;
            skipBtn.addEventListener('click', () => {
                this.addMessage(`${this.getIconSVG('skip', 16)} 건너뛰기`, 'user');
                resolve();
            });
            questionDiv.appendChild(skipBtn);
            
            this.elements.messages.appendChild(questionDiv);
            this.scrollToBottom();
        });
    }

    /**
     * Generate final LLM response
     */
    async generateResponse() {
        try {
            this.showLoading();

            // Get generation settings
            const internetMode = this.elements.internetModeToggle?.checked || false;
            const specificityLevel = this.elements.specificityLevel?.value || '간결';
            const preferredModel = this.elements.modelSelect?.value || '';

            const result = await LoomonAIAPI.generateLLM(this.sessionId, {
                quality: 'balanced',
                internetMode: internetMode,
                specificityLevel: specificityLevel,
                preferred_model: preferredModel,
            });

            this.hideLoading();

            // Save prompt history ID for feedback
            this.currentPromptHistoryId = result.prompt_history_id;

            // Add response to UI (with references if available)
            this.addMessage(result.response, 'system', true, result.references);
            
            // 대화 제목 업데이트 (첫 메시지인 경우)
            if (this.currentUser && this.currentConversation && this.conversationHistory.filter(m => m.role === 'user').length === 1) {
                const firstUserMessage = this.conversationHistory.find(m => m.role === 'user');
                if (firstUserMessage) {
                    const title = firstUserMessage.content.substring(0, 50) + 
                        (firstUserMessage.content.length > 50 ? '...' : '');
                    try {
                        await ConversationAPI.renameConversation(this.currentConversation, title);
                        this.elements.chatTitle.textContent = title;
                        await this.loadConversations(); // 목록 새로고침
                    } catch (error) {
                        console.error('Failed to update conversation title:', error);
                    }
                }
            }

            // Add to conversation history
            this.conversationHistory.push({
                role: 'assistant',
                content: result.response,
            });

            // Show model info with settings
            let modelInfo = `모델: ${this.getModelDisplayName(result.model_used)} | 토큰: ${result.tokens_used}`;
            if (internetMode) {
                modelInfo += ' | 🌐 인터넷 검색 사용';
                if (result.references && result.references.length > 0) {
                    modelInfo += ` (${result.references.length}개 참고자료)`;
                }
            }
            modelInfo += ` | 구체성: ${specificityLevel}`;
            this.addSystemInfo(modelInfo);

            // Clear current questions
            this.currentQuestions = [];
            this.answeredQuestions.clear();

        } catch (error) {
            console.error('Error generating response:', error);
            this.hideLoading();
            this.showToast(`응답 생성 실패: ${error.message}`, 'error');
            this.addMessage('응답을 생성하는 중 오류가 발생했습니다.', 'system');
        }
    }

    /**
     * Add a message to the chat
     */
    addMessage(content, type = 'system', withFeedback = false, references = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        bubble.appendChild(contentDiv);

        // Add timestamp
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
        });
        bubble.appendChild(time);

        // Add references if available
        if (references && references.length > 0) {
            const referencesDiv = document.createElement('div');
            referencesDiv.className = 'message-references';
            referencesDiv.innerHTML = `<div class="references-title">${this.getIconSVG('book', 16)} 참고 자료</div>`;
            
            const referencesGrid = document.createElement('div');
            referencesGrid.className = 'references-grid';
            
            references.forEach(ref => {
                const refCard = document.createElement('a');
                refCard.className = 'reference-card';
                refCard.href = ref.url;
                refCard.target = '_blank';
                refCard.rel = 'noopener noreferrer';
                refCard.innerHTML = `
                    <div class="reference-icon">${this.getIconSVG('link', 16)}</div>
                    <div class="reference-content">
                        <div class="reference-title">${ref.title}</div>
                        <div class="reference-url">${new URL(ref.url).hostname}</div>
                    </div>
                `;
                referencesGrid.appendChild(refCard);
            });
            
            referencesDiv.appendChild(referencesGrid);
            bubble.appendChild(referencesDiv);
        }

        // Add feedback buttons for system messages
        if (withFeedback && type === 'system') {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-buttons';

            const positiveBtn = this.createFeedbackButton(`${this.getIconSVG('thumbs-up', 16)} 좋아요`, 'positive');
            const negativeBtn = this.createFeedbackButton(`${this.getIconSVG('thumbs-down', 16)} 아쉬워요`, 'negative');

            feedbackDiv.appendChild(positiveBtn);
            feedbackDiv.appendChild(negativeBtn);
            bubble.appendChild(feedbackDiv);
        }

        messageDiv.appendChild(bubble);
        this.elements.messages.appendChild(messageDiv);

        this.scrollToBottom();
    }

    /**
     * Add system message (AI status updates)
     */
    addSystemMessage(content, iconType = 'robot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-status-message';
        messageDiv.innerHTML = `
            <div class="status-icon">${this.getIconSVG(iconType, 20)}</div>
            <div class="status-text">${content}</div>
        `;
        this.elements.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Add system info message
     */
    addSystemInfo(content) {
        const infoDiv = document.createElement('div');
        infoDiv.style.cssText = `
            text-align: center;
            padding: 8px;
            margin: 8px 0;
            font-size: 12px;
            color: var(--text-tertiary);
            font-family: monospace;
        `;
        infoDiv.textContent = content;
        this.elements.messages.appendChild(infoDiv);
    }

    /**
     * Create feedback button
     */
    createFeedbackButton(text, sentiment) {
        const button = document.createElement('button');
        button.className = `feedback-btn ${sentiment}`;
        button.textContent = text;

        button.addEventListener('click', async () => {
            try {
                await LoomonAIAPI.submitFeedback(
                    this.sessionId,
                    `User ${sentiment} feedback`,
                    sentiment,
                    this.currentPromptHistoryId
                );

                button.disabled = true;
                button.style.opacity = '0.5';
                this.showToast('피드백이 전송되었습니다', 'success');

            } catch (error) {
                console.error('Error submitting feedback:', error);
                this.showToast('피드백 전송 실패', 'error');
            }
        });

        return button;
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        this.elements.loadingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        this.elements.loadingIndicator.style.display = 'none';
    }

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        setTimeout(() => {
            if (this.elements.chatArea) {
                this.elements.chatArea.scrollTop = this.elements.chatArea.scrollHeight;
            }
        }, 100);
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = this.elements.toast;
        toast.textContent = message;
        toast.className = `toast ${type} show`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    /**
     * Update model selection UI based on subscription
     */
    async updateModelSelectionUI() {
        if (!this.currentUser) {
            this.elements.modelSelect.style.display = 'none';
            return;
        }

        try {
            const availableModels = await SubscriptionAPI.getAvailableModels();

            // Clear existing options except "자동 선택"
            this.elements.modelSelect.innerHTML = '<option value="">자동 선택</option>';

            // Add available models
            availableModels.forEach(model => {
                if (model.is_available) {
                    const option = document.createElement('option');
                    option.value = model.model_name;
                    option.textContent = this.getModelDisplayName(model.model_name);
                    this.elements.modelSelect.appendChild(option);
                }
            });

            // Show/hide model selector based on available models
            const modelSelectContainer = document.getElementById('modelSelectContainer');
            if (availableModels.length > 0 && modelSelectContainer) {
                modelSelectContainer.style.display = 'inline-flex';
            } else if (modelSelectContainer) {
                modelSelectContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to update model selection UI:', error);
            this.elements.modelSelect.style.display = 'none';
        }
    }

    // ============ 구독 관련 메소드들 ============

    /**
     * Get display name for model
     */
    getModelDisplayName(modelName) {
        const modelNames = {
            'gpt-5-nano': '⚡ 빠른 응답',
            'gpt-5-mini': '⚖️ 균형 잡힌 성능',
            'gpt-5': '🧠 고품질 분석',
            'gpt-4.1': '👨‍🔬 전문가 수준',
            'gpt-4.1-mini': '🎯 효율적인 전문'
        };
        return modelNames[modelName] || modelName;
    }

    // ============ 구독 관련 메소드들 ============

    /**
     * Update subscription UI in sidebar
     */
    async updateSubscriptionUI() {
        if (!this.currentUser) {
            if (this.elements.subscriptionSection) {
                this.elements.subscriptionSection.style.display = 'none';
            }
            return;
        }

        try {
            // Get current subscription
            const subscriptionResponse = await SubscriptionAPI.getCurrentSubscription();
            const subscription = subscriptionResponse;

            // Get usage stats
            const usageStats = await SubscriptionAPI.getUsageStats();

            // Update sidebar UI
            if (this.elements.subscriptionPlan) {
                this.elements.subscriptionPlan.textContent = subscription.plan.display_name;
            }
            if (this.elements.subscriptionUsage) {
                this.elements.subscriptionUsage.textContent = `${usageStats.current_usage.toLocaleString()}/${usageStats.total_available.toLocaleString()} 토큰`;
            }

            // Update progress bar
            if (this.elements.usageProgressFill) {
                const progressPercent = usageStats.usage_percentage;
                this.elements.usageProgressFill.style.width = `${Math.min(progressPercent, 100)}%`;

                // Change color based on usage
                if (progressPercent >= 90) {
                    this.elements.usageProgressFill.style.background = 'linear-gradient(90deg, #EF4444 0%, #DC2626 100%)';
                } else if (progressPercent >= 75) {
                    this.elements.usageProgressFill.style.background = 'linear-gradient(90deg, #F59E0B 0%, #D97706 100%)';
                } else {
                    this.elements.usageProgressFill.style.background = 'linear-gradient(90deg, var(--wise-green) 0%, var(--wise-teal) 100%)';
                }
            }

            // Update model selection UI
            await this.updateModelSelectionUI();

            if (this.elements.subscriptionSection) {
                this.elements.subscriptionSection.style.display = 'block';
            }
        } catch (error) {
            console.error('Failed to update subscription UI:', error);
            if (this.elements.subscriptionSection) {
                this.elements.subscriptionSection.style.display = 'none';
            }
        }
    }

    /**
     * Show subscription modal
     */
    showSubscriptionModal() {
        this.elements.subscriptionModal.classList.remove('hidden');
        this.loadSubscriptionTabContent('plans');
    }

    /**
     * Hide subscription modal
     */
    hideSubscriptionModal() {
        this.elements.subscriptionModal.classList.add('hidden');
    }

    /**
     * Load subscription tab content
     */
    async loadSubscriptionTabContent(tabName) {
        try {
            switch (tabName) {
                case 'plans':
                    await this.loadPlansContent();
                    break;
                case 'usage':
                    await this.loadUsageContent();
                    break;
                case 'invite':
                    await this.loadInviteContent();
                    break;
                case 'payment':
                    await this.loadPaymentContent();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${tabName} content:`, error);
            this.showToast('콘텐츠를 불러오는 중 오류가 발생했습니다.', 'error');
        }
    }

    /**
     * Load plans tab content
     */
    async loadPlansContent() {
        try {
            const plans = await SubscriptionAPI.getPlans();
            const currentSubscription = await SubscriptionAPI.getCurrentSubscription();

            const plansGrid = this.elements.plansGrid;
            plansGrid.innerHTML = '';

            plans.forEach(plan => {
                const isCurrentPlan = currentSubscription.plan.id === plan.id;
                const planCard = document.createElement('div');
                planCard.className = `plan-card ${isCurrentPlan ? 'current' : ''}`;

                planCard.innerHTML = `
                    <div class="plan-header">
                        <h4>${plan.display_name}</h4>
                        ${isCurrentPlan ? '<span class="current-badge">현재 플랜</span>' : ''}
                    </div>
                    <div class="plan-price">
                        $${plan.price}/월
                    </div>
                    <div class="plan-limits">
                        월 ${plan.monthly_limit.toLocaleString()} 토큰
                    </div>
                    <div class="plan-description">
                        ${plan.description}
                    </div>
                    <div class="plan-models">
                        사용 가능 모델: ${plan.allowed_models.map(model => this.getModelDisplayName(model)).join(', ')}
                    </div>
                    ${plan.plan_type === 'free' ?
                        '<button class="btn btn-secondary" disabled>무료 플랜</button>' :
                        `<button class="btn btn-primary" onclick="app.changePlan('${plan.id}')">
                            ${isCurrentPlan ? '현재 플랜' : '플랜 변경'}
                        </button>`
                    }
                `;

                plansGrid.appendChild(planCard);
            });
        } catch (error) {
            this.elements.plansGrid.innerHTML = '<p>플랜 정보를 불러올 수 없습니다.</p>';
        }
    }

    /**
     * Load usage tab content
     */
    async loadUsageContent() {
        try {
            const usageStats = await SubscriptionAPI.getUsageStats();

            this.elements.usageDetails.innerHTML = `
                <div class="usage-summary">
                    <div class="usage-stat">
                        <div class="stat-label">현재 사용량</div>
                        <div class="stat-value">${usageStats.current_usage.toLocaleString()} 토큰</div>
                    </div>
                    <div class="usage-stat">
                        <div class="stat-label">월 제한량</div>
                        <div class="stat-value">${usageStats.monthly_limit.toLocaleString()} 토큰</div>
                    </div>
                    <div class="usage-stat">
                        <div class="stat-label">보너스 토큰</div>
                        <div class="stat-value">${usageStats.bonus_tokens.toLocaleString()} 토큰</div>
                    </div>
                    <div class="usage-stat">
                        <div class="stat-label">총 사용 가능</div>
                        <div class="stat-value">${usageStats.total_available.toLocaleString()} 토큰</div>
                    </div>
                    <div class="usage-stat">
                        <div class="stat-label">남은 토큰</div>
                        <div class="stat-value">${usageStats.remaining.toLocaleString()} 토큰</div>
                    </div>
                    <div class="usage-stat">
                        <div class="stat-label">사용률</div>
                        <div class="stat-value">${usageStats.usage_percentage}%</div>
                    </div>
                </div>
                <div class="usage-progress-large">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(usageStats.usage_percentage, 100)}%"></div>
                    </div>
                    <div class="progress-text">${usageStats.usage_percentage}% 사용됨</div>
                </div>
            `;
        } catch (error) {
            this.elements.usageDetails.innerHTML = '<p>사용량 정보를 불러올 수 없습니다.</p>';
        }
    }

    /**
     * Load invite tab content
     */
    async loadInviteContent() {
        try {
            const inviteStats = await InviteAPI.getStats();

            this.elements.inviteStats.innerHTML = `
                <div class="invite-stat">
                    <div class="stat-label">총 초대</div>
                    <div class="stat-value">${inviteStats.total_invites}</div>
                </div>
                <div class="invite-stat">
                    <div class="stat-label">사용된 초대</div>
                    <div class="stat-value">${inviteStats.used_invites}</div>
                </div>
                <div class="invite-stat">
                    <div class="stat-label">받은 보너스 토큰</div>
                    <div class="stat-value">${inviteStats.received_bonus_tokens.toLocaleString()}</div>
                </div>
            `;

            // Load invite codes
            await this.loadInviteCodes();
        } catch (error) {
            this.elements.inviteStats.innerHTML = '<p>초대 통계를 불러올 수 없습니다.</p>';
        }
    }

    /**
     * Load invite codes
     */
    async loadInviteCodes() {
        try {
            const inviteCodes = await InviteAPI.getCodes();

            const inviteCodesContainer = this.elements.inviteCodes;
            inviteCodesContainer.innerHTML = '';

            if (inviteCodes.length === 0) {
                inviteCodesContainer.innerHTML = '<p>생성된 초대 코드가 없습니다.</p>';
                return;
            }

            inviteCodes.forEach(code => {
                const codeItem = document.createElement('div');
                codeItem.className = 'invite-code-item';

                const statusText = code.is_used ? '사용됨' : '사용 가능';
                const statusClass = code.is_used ? 'used' : 'available';

                codeItem.innerHTML = `
                    <div class="code-info">
                        <div class="code-text">${code.code}</div>
                        <div class="code-status ${statusClass}">${statusText}</div>
                    </div>
                    <div class="code-actions">
                        <button class="btn btn-sm btn-secondary" onclick="navigator.clipboard.writeText('${code.code}').then(() => app.showToast('초대 코드가 복사되었습니다.', 'success'))">
                            복사
                        </button>
                    </div>
                `;

                inviteCodesContainer.appendChild(codeItem);
            });
        } catch (error) {
            this.elements.inviteCodes.innerHTML = '<p>초대 코드를 불러올 수 없습니다.</p>';
        }
    }

    /**
     * Load payment tab content
     */
    async loadPaymentContent() {
        try {
            const accountInfo = await PaymentAPI.getAccountInfo();
            const paymentRequests = await PaymentAPI.getStatus();

            let paymentContent = `
                <div class="payment-info">
                    <h4>입금 정보</h4>
                    <div class="account-details">
                        <div class="account-item">
                            <span class="account-label">은행:</span>
                            <span class="account-value">${accountInfo.bank_name}</span>
                        </div>
                        <div class="account-item">
                            <span class="account-label">계좌번호:</span>
                            <span class="account-value">${accountInfo.account_number}</span>
                        </div>
                        <div class="account-item">
                            <span class="account-label">예금주:</span>
                            <span class="account-value">${accountInfo.account_holder}</span>
                        </div>
                    </div>
                </div>

                <div class="payment-actions">
                    <button class="btn btn-primary" onclick="app.requestBasicPlan()">Basic 플랜 구매 ($9.99)</button>
                    <button class="btn btn-primary" onclick="app.requestProPlan()">Pro 플랜 구매 ($39.99)</button>
                </div>
            `;

            if (paymentRequests.length > 0) {
                paymentContent += `
                    <div class="payment-history">
                        <h4>결제 내역</h4>
                        <div class="payment-requests">
                `;

                paymentRequests.slice(0, 3).forEach(request => {
                    const statusText = {
                        'pending': '대기중',
                        'deposit_confirmed': '입금 확인 대기',
                        'approved': '승인됨',
                        'rejected': '거부됨'
                    }[request.status] || request.status;

                    paymentContent += `
                        <div class="payment-request-item">
                            <div class="request-info">
                                <div class="request-plan">${request.plan.display_name}</div>
                                <div class="request-date">${new Date(request.requested_at).toLocaleDateString()}</div>
                            </div>
                            <div class="request-status status-${request.status}">${statusText}</div>
                            ${request.status === 'pending' ? `<button class="btn btn-sm btn-secondary" onclick="app.confirmDeposit('${request.id}')">입금 완료</button>` : ''}
                        </div>
                    `;
                });

                paymentContent += `
                        </div>
                    </div>
                `;
            }

            this.elements.paymentSection.innerHTML = paymentContent;
        } catch (error) {
            this.elements.paymentSection.innerHTML = '<p>결제 정보를 불러올 수 없습니다.</p>';
        }
    }

    /**
     * Handle create invite code
     */
    async handleCreateInviteCode() {
        try {
            const inviteCode = await InviteAPI.createCode();
            this.showToast('초대 코드가 생성되었습니다!', 'success');
            await this.loadInviteCodes();
        } catch (error) {
            this.showToast('초대 코드 생성에 실패했습니다.', 'error');
        }
    }

    /**
     * Handle use invite code
     */
    async handleUseInviteBtn() {
        const code = this.elements.inviteCodeInput.value.trim();
        if (!code) {
            this.showToast('초대 코드를 입력해주세요.', 'error');
            return;
        }

        try {
            const result = await InviteAPI.useCode(code);
            this.showToast(result.message, 'success');
            this.elements.inviteCodeInput.value = '';
            await this.loadInviteContent();
            await this.updateSubscriptionUI();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    /**
     * Change plan
     */
    async changePlan(planId) {
        try {
            await SubscriptionAPI.changePlan(planId);
            this.showToast('플랜이 변경되었습니다!', 'success');
            await this.updateSubscriptionUI();
            await this.loadPlansContent();
        } catch (error) {
            this.showToast('플랜 변경에 실패했습니다.', 'error');
        }
    }

    /**
     * Request Basic plan
     */
    async requestBasicPlan() {
        await this.requestPlan('basic');
    }

    /**
     * Request Pro plan
     */
    async requestProPlan() {
        await this.requestPlan('pro');
    }

    /**
     * Request plan
     */
    async requestPlan(planType) {
        try {
            const plan = await SubscriptionAPI.getPlanByType(planType);
            await PaymentAPI.requestPayment(plan.id);
            this.showToast('결제 요청이 생성되었습니다. 계좌 정보를 확인해주세요.', 'success');
            await this.loadPaymentContent();
        } catch (error) {
            this.showToast('결제 요청 생성에 실패했습니다.', 'error');
        }
    }

    /**
     * Confirm deposit
     */
    async confirmDeposit(paymentRequestId) {
        try {
            await PaymentAPI.confirmDeposit(paymentRequestId);
            this.showToast('입금 완료 신청이 처리되었습니다. 관리자 승인을 기다려주세요.', 'success');
            await this.loadPaymentContent();
        } catch (error) {
            this.showToast('입금 완료 신청에 실패했습니다.', 'error');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LoomonAIApp();
});
