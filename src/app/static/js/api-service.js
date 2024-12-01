// src/app/static/js/api-service.js

// Base URL for all API endpoints
const BASE_URL = 'http://localhost:5002';

// API endpoint definitions
const ENDPOINTS = {
    SYSTEM: {
        STATUS: '/api/system-status',
        FIREWALL: '/api/check-firewall',
        SERVICES: '/api/service-status'
    },
    SECURITY: {
        EVENTS: '/api/security-events',
        EXECUTE_SCRIPT: '/api/execute'
    },
    ANALYSIS: {
        LLM: '/api/analyze_llm',
        LOGS: '/api/get-logs'
    },
    MONITORING: {
        CONNECTIONS: '/api/active-connections',
        NETWORK: '/api/network-status'
    }
};

/**
 * Makes an API call to the specified endpoint
 * @param {string} endpoint - The API endpoint to call
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<any>} The JSON response from the API
 */
async function apiCall(endpoint, options = {}) {
    try {
        const url = `${BASE_URL}${endpoint}`;
        
        // Log request details for debugging
        console.log('API Request:', {
            url,
            method: options.method || 'GET',
            body: options.body ? JSON.parse(options.body) : undefined
        });

        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });

        if (!response.ok) {
            // Try to get error details from response
            let errorDetails;
            try {
                errorDetails = await response.json();
            } catch {
                errorDetails = { error: response.statusText };
            }
            
            throw new Error(
                errorDetails.error || 
                `API call failed: ${response.status} ${response.statusText}`
            );
        }

        const data = await response.json();
        console.log('API Response:', data);
        return data;
    } catch (error) {
        console.error(`Error calling ${endpoint}:`, error);
        throw error;
    }
}

// API service methods for specific functionality
const apiService = {
    system: {
        async getStatus() {
            return apiCall(ENDPOINTS.SYSTEM.STATUS);
        },
        async checkFirewall() {
            return apiCall(ENDPOINTS.SYSTEM.FIREWALL);
        },
        async getServices() {
            return apiCall(ENDPOINTS.SYSTEM.SERVICES);
        }
    },
    security: {
        async getEvents() {
            return apiCall(ENDPOINTS.SECURITY.EVENTS);
        },
        async executeScript(scriptKey) {
            return apiCall(ENDPOINTS.SECURITY.EXECUTE_SCRIPT, {
                method: 'POST',
                body: JSON.stringify({ script: scriptKey })
            });
        }
    },
    analysis: {
        async analyzeLLM({ question, logs }) {  // Updated to accept object parameter
            return apiCall(ENDPOINTS.ANALYSIS.LLM, {
                method: 'POST',
                body: JSON.stringify({
                    question: question,
                    logs: logs
                })
            });
        },
        async getLogs() {
            return apiCall(ENDPOINTS.ANALYSIS.LOGS);
        },
        // Additional helper methods for analysis
        async deleteLog(logName) {
            return apiCall('/api/logs/delete', {
                method: 'POST',
                body: JSON.stringify({
                    logs: [logName]
                })
            });
        },
        async downloadLog(logName) {
            return apiCall(`/api/logs/download/${logName}`);
        }
    },
    monitoring: {
        async getConnections() {
            return apiCall(ENDPOINTS.MONITORING.CONNECTIONS);
        },
        async getNetworkStatus() {
            return apiCall(ENDPOINTS.MONITORING.NETWORK);
        }
    }
};

export { apiService, BASE_URL, ENDPOINTS };