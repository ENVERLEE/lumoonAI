/**
 * Authentication API
 * 
 * 사용자 인증 관련 API 함수들
 */

class AuthAPI {
    static BASE_URL = '/api';

    /**
     * 회원가입
     */
    static async register(username, email, password, bio = '') {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    bio
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '회원가입에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Register error:', error);
            throw error;
        }
    }

    /**
     * 로그인
     */
    static async login(username, password) {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    username,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '로그인에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    /**
     * 로그아웃
     */
    static async logout() {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '로그아웃에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Logout error:', error);
            throw error;
        }
    }

    /**
     * 현재 사용자 정보 조회
     */
    static async getCurrentUser() {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/me/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                // 인증되지 않은 사용자
                return null;
            }

            const data = await response.json();

            // 메시지만 있는 경우 (인증되지 않은 사용자)
            if (data.message && !data.id) {
                return null;
            }

            return data;
        } catch (error) {
            console.error('Get current user error:', error);
            return null;
        }
    }

    /**
     * 사용자 정보 업데이트
     */
    static async updateUser(updates) {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(updates)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '사용자 정보 업데이트에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Update user error:', error);
            throw error;
        }
    }

    /**
     * 이메일 인증 확인
     */
    static async verifyEmail(token) {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/verify-email/?token=${token}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '이메일 인증에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Verify email error:', error);
            throw error;
        }
    }

    /**
     * 인증 이메일 재발송
     */
    static async resendVerification() {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/resend-verification/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '인증 이메일 재발송에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Resend verification error:', error);
            throw error;
        }
    }
}

/**
 * Conversation API
 */
class ConversationAPI {
    static BASE_URL = '/api';

    /**
     * 대화 목록 조회
     */
    static async getConversations(page = 1) {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/?page=${page}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('대화 목록을 가져올 수 없습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('Get conversations error:', error);
            throw error;
        }
    }

    /**
     * 대화 생성
     */
    static async createConversation(title = '새로운 대화') {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ title })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '대화 생성에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Create conversation error:', error);
            throw error;
        }
    }

    /**
     * 대화 상세 조회
     */
    static async getConversation(conversationId) {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/${conversationId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('대화를 가져올 수 없습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('Get conversation error:', error);
            throw error;
        }
    }

    /**
     * 대화 메시지 조회
     */
    static async getMessages(conversationId) {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/${conversationId}/messages/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('메시지를 가져올 수 없습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('Get messages error:', error);
            throw error;
        }
    }

    /**
     * 대화 제목 변경
     */
    static async renameConversation(conversationId, title) {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/${conversationId}/rename/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ title })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '대화 이름 변경에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Rename conversation error:', error);
            throw error;
        }
    }

    /**
     * 대화 삭제
     */
    static async deleteConversation(conversationId) {
        try {
            const response = await fetch(`${this.BASE_URL}/conversations/${conversationId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('대화 삭제에 실패했습니다.');
            }

            return true;
        } catch (error) {
            console.error('Delete conversation error:', error);
            throw error;
        }
    }
}

/**
 * Custom Instructions API
 */
class CustomInstructionsAPI {
    static BASE_URL = '/api';

    /**
     * 커스텀 지침 조회
     */
    static async getInstructions() {
        try {
            const response = await fetch(`${this.BASE_URL}/custom-instructions/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                if (response.status === 404) {
                    return null;
                }
                throw new Error('커스텀 지침을 가져올 수 없습니다.');
            }

            const data = await response.json();
            return data.results && data.results.length > 0 ? data.results[0] : null;
        } catch (error) {
            console.error('Get instructions error:', error);
            return null;
        }
    }

    /**
     * 커스텀 지침 저장
     */
    static async saveInstructions(instructions, isActive = true) {
        try {
            const response = await fetch(`${this.BASE_URL}/custom-instructions/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    instructions,
                    is_active: isActive
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '커스텀 지침 저장에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Save instructions error:', error);
            throw error;
        }
    }

    /**
     * 커스텀 지침 업데이트
     */
    static async updateInstructions(instructionsId, instructions, isActive) {
        try {
            const response = await fetch(`${this.BASE_URL}/custom-instructions/${instructionsId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    instructions,
                    is_active: isActive
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '커스텀 지침 업데이트에 실패했습니다.');
            }

            return data;
        } catch (error) {
            console.error('Update instructions error:', error);
            throw error;
        }
    }
}

