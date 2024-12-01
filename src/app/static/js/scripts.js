// src/app/static/js/scripts.js

/**
 * scripts.js - Main JavaScript file for GuardStick Security Application
 */

import { initializeThemeToggle } from './theme-toggle.js';

// ==================================
// INITIALIZATION AND EVENT LISTENERS
// ==================================
document.addEventListener('DOMContentLoaded', () => {
    initializeThemeToggle();
    setupEventListeners();
    initializeDashboard();
    loadSecurityTasks();
    fetchLogs();
});

// ==================================
// DASHBOARD INITIALIZATION
// ==================================
const initializeDashboard = () => {
    // Start updating metrics
    updateSystemMetrics();
    setInterval(updateSystemMetrics, 5000);  // Update every 5 seconds

    // Update firewall status
    updateFirewallStatus();
    setInterval(updateFirewallStatus, 30000);  // Update every 30 seconds

    // Update security events
    updateSecurityEvents();
    setInterval(updateSecurityEvents, 60000);  // Update every minute

    // Initialize network monitoring
    initializeNetworkMonitoring();

    // Initialize security monitoring
    initializeSecurityMonitoring();

    // Set up refresh intervals for other components
    setInterval(updateSecurityEvents, 30000);
    setInterval(updateServiceStatus, 60000);
};

// ==================================
// SYSTEM METRICS MONITORING
// ==================================
const updateSystemMetrics = async () => {
    try {
        const response = await fetch('/api/system-status');
        const data = await response.json();

        if (data.status === 'success') {
            // Update CPU
            document.getElementById('cpu-usage').textContent = data.system_info.cpu_usage;
            document.getElementById('cpu-bar').style.width = data.system_info.cpu_usage;

            // Update Memory
            document.getElementById('memory-usage').textContent = data.system_info.memory_usage;
            document.getElementById('memory-bar').style.width = data.system_info.memory_usage;

            // Update Disk
            document.getElementById('disk-usage').textContent = data.system_info.disk_usage;
            document.getElementById('disk-bar').style.width = data.system_info.disk_usage;

            // Update Uptime
            document.getElementById('uptime').textContent = data.system_info.uptime;
        }
    } catch (error) {
        console.error('Error fetching system metrics:', error);
    }
};

// ==================================
// FIREWALL STATUS
// ==================================
const updateFirewallStatus = async () => {
    try {
        const response = await fetch('/api/check-firewall');
        const data = await response.json();

        const firewallStatus = document.getElementById('firewall-status');
        if (data.status === 'success') {
            firewallStatus.textContent = data.firewall_status;
            firewallStatus.className = `status-indicator status-${data.firewall_status.toLowerCase()}`;
        }
    } catch (error) {
        console.error('Error checking firewall:', error);
    }
};

// ==================================
// ACTIVE CONNECTIONS
// ==================================
const updateActiveConnections = async () => {
    try {
        const response = await fetch('/api/active-connections');
        const data = await response.json();

        if (data.status === 'success') {
            document.getElementById('active-connections').textContent = data.active_connections;
        }
    } catch (error) {
        console.error('Error fetching active connections:', error);
    }
};

// ==================================
// SECURITY EVENTS
// ==================================
const updateSecurityEvents = async () => {
    try {
        const response = await fetch('/api/security-events');
        const data = await response.json();
        const eventsContainer = document.getElementById('security-events');
        
        if (data.status === 'success') {
            if (data.events && data.events.length > 0) {
                eventsContainer.innerHTML = data.events.map(event => createEventElement(event)).join('');
            } else {
                eventsContainer.innerHTML = '<div class="no-events">No recent security events</div>';
            }
        }
    } catch (error) {
        console.error('Error fetching security events:', error);
    }
};

const createEventElement = (event) => {
    const severityClass = getSeverityClass(event.severity);
    const timeString = new Date(event.timestamp).toLocaleString();

    return `
        <div class="event-item ${severityClass}">
            <div class="event-time">${timeString}</div>
            <div class="event-type">${event.type}</div>
            <div class="event-message">${event.message}</div>
            ${event.details ? `<div class="event-details">${event.details}</div>` : ''}
        </div>
    `;
};

const getSeverityClass = (severity) => {
    switch (severity.toLowerCase()) {
        case 'critical': return 'severity-critical';
        case 'warning': return 'severity-warning';
        case 'info': return 'severity-info';
        default: return 'severity-normal';
    }
};

// ==================================
// NETWORK MONITORING
// ==================================
let networkChart;  // Chart.js instance

const initializeNetworkMonitoring = () => {
    const networkChartCtx = document.getElementById('network-chart');
    if (!networkChartCtx) return;

    networkChart = new Chart(networkChartCtx, {
        type: 'line',
        data: {
            labels: Array(30).fill(''),
            datasets: [
                {
                    label: 'Incoming Traffic (MB/s)',
                    data: Array(30).fill(0),
                    borderColor: '#3B82F6',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Outgoing Traffic (MB/s)',
                    data: Array(30).fill(0),
                    borderColor: '#10B981',
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'MB/s'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });

    // Start network monitoring loop
    updateNetworkChart();
    setInterval(() => updateNetworkChart(), 1000);
};

const updateNetworkChart = async () => {
    try {
        const response = await fetch('/api/system-status');  // Reusing system-status for example
        const data = await response.json();

        if (data.status === 'success' && networkChart) {
            // For demonstration, generate random data
            const incoming = (Math.random() * 100).toFixed(2);  // Replace with real data
            const outgoing = (Math.random() * 100).toFixed(2);  // Replace with real data

            networkChart.data.datasets[0].data.push(incoming);
            networkChart.data.datasets[0].data.shift();
            networkChart.data.datasets[1].data.push(outgoing);
            networkChart.data.datasets[1].data.shift();
            networkChart.update();
        }
    } catch (error) {
        console.error('Error updating network chart:', error);
    }
};

// ==================================
// SERVICES STATUS
// ==================================
const updateServiceStatus = async () => {
    try {
        const response = await fetch('/api/service-status');
        const data = await response.json();

        if (data.status === 'success') {
            const servicesContainer = document.getElementById('services-status');
            if (!servicesContainer) return;

            servicesContainer.innerHTML = data.services
                .map(service => createServiceElement(service))
                .join('');
        }
    } catch (error) {
        console.error('Error updating service status:', error);
    }
};

const createServiceElement = (service) => {
    const statusClass = service.status.toLowerCase() === 'running' ? 'status-running' : 'status-stopped';
    return `
        <div class="service-item ${statusClass}">
            <div class="service-name">${service.name}</div>
            <div class="service-status">
                <span class="status-indicator"></span>
                ${service.status}
            </div>
            <div class="service-uptime">${service.uptime}</div>
        </div>
    `;
};

// ==================================
// SECURITY TASKS
// ==================================
const setupEventListeners = () => {
    // Example: Handle security task execution buttons
    document.querySelectorAll('.security-task-card .button').forEach(button => {
        button.addEventListener('click', (e) => {
            const action = e.target.getAttribute('onclick');
            if (action) {
                const functionName = action.split('(')[0];
                const argument = action.split('(')[1].replace(')', '').replace(/'/g, '');
                if (typeof window[functionName] === 'function') {
                    window[functionName](argument);
                }
            }
        });
    });
};

const loadSecurityTasks = async () => {
    // Fetch available security tasks from the backend or define them here
    // For demonstration, this function can be left empty or used to dynamically load tasks
};

const fetchLogs = async () => {
    try {
        const response = await fetch('/api/get-logs');
        const data = await response.json();

        if (data.status === 'success') {
            populateLogSelect(data.logs);
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
};

const populateLogSelect = (logs) => {
    const logSelect = document.getElementById('log-select');
    if (!logSelect) return;

    logs.forEach(log => {
        const option = document.createElement('option');
        option.value = log.download_url.replace('/api/logs/download/', '');
        option.textContent = log.name;
        logSelect.appendChild(option);
    });
};

// ==================================
// ANALYZE LOGS
// ==================================
window.analyzeLogs = async () => {
    try {
        const question = document.getElementById('analysis-question').value.trim();
        const logSelect = document.getElementById('log-select');
        const selectedOptions = Array.from(logSelect.selectedOptions).map(option => option.value);

        if (!question) {
            alert('Please enter a question for analysis.');
            return;
        }

        if (selectedOptions.length === 0) {
            alert('Please select at least one log for analysis.');
            return;
        }

        const response = await fetch('/api/analyze-logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, logs: selectedOptions })
        });

        const data = await response.json();

        const analysisResult = document.getElementById('analysis-result');
        if (data.status === 'success') {
            analysisResult.className = 'status-message status-success';
            analysisResult.innerHTML = `<strong>Analysis:</strong><pre>${data.analysis}</pre>`;
        } else {
            analysisResult.className = 'status-message status-error';
            analysisResult.innerHTML = `<strong>Error:</strong> ${data.message}`;
        }
    } catch (error) {
        console.error('Error analyzing logs:', error);
    }
};
