import { apiService } from './api-service.js';

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const logListContainer = document.getElementById('log-list');
    const questionInput = document.getElementById('llm-question');
    const submitButton = document.getElementById('submit-question');
    const progressContainer = document.getElementById('analysis-progress');
    const progressBar = progressContainer.querySelector('.progress');
    const progressStatus = document.getElementById('progress-status');
    const resultsContainer = document.getElementById('analysis-results');
    const responseElement = document.getElementById('llm-response');
    const llmStatus = document.getElementById('llm-status');
    const metadataContent = document.getElementById('metadata-content');
    const errorDiv = document.getElementById('analysis-error');

    let analysisStartTime;

    // Function to extract and format the LLM response
    function formatLLMResponse(text) {
        // Remove any JSON or raw data before "Answer:"
        const cleanText = text.replace(/^[\s\S]*?(?=Answer:)/g, '');
        
        // Split the response into sections
        const sections = {
            answer: '',
            explanation: '',
            tips: ''
        };

        // Extract Answer section
        const answerMatch = cleanText.match(/Answer:(.*?)(?=Detailed Explanation:|$)/s);
        if (answerMatch) sections.answer = answerMatch[1].trim();

        // Extract Detailed Explanation section
        const explanationMatch = cleanText.match(/Detailed Explanation:(.*?)(?=Practical Tips:|$)/s);
        if (explanationMatch) sections.explanation = explanationMatch[1].trim();

        // Extract Practical Tips section
        const tipsMatch = cleanText.match(/Practical Tips:(.*?)$/s);
        if (tipsMatch) sections.tips = tipsMatch[1].trim();

        // Create formatted HTML
        return `
            <div class="response-section">
                <h3>Answer</h3>
                <p>${sections.answer}</p>
            </div>
            ${sections.explanation ? `
                <div class="response-section">
                    <h3>Detailed Explanation</h3>
                    <p>${sections.explanation}</p>
                </div>
            ` : ''}
            ${sections.tips ? `
                <div class="response-section">
                    <h3>Practical Tips</h3>
                    <p>${sections.tips}</p>
                </div>
            ` : ''}
        `;
    }

    // Update step history in UI
    function updateStepHistory(step) {
        const history = document.getElementById('step-history');
        const currentStepValue = document.querySelector('.step-value');
        
        if (currentStepValue.textContent !== 'Initializing...') {
            const historyItem = document.createElement('div');
            historyItem.className = 'completed-step';
            historyItem.innerHTML = `
                <div class="step-indicator"></div>
                <div class="step-content">
                    <span class="step-value">${currentStepValue.textContent}</span>
                </div>
            `;
            history.insertBefore(historyItem, history.firstChild);
        }
        
        currentStepValue.textContent = step;
    }

    // Update progress status
    async function updateProgressStatus(status, percentage) {
        progressStatus.textContent = status;
        progressBar.style.width = `${percentage}%`;
        updateStepHistory(status);
    }

    // Fetch and display logs
    async function fetchAndDisplayLogs() {
        try {
            const data = await apiService.analysis.getLogs();
            if (!data.logs || data.logs.length === 0) {
                logListContainer.innerHTML = '<p>No logs available for analysis.</p>';
                return;
            }

            logListContainer.innerHTML = data.logs
                .map((log, index) => `
                    <div class="log-item">
                        <input type="checkbox" id="log-${index}" value="${log.name}" class="log-checkbox">
                        <label for="log-${index}" class="log-label">
                            ${log.name} (${(log.size / 1024).toFixed(2)} KB)
                        </label>
                    </div>
                `)
                .join('');

            document.getElementById('log-count').textContent = `${data.logs.length} logs found`;
            
            // Update LLM initialization status
            document.getElementById('llm-initialization-status').querySelector('.status-value')
                .textContent = 'Ready';
        } catch (error) {
            console.error('Error fetching logs:', error);
            logListContainer.innerHTML = '<p>Error loading logs.</p>';
        }
    }

    // Submit analysis
    async function submitAnalysis() {
        const question = questionInput.value.trim();
        const selectedLogs = Array.from(document.querySelectorAll('.log-checkbox:checked'))
            .map(cb => cb.value);
        
        errorDiv.style.display = 'none';
        
        if (!question || selectedLogs.length === 0) {
            errorDiv.style.display = 'block';
            errorDiv.textContent = !question 
                ? 'Please enter a question for analysis.' 
                : 'Please select at least one log for analysis.';
            return;
        }
    
        try {
            console.group('LLM Analysis Request');
            console.time('Total Analysis Time');
            console.log('Question:', question);
            console.log('Selected Logs:', selectedLogs);
    
            submitButton.disabled = true;
            llmStatus.style.display = 'block';
            progressContainer.style.display = 'block';
            resultsContainer.style.display = 'none';
            analysisStartTime = Date.now();
            
            document.getElementById('step-history').innerHTML = '';
    
            const steps = [
                ['Initializing LLM model and configuration', 5],
                ['Verifying model parameters', 15],
                ['Loading selected logs', 30],
                ['Processing log content', 45],
                ['Running tokenization', 60],
                ['Executing LLM analysis', 75]
            ];
    
            for (const [step, percentage] of steps) {
                console.log(`Step: ${step} (${percentage}%)`);
                await updateProgressStatus(`${step}...`, percentage);
                await new Promise(resolve => setTimeout(resolve, 800));
            }
    
            try {
                console.log('Sending API request...');
                const response = await apiService.analysis.analyzeLLM({
                    question: question,
                    logs: selectedLogs
                });
    
                console.group('API Response');
                console.log('Status:', response.status);
                console.log('Metadata:', response.metadata);
                console.log('Response Length:', response.response?.length || 0);
                console.groupEnd();
    
                if (response.status === 'success') {
                    console.log('Processing successful response');
                    await updateProgressStatus('Processing results...', 90);
                    
                    const generationTime = ((Date.now() - analysisStartTime) / 1000).toFixed(2);
                    console.log('Generation Time:', generationTime, 'seconds');
                    
                    document.getElementById('device-type').textContent = response.metadata.device || 'CPU';
                    document.getElementById('generation-time').textContent = `${generationTime}s`;
                    document.getElementById('input-tokens').textContent = response.metadata.input_length || '0';
                    document.getElementById('output-tokens').textContent = response.metadata.output_length || '0';
                    
                    document.getElementById('token-stats').style.display = 'block';
                    document.getElementById('performance-stats').style.display = 'block';
                    
                    resultsContainer.style.display = 'block';
                    responseElement.innerHTML = formatLLMResponse(response.response);
                    responseElement.classList.remove('error');
                    
                    metadataContent.innerHTML = `Model Configuration:
    • Temperature: ${response.metadata.temperature}
    • Top-p: ${response.metadata.top_p}
    • Device: ${response.metadata.device}
    • Generation Time: ${generationTime} seconds
    
    Token Usage:
    • Input Length: ${response.metadata.input_length} tokens
    • Output Length: ${response.metadata.output_length} tokens`;
                } else {
                    throw new Error(response.error || 'Analysis failed');
                }
            } catch (error) {
                console.error('API Error:', error);
                throw new Error(`API Error: ${error.message}`);
            }
    
            console.timeEnd('Total Analysis Time');
            console.groupEnd();
    
        } catch (error) {
            console.error('Analysis Error:', error);
            errorDiv.style.display = 'block';
            errorDiv.textContent = error.message;
            progressContainer.style.display = 'none';
        } finally {
            submitButton.disabled = false;
        }
    }

    // Event Listeners
    submitButton.addEventListener('click', submitAnalysis);
    
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            submitAnalysis();
        }
    });

    // Log selection helpers
    window.selectAllLogs = () => {
        document.querySelectorAll('.log-checkbox').forEach(cb => cb.checked = true);
    };
    
    window.deselectAllLogs = () => {
        document.querySelectorAll('.log-checkbox').forEach(cb => cb.checked = false);
    };

    // Initialize
    fetchAndDisplayLogs();
});