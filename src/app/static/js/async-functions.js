const BASE_URL = 'http://localhost:5002';

// Utility function for displaying errors
function displayError(message, containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="log-output error">Error: ${message}</div>`;
    }
}

// Execute a script by its key
export async function executeScript(scriptKey) {
    try {
        const button = document.getElementById(`${scriptKey}-button`);
        if (!button) throw new Error(`Button for scriptKey '${scriptKey}' not found.`);

        const originalText = button.textContent;
        button.style.backgroundColor = 'var(--warning)';
        button.textContent = `${originalText.split(' ')[0]} Running...`;

        const response = await fetch(`${BASE_URL}/api/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script: scriptKey }),
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        const resultsContainer = document.getElementById('scan-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="log-output">${result.output.replace(/\n/g, '<br>')}</div>`;
        }

        await fetchLogs();
        button.style.backgroundColor = 'var(--success)';
        button.textContent = `${originalText.split(' ')[0]} Complete`;
    } catch (error) {
        console.error(`Error executing script '${scriptKey}':`, error);

        const button = document.getElementById(`${scriptKey}-button`);
        if (button) {
            button.style.backgroundColor = 'var(--danger)';
            button.textContent = `${button.textContent.split(' ')[0]} Failed`;
        }

        const resultsContainer = document.getElementById('scan-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="log-output error">Error: ${error.message}</div>`;
        }
    }
}

// Fetch logs from the server
export async function fetchLogs() {
    try {
        const response = await fetch(`${BASE_URL}/api/get-logs`);
        if (!response.ok) {
            throw new Error(`Failed to fetch logs: ${response.statusText}`);
        }

        const data = await response.json();
        const logListContainer = document.getElementById('log-list');
        if (logListContainer) {
            logListContainer.innerHTML = '';

            data.logs.forEach((log, index) => {
                const logItem = document.createElement('div');
                logItem.classList.add('log-item');

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.classList.add('log-checkbox');
                checkbox.id = `log-${index}`;
                checkbox.value = log.name;

                const label = document.createElement('label');
                label.htmlFor = `log-${index}`;
                label.classList.add('log-label');
                label.textContent = `${log.name} (${log.size})`;

                logItem.appendChild(checkbox);
                logItem.appendChild(label);
                logListContainer.appendChild(logItem);
            });

            const logCount = document.getElementById('log-count');
            if (logCount) logCount.textContent = `${data.logs.length} logs found`;
        } else {
            console.warn("Log list container not found in the DOM.");
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
        displayError(error.message, 'log-list');
    }
}

// Select all logs
export function selectAllLogs() {
    try {
        document.querySelectorAll('.log-checkbox').forEach(checkbox => checkbox.checked = true);
    } catch (error) {
        console.error('Error selecting all logs:', error);
    }
}

// Deselect all logs
export function deselectAllLogs() {
    try {
        document.querySelectorAll('.log-checkbox').forEach(checkbox => checkbox.checked = false);
    } catch (error) {
        console.error('Error deselecting all logs:', error);
    }
}

// Fetch system status from the server
async function fetchSystemStatus() {
    try {
        const mockData = {
            status: 'success',
            system_info: {
                sip_status: 'Enabled',
                firewall_status: 'Active',
                filevault_status: 'Enabled',
            },
        };
        const data = mockData; // Replace API call temporarily
        console.log('Mock Data:', data);
        updateMetric('sip-status', data.system_info.sip_status);
        updateMetric('firewall-status-overview', data.system_info.firewall_status);
        updateMetric('filevault-status', data.system_info.filevault_status);
    } catch (error) {
        console.error('Error fetching mock data:', error);
        fallbackErrorState();
    }
}


// Fetch active connections
export async function fetchActiveConnections() {
    try {
        const response = await fetch(`${BASE_URL}/api/active-connections`);
        if (!response.ok) {
            throw new Error(`Failed to fetch active connections: ${response.statusText}`);
        }

        const data = await response.json();
        const activeConnections = document.getElementById('active-network-connections');
        if (activeConnections) {
            activeConnections.textContent = data.connections || 'No connections detected';
        }
    } catch (error) {
        console.error('Error fetching active connections:', error);
        displayError(error.message, 'active-network-connections');
    }
}

// Load security tasks into the container
export async function loadSecurityTasks() {
    try {
        const response = await fetch('/static/html/security-tasks.html');
        if (!response.ok) {
            throw new Error(`Failed to load security tasks: ${response.statusText}`);
        }

        const html = await response.text();
        const container = document.getElementById('security-tasks-container');
        if (container) {
            container.innerHTML = html;
            document.querySelectorAll('.button.secondary').forEach(button => {
                button.addEventListener('click', event => {
                    const scriptKey = button.id.replace('-button', '');
                    executeScript(scriptKey);
                });
            });
        } else {
            console.warn("Security tasks container not found in the DOM.");
        }
    } catch (error) {
        console.error('Error loading security tasks:', error);
        displayError(error.message, 'security-tasks-container');
    }
}
