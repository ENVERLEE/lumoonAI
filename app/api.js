/**
 * API Client for Loomon AI Backend
 * 
 * Provides wrapper functions for all backend API endpoints
 */

const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        credentials: 'include',  // 세션 쿠키 포함
        ...options,
    };

    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

/**
 * Parse user intent from input
 * 
 * @param {string} userInput - User's input text
 * @param {string|null} sessionId - Optional session ID
 * @param {Array} history - Optional conversation history
 * @returns {Promise<Object>} Intent parse result with session_id
 */
async function parseIntent(userInput, sessionId = null, history = []) {
    const body = {
        user_input: userInput,
        history: history,
    };

    if (sessionId) {
        body.session_id = sessionId;
    }

    return await apiFetch('/intent/parse/', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Get context questions for the current session
 * 
 * @param {string} sessionId - Session ID
 * @param {string|null} intentId - Optional intent ID
 * @returns {Promise<Object>} Questions array
 */
async function getQuestions(sessionId, intentId = null) {
    const body = {
        session_id: sessionId,
    };

    if (intentId) {
        body.intent_id = intentId;
    }

    return await apiFetch('/context/questions/', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Submit answer to a context question
 * 
 * @param {string} sessionId - Session ID
 * @param {string} questionText - Question text
 * @param {string} answer - User's answer
 * @returns {Promise<Object>} Success response
 */
async function answerQuestion(sessionId, questionText, answer) {
    return await apiFetch('/context/answer/', {
        method: 'POST',
        body: JSON.stringify({
            session_id: sessionId,
            question_text: questionText,
            answer: answer,
        }),
    });
}

/**
 * Synthesize optimized prompt
 * 
 * @param {string} sessionId - Session ID
 * @param {string|null} userInput - Optional user input override
 * @param {string|null} outputFormat - Optional output format
 * @returns {Promise<Object>} Synthesized prompt
 */
async function synthesizePrompt(sessionId, userInput = null, outputFormat = null) {
    const body = {
        session_id: sessionId,
    };

    if (userInput) {
        body.user_input = userInput;
    }

    if (outputFormat) {
        body.output_format = outputFormat;
    }

    return await apiFetch('/prompt/synthesize/', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Generate LLM response
 * 
 * @param {string} sessionId - Session ID
 * @param {Object} options - Generation options
 * @param {string} options.prompt - Optional custom prompt
 * @param {string} options.userInput - Optional user input
 * @param {string} options.quality - Quality level (fast/balanced/best)
 * @param {number} options.temperature - Temperature (0-1)
 * @param {number} options.maxTokens - Max tokens
 * @param {boolean} options.internetMode - Enable internet search mode (Perplexity Sonar)
 * @param {string} options.specificityLevel - Specificity level (짧음/간결/보통/구체적/매우 구체적)
 * @returns {Promise<Object>} LLM response
 */
async function generateLLM(sessionId, options = {}) {
    const body = {
        session_id: sessionId,
        quality: options.quality || 'balanced',
    };

    if (options.prompt) {
        body.prompt = options.prompt;
    }

    if (options.userInput) {
        body.user_input = options.userInput;
    }

    if (options.temperature !== undefined) {
        body.temperature = options.temperature;
    }

    if (options.maxTokens) {
        body.max_tokens = options.maxTokens;
    }

    if (options.internetMode !== undefined) {
        body.internet_mode = options.internetMode;
    }

    if (options.specificityLevel) {
        body.specificity_level = options.specificityLevel;
    }

    if (options.preferred_model) {
        body.preferred_model = options.preferred_model;
    }

    return await apiFetch('/llm/generate/', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Submit feedback for a response
 * 
 * @param {string} sessionId - Session ID
 * @param {string} feedbackText - Feedback text
 * @param {string} sentiment - Sentiment (positive/negative/neutral)
 * @param {string|null} promptHistoryId - Optional prompt history ID
 * @returns {Promise<Object>} Feedback response
 */
async function submitFeedback(sessionId, feedbackText, sentiment = 'neutral', promptHistoryId = null) {
    const body = {
        session_id: sessionId,
        feedback_text: feedbackText,
        sentiment: sentiment,
    };

    if (promptHistoryId) {
        body.prompt_history_id = promptHistoryId;
    }

    return await apiFetch('/feedback/', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Get session summary
 * 
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Session summary
 */
async function getSessionSummary(sessionId) {
    return await apiFetch(`/sessions/${sessionId}/summary/`, {
        method: 'GET',
    });
}

/**
 * Get session details
 * 
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Session details
 */
async function getSession(sessionId) {
    return await apiFetch(`/sessions/${sessionId}/`, {
        method: 'GET',
    });
}

/**
 * Get prompt history for a session
 * 
 * @param {string} sessionId - Session ID
 * @returns {Promise<Array>} Prompt history
 */
async function getPromptHistory(sessionId) {
    return await apiFetch(`/prompt-history/?session_id=${sessionId}`, {
        method: 'GET',
    });
}

/**
 * Set user's initial goal for a session
 * 
 * @param {string} sessionId - Session ID
 * @param {string} goal - User's goal (알기/하기/만들기/배우기)
 * @returns {Promise<Object>} Success response
 */
async function setGoal(sessionId, goal) {
    return await apiFetch(`/sessions/${sessionId}/set_goal/`, {
        method: 'POST',
        body: JSON.stringify({
            goal: goal,
        }),
    });
}

// Export API functions
window.LoomonAIAPI = {
    parseIntent,
    getQuestions,
    answerQuestion,
    synthesizePrompt,
    generateLLM,
    submitFeedback,
    getSessionSummary,
    getSession,
    getPromptHistory,
    setGoal,
};

