// Subscription API functions
class SubscriptionAPI {
    static async getPlans() {
        const response = await fetch('/api/subscription-plans/');
        if (!response.ok) throw new Error('플랜 정보를 불러올 수 없습니다.');
        const data = await response.json();
        return data.results || data;
    }

    static async getCurrentSubscription() {
        const response = await fetch('/api/subscriptions/current/');
        if (!response.ok) throw new Error('구독 정보를 불러올 수 없습니다.');
        return await response.json();
    }

    static async getUsageStats() {
        const response = await fetch('/api/subscriptions/usage/');
        if (!response.ok) throw new Error('사용량 정보를 불러올 수 없습니다.');
        return await response.json();
    }

    static async getAvailableModels() {
        const response = await fetch('/api/subscriptions/available_models/');
        if (!response.ok) throw new Error('모델 정보를 불러올 수 없습니다.');
        return await response.json();
    }

    static async changePlan(planId) {
        const response = await fetch('/api/subscriptions/change/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ plan_id: planId }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '플랜 변경에 실패했습니다.');
        }

        return await response.json();
    }

    static async getPlanByType(planType) {
        const plans = await this.getPlans();
        return plans.find(plan => plan.plan_type === planType);
    }

    static getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}
