import { apiService } from './api-service.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeSystemStatus();
});

async function initializeSystemStatus() {
    await fetchSystemStatus();
    setInterval(fetchSystemStatus, 5000); // Update every 5 seconds
}

async function fetchSystemStatus() {
    try {
        const data = await apiService.system.getStatus();
        if (data.status === 'success') {
            const info = data.system_info;
            
            // Update basic metrics
            updateMetric('cpu-usage', info.cpu_usage);
            updateMetric('memory-usage', info.memory_usage);
            updateMetric('disk-usage', info.disk_usage);
            updateMetric('system-uptime', info.uptime);
            
            // Update progress bars
            updateProgressBar('cpu-progress', parseFloat(info.cpu_usage));
            updateProgressBar('memory-progress', parseFloat(info.memory_usage));
            updateProgressBar('disk-progress', parseFloat(info.disk_usage));
            
            // Update detailed info if available
            if (info.detailed_memory) {
                document.querySelector('.memory-details')?.setAttribute('title', 
                    `Total: ${info.detailed_memory.total}\n` +
                    `Used: ${info.detailed_memory.used}\n` +
                    `Available: ${info.detailed_memory.available}`
                );
            }
            
            if (info.detailed_disk) {
                document.querySelector('.disk-details')?.setAttribute('title',
                    `Total: ${info.detailed_disk.total}\n` +
                    `Used: ${info.detailed_disk.used}\n` +
                    `Free: ${info.detailed_disk.free}`
                );
            }
        }
    } catch (error) {
        console.error('Error fetching system status:', error);
        fallbackErrorState();
    }
}

function updateMetric(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || 'Unavailable';
    }
}


function updateProgressBar(elementId, value) {
    const progressBar = document.getElementById(elementId);
    if (progressBar) {
        progressBar.style.width = `${value}%`;
        progressBar.style.backgroundColor = getProgressColor(value);
    }
}

function getProgressColor(value) {
    if (value < 70) return 'var(--success)';
    if (value < 90) return 'var(--warning)';
    return 'var(--danger)';
}

function fallbackErrorState() {
    ['cpu-usage', 'memory-usage', 'disk-usage', 'system-uptime'].forEach(id => {
        updateMetric(id, 'Error');
    });
}
async function fetchHealthIndicators() {
    try {
        // Fetch health indicators from the API
        const response = await fetch('/api/health-indicators');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
            const indicators = data.health_indicators;

            // Update SIP Status
            document.getElementById('sip-status').textContent = `SIP Status: ${indicators.sip_status}`;

            // Update Firewall Status
            document.getElementById('firewall-status-overview').textContent = `Firewall: ${indicators.firewall_status}`;

            // Update FileVault Status
            document.getElementById('filevault-status').textContent = `FileVault: ${indicators.filevault_status}`;

            // Update Threat Level
            document.getElementById('threat-level').textContent = `Threat Level: ${indicators.threat_level}`;
        } else {
            throw new Error(data.message || 'Failed to fetch health indicators');
        }
    } catch (error) {
        console.error('Error fetching health indicators:', error);

        // Display error messages in the DOM
        document.getElementById('sip-status').textContent = 'SIP Status: Error';
        document.getElementById('firewall-status-overview').textContent = 'Firewall: Error';
        document.getElementById('filevault-status').textContent = 'FileVault: Error';
        document.getElementById('threat-level').textContent = 'Threat Level: Error';
    }
}

// Call this function on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchHealthIndicators();
});
