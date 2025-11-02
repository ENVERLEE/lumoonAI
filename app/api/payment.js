// Payment API functions
class PaymentAPI {
    static async getAccountInfo() {
        const response = await fetch('/api/payment/account/');
        if (!response.ok) throw new Error('계좌 정보를 불러올 수 없습니다.');
        return await response.json();
    }

    static async requestPayment(planId) {
        const response = await fetch('/api/payment/request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ plan_id: planId }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '결제 요청 생성에 실패했습니다.');
        }

        return await response.json();
    }

    static async confirmDeposit(paymentRequestId) {
        const response = await fetch('/api/payment/deposit/confirm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ payment_request_id: paymentRequestId }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '입금 완료 신청에 실패했습니다.');
        }

        return await response.json();
    }

    static async getStatus() {
        const response = await fetch('/api/payment/status/');
        if (!response.ok) throw new Error('결제 상태를 불러올 수 없습니다.');
        const data = await response.json();
        return data.results || data;
    }

    static getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}
