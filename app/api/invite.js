// Invite API functions
class InviteAPI {
    static async createCode(expiresInDays = 30) {
        const response = await fetch('/api/invite/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ expires_in_days: expiresInDays }),
        });

        if (!response.ok) throw new Error('초대 코드 생성에 실패했습니다.');
        return await response.json();
    }

    static async getCodes() {
        const response = await fetch('/api/invite/list/');
        if (!response.ok) throw new Error('초대 코드 목록을 불러올 수 없습니다.');
        const data = await response.json();
        return data.results || data;
    }

    static async useCode(code) {
        const response = await fetch('/api/invite/use/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ code: code }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '초대 코드 사용에 실패했습니다.');
        }

        return await response.json();
    }

    static async getStats() {
        const response = await fetch('/api/invite/stats/');
        if (!response.ok) throw new Error('초대 통계를 불러올 수 없습니다.');
        return await response.json();
    }

    static getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}
