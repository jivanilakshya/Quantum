/**
 * API client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class APIClient {
    private baseURL: string;
    private token: string | null = null;

    constructor(baseURL: string = API_BASE_URL) {
        this.baseURL = baseURL;
        // Try to load token from localStorage
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('auth_token');
        }
    }

    setToken(token: string) {
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('auth_token', token);
        }
    }

    clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
    }

    private async request(endpoint: string, options: RequestInit = {}) {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string> || {}),
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || 'Request failed');
        }

        return response.json();
    }

    // Authentication
    async login(email: string, password: string) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        if (data.access_token) {
            this.setToken(data.access_token);
        }
        return data;
    }

    async signup(name: string, email: string, password: string, role: string) {
        const data = await this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role }),
        });
        if (data.access_token) {
            this.setToken(data.access_token);
        }
        return data;
    }

    // Bot Management
    async startBot(platform: string, meetingUrl: string, language: string = 'en', botName: string = 'Quantum AI Bot') {
        return this.request('/bots/start', {
            method: 'POST',
            body: JSON.stringify({
                platform,
                meeting_url: meetingUrl,
                language,
                bot_name: botName,
            }),
        });
    }

    async stopBot(platform: string, meetingId: string) {
        return this.request('/bots/stop', {
            method: 'POST',
            body: JSON.stringify({
                platform,
                native_meeting_id: meetingId,
            }),
        });
    }

    async getBotStatus() {
        return this.request('/bots/status');
    }

    async updateBotLanguage(platform: string, meetingId: string, language: string) {
        return this.request(`/bots/${platform}/${meetingId}/language`, {
            method: 'PUT',
            body: JSON.stringify({ language }),
        });
    }

    // Meeting Management
    async listMeetings() {
        return this.request('/meetings/');
    }

    async getTranscript(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/transcript`);
    }

    async updateMeeting(
        platform: string,
        meetingId: string,
        data: {
            name?: string;
            participants?: string[];
            languages?: string[];
            notes?: string;
        }
    ) {
        return this.request(`/meetings/${platform}/${meetingId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteMeetingTranscripts(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}`, {
            method: 'DELETE',
        });
    }

    // Meeting Processing
    async processMeeting(platform: string, meetingId: string, title?: string) {
        return this.request(`/meetings/${platform}/${meetingId}/process`, {
            method: 'POST',
            body: JSON.stringify({ title }),
        });
    }

    async getMeetingSummary(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/summary`);
    }

    async getActionItems(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/action-items`);
    }

    async getParticipants(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/participants`);
    }

    async getEmotions(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/emotions`);
    }

    async getMeetingStatus(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/status`);
    }

    async checkBackendConnection(): Promise<boolean> {
        try {
            // Try connecting to health endpoint without /api prefix
            const healthUrl = this.baseURL.replace('/api', '') + '/health';
            console.log('Checking backend connection at:', healthUrl);
            
            const response = await fetch(healthUrl, {
                method: 'GET',
                mode: 'cors', // Explicitly allow CORS
                cache: 'no-cache',
            });
            
            console.log('Health check response:', response.status, response.statusText);
            return response.ok;
        } catch (error: any) {
            console.error('Backend connection check failed:', error);
            console.error('Error details:', {
                message: error.message,
                name: error.name,
                stack: error.stack,
            });
            return false;
        }
    }

    async analyzeVideoEmotions(file: File, meetingId?: string) {
        // First check if backend is reachable
        const isBackendRunning = await this.checkBackendConnection();
        if (!isBackendRunning) {
            throw new Error(
                `Cannot connect to backend server at ${this.baseURL.replace('/api', '')}. ` +
                `Please ensure the backend is running on port 8000. ` +
                `Run: cd quantum-backend && python main.py`
            );
        }

        const formData = new FormData();
        formData.append('file', file);
        if (meetingId) {
            formData.append('meeting_id', meetingId);
        }

        // Don't set Content-Type header - browser will set it automatically with boundary for FormData
        const headers: HeadersInit = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        // Explicitly do NOT set Content-Type - let browser handle it

        const endpoint = `${this.baseURL}/meetings/analyze-video-emotions`;
        console.log('Uploading to:', endpoint);
        console.log('File:', file.name, 'Size:', (file.size / 1024 / 1024).toFixed(2), 'MB');

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers,
                body: formData,
            });

            console.log('Response status:', response.status, response.statusText);

            if (!response.ok) {
                let errorMessage = 'Request failed';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || error.message || errorMessage;
                } catch (e) {
                    // If response is not JSON, try to get text
                    try {
                        const text = await response.text();
                        errorMessage = text || errorMessage;
                    } catch (e2) {
                        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    }
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            console.log('Video analysis successful:', result);
            return result;
        } catch (error: any) {
            console.error('Video upload error:', error);
            // Handle network errors
            if (error instanceof TypeError && (error.message.includes('fetch') || error.message.includes('Failed to fetch'))) {
                throw new Error(
                    `Network error: Cannot connect to backend at ${this.baseURL}. ` +
                    `Please check:\n` +
                    `1. Backend server is running (python main.py in quantum-backend directory)\n` +
                    `2. Backend is accessible at http://localhost:8000\n` +
                    `3. No firewall is blocking the connection\n` +
                    `4. Check browser console for CORS errors`
                );
            }
            throw error;
        }
    }

    async startEmotionAnalysis(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/start-emotion-analysis`, {
            method: 'POST',
        });
    }

    async processEmotionFrame(platform: string, meetingId: string, file: File) {
        const formData = new FormData();
        formData.append('file', file);

        const headers: HeadersInit = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${this.baseURL}/meetings/${platform}/${meetingId}/process-emotion-frame`, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || 'Request failed');
        }

        return response.json();
    }

    async stopEmotionAnalysis(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/stop-emotion-analysis`, {
            method: 'POST',
        });
    }

    async getEmotionAnalysisStatus(platform: string, meetingId: string) {
        return this.request(`/meetings/${platform}/${meetingId}/emotion-analysis-status`);
    }
}

export const apiClient = new APIClient();
