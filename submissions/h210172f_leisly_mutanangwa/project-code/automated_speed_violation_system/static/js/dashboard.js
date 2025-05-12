// Dashboard functionality

// Global chart reference
let speedChart = null;

// Fetch speed data and update the dashboard
async function fetchSpeedData() {
  try {
    const response = await fetch('/api/speed-monitoring');
    const data = await response.json();

    if (data.error) {
      console.error("API Error:", data.error);
      return;
    }

    // Update summary
    document.getElementById('total-vehicles').textContent = data.total_vehicles;
    document.getElementById('average-speed').textContent = `${data.average_speed} km/h`;
    document.getElementById('maximum-speed').textContent = `${data.maximum_speed} km/h`;
    document.getElementById('speed-violations').textContent = data.total_violations;
    document.getElementById('speed-limit-info').textContent = `Based on ${data.speed_limit} km/h limit`;

    // Update violations breakdown
    document.getElementById('mild-violations').textContent = data.mild_violations;
    document.getElementById('moderate-violations').textContent = data.moderate_violations;
    document.getElementById('severe-violations').textContent = data.severe_violations;

    // Update table
    const tableBody = document.getElementById('violations-table');
    tableBody.innerHTML = ''; // Clear existing rows
    
    // Check if we have violations
    if (data.recent_violations.length === 0) {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td colspan="5" class="border px-4 py-4 text-center text-gray-500">No speed violations recorded</td>
      `;
      tableBody.appendChild(row);
    } else {
      // Add each violation to the table
      data.recent_violations.forEach((violation) => {
        const row = document.createElement('tr');
        
        // Determine row color based on speed (highlight severe violations)
        let rowClass = '';
        if (violation.speed > data.speed_limit * 1.25) {
          rowClass = 'bg-red-100';
        } else if (violation.speed > data.speed_limit * 1.1) {
          rowClass = 'bg-orange-50';
        }
        
        row.className = rowClass;
        row.innerHTML = `
          <td class="border px-4 py-2">${violation.id}</td>
          <td class="border px-4 py-2">${violation.vehicle}</td>
          <td class="border px-4 py-2">${violation.number_plate || 'Unknown'}</td>
          <td class="border px-4 py-2 font-semibold">${violation.speed} km/h</td>
          <td class="border px-4 py-2">${violation.timestamp}</td>
        `;
        tableBody.appendChild(row);
      });
    }

    // Update chart
    updateSpeedChart(data);
    
  } catch (error) {
    console.error('Error fetching speed data:', error);
  }
}

// Create/update speed distribution chart
function updateSpeedChart(data) {
  const ctx = document.getElementById('speed-chart').getContext('2d');
  
  // If we already have a chart, destroy it
  if (speedChart) {
    speedChart.destroy();
  }
  
  // Create speed ranges for the chart
  const speedLimit = data.speed_limit;
  const ranges = [
    `0-${speedLimit*0.5}`,
    `${speedLimit*0.5}-${speedLimit}`,
    `${speedLimit}-${speedLimit*1.1}`,
    `${speedLimit*1.1}-${speedLimit*1.25}`,
    `>${speedLimit*1.25}`
  ];
  
  // Counts will come from the API in the future
  // For now, let's simulate with violations data
  const counts = [
    data.total_vehicles - data.total_violations, // Below speed limit
    data.total_vehicles * 0.2, // Around speed limit
    data.mild_violations,
    data.moderate_violations,
    data.severe_violations
  ];
  
  // Create the chart
  speedChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ranges,
      datasets: [{
        label: 'Vehicle Count',
        data: counts,
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)', // Below limit - teal
          'rgba(54, 162, 235, 0.6)', // At limit - blue
          'rgba(255, 206, 86, 0.6)', // Mild violation - yellow
          'rgba(255, 159, 64, 0.6)', // Moderate - orange
          'rgba(255, 99, 132, 0.6)'  // Severe - red
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of Vehicles'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Speed Range (km/h)'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: `Speed Distribution (Limit: ${speedLimit} km/h)`
        },
        legend: {
          display: false
        }
      }
    }
  });
}

// Handle speed limit type change
async function changeSpeedLimit(limitType) {
  try {
    const response = await fetch('/api/speed-limit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ type: limitType })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Refresh data with new speed limit
      fetchSpeedData();
    } else {
      console.error('Failed to change speed limit:', data.error);
    }
  } catch (error) {
    console.error('Error changing speed limit:', error);
  }
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Fetch speed data on page load
  fetchSpeedData();
  
  // Set up speed limit selector
  const speedLimitSelector = document.getElementById('speed-limit-selector');
  speedLimitSelector.addEventListener('change', (e) => {
    changeSpeedLimit(e.target.value);
  });
  
  // Refresh data every 5 seconds
  setInterval(fetchSpeedData, 5000);
});