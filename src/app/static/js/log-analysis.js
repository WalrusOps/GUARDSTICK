import { apiService } from './api-service.js';

class LogAnalyzer {
    constructor() {
        this.initializeElements();
        this.bindEventListeners();
        this.fetchLogs();
    }

    initializeElements() {
        this.logSelect = document.getElementById('log-select');
        this.analysisQuestion = document.getElementById('analysis-question');
        this.analyzeButton = document.getElementById('analyze-button');
        this.resultsContainer = document.getElementById('analysis-result');
        this.progressBar = document.getElementById('analysis-progress');
        this.logList = document.getElementById('log-list');
        this.logCount = document.getElementById('log-count');
    }

    bindEventListeners() {
        this.analyzeButton?.addEventListener('click', () => this.analyzeLogs());
        document.getElementById('select-all-logs')?.addEventListener('click', () => this.selectAllLogs());
        document.getElementById('deselect-all-logs')?.addEventListener('click', () => this.deselectAllLogs());
        document.getElementById('delete-selected-logs')?.addEventListener('click', () => this.deleteSelectedLogs());
        this.setupKeyboardShortcuts();
    }

    setupKeyboardShortcuts() {
        this.analysisQuestion?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.analyzeLogs();
            }
        });
    }

    async fetchLogs() {
        try {
            const data = await apiService.analysis.getLogs();
            this.updateLogList(data.logs);
        } catch (error) {
            console.error('Error fetching logs:', error);
            this.showError('Failed to fetch logs');
        }
    }

    updateLogList(logs) {
        if (!this.logList) return;
    
        this.logList.innerHTML = logs.map((log, index) => {
            // Ensure the file name is cleaned up: remove underscores and the .json extension
            const userFriendlyName = log.name.replace(/_/g, ' ').replace('.json', '');  // Replace underscores with spaces and remove .json extension
    
            // Get the DTG (Date-Time Group) of when the log was collected (assuming `log.timestamp` exists)
            const logDate = new Date(log.timestamp);  // Assuming the log object contains a 'timestamp'
            const dtg = logDate.toISOString().slice(0, 19).replace('T', ' ');  // Format: "2024-11-28 14:30:00"
    
            return `
                <div class="log-item">
                    <input type="checkbox" class="log-checkbox" id="log-${index}" value="${log.name}">
                    <label for="log-${index}" class="log-label">
                        ${userFriendlyName} (${log.size})
                        <br>
                        <small style="color: #888; font-size: 0.8em;">Collected at: ${dtg}</small>
                    </label>
                </div>
            `;
        }).join('');
    
        if (this.logCount) {
            this.logCount.textContent = `${logs.length} logs found`;
        }
    }
    
    
    

    async analyzeLogs() {
        const question = this.analysisQuestion?.value.trim();
        const selectedLogs = this.getSelectedLogs();

        if (!question) {
            alert('Please enter a question for analysis.');
            return;
        }

        if (selectedLogs.length === 0) {
            alert('Please select at least one log for analysis.');
            return;
        }

        try {
            this.showProgress();
            const data = await apiService.analysis.analyzeLogs(question, selectedLogs);
            this.showResults(data.analysis);
        } catch (error) {
            console.error('Error analyzing logs:', error);
            this.showError('Failed to analyze logs: ' + error.message);
        } finally {
            this.hideProgress();
        }
    }

    getSelectedLogs() {
        return Array.from(document.querySelectorAll('.log-checkbox:checked'))
            .map(checkbox => checkbox.value);
    }

    selectAllLogs() {
        document.querySelectorAll('.log-checkbox')
            .forEach(checkbox => checkbox.checked = true);
    }

    deselectAllLogs() {
        document.querySelectorAll('.log-checkbox')
            .forEach(checkbox => checkbox.checked = false);
    }

    async deleteSelectedLogs() {
        const selectedLogs = this.getSelectedLogs();
        
        if (selectedLogs.length === 0) {
            alert('Please select logs to delete.');
            return;
        }

        if (!confirm(`Are you sure you want to delete ${selectedLogs.length} log(s)?`)) {
            return;
        }

        try {
            await apiService.analysis.deleteLogs(selectedLogs);
            await this.fetchLogs(); // Refresh the list
            this.showSuccess(`Successfully deleted ${selectedLogs.length} log(s)`);
        } catch (error) {
            console.error('Error deleting logs:', error);
            this.showError('Failed to delete logs: ' + error.message);
        }
    }

    showProgress() {
        if (this.progressBar) {
            this.progressBar.style.display = 'block';
            this.progressBar.style.width = '0%';
            this.simulateProgress();
        }
        if (this.analyzeButton) {
            this.analyzeButton.disabled = true;
        }
    }

    hideProgress() {
        if (this.progressBar) {
            this.progressBar.style.display = 'none';
        }
        if (this.analyzeButton) {
            this.analyzeButton.disabled = false;
        }
    }

    simulateProgress() {
        let width = 0;
        const interval = setInterval(() => {
            if (!this.progressBar || width >= 90) {
                clearInterval(interval);
                return;
            }
            width += 5;
            this.progressBar.style.width = width + '%';
        }, 500);
    }

    showResults({ response, advice }) {
        if (!this.resultsContainer) return;
    
        // Set the result container's class and visibility
        this.resultsContainer.className = 'status-message status-success';
        this.resultsContainer.style.display = 'block';
    
        // Construct the HTML for results and advice
        this.resultsContainer.innerHTML = `
            <strong>Analysis Results:</strong>
            <pre>${response}</pre>
            <strong>Next Steps:</strong>
            <ul>
                ${advice.map(step => `<li>${step}</li>`).join('')}
            </ul>
        `;
    }

    showError(message) {
        if (!this.resultsContainer) return;

        this.resultsContainer.className = 'status-message status-error';
        this.resultsContainer.innerHTML = `<strong>Error:</strong> ${message}`;
        this.resultsContainer.style.display = 'block';
    }

    showSuccess(message) {
        if (!this.resultsContainer) return;

        this.resultsContainer.className = 'status-message status-success';
        this.resultsContainer.innerHTML = `<strong>Success:</strong> ${message}`;
        this.resultsContainer.style.display = 'block';
    }
}

// Initialize the LogAnalyzer when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LogAnalyzer();
});

// Export the class for potential use in other modules
export { LogAnalyzer };
