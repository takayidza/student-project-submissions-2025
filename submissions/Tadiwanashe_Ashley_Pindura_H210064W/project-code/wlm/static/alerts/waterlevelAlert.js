let lastAlertState = null;         // Track critical states: 'low', 'high', or null
let flashingInterval = null;       // Interval for flashing alert
let checkingInterval = null;      // Regular water level checks
let alertTimer = null;             // To handle 1-minute re-alerts

async function checkWaterLevel() {
  try {
    const response = await fetch('/api/get-latest-water-level/');
    const data = await response.json();

    if (data.error) {
      console.warn('No water data yet');
      return;
    }

    const waterLevel = data.water_level;
    console.log('Water level:', waterLevel);

    if (waterLevel < 20) {
      handleFlashingAlert('low', '⚠️ Water level is too low!');
    } else if (waterLevel > 80) {
      handleFlashingAlert('high', '⚠️ Water level is too high!');
    } else {
      stopFlashingAlert();
    }
  } catch (error) {
    console.error('Error fetching water data:', error);
  }
}

function handleFlashingAlert(state, message) {
  if (lastAlertState !== state) {
    lastAlertState = state;
    startFlashing(message);
  }
}

function startFlashing(message) {
  stopFlashingAlert();  // Stop any previously running flashing alert

  flashingInterval = setInterval(() => {
    Swal.fire({
      title: 'ALERT!',
      text: message,
      icon: 'warning',
      showConfirmButton: true,
      confirmButtonText: 'OK',
      customClass: { confirmButton: 'btn btn-danger' },  // Optional: Customize button style
      buttonsStyling: false,
      timer: 0,  // Do not auto-close the alert
      allowOutsideClick: false,  // Disable closing by clicking outside the alert
      allowEscapeKey: false      // Disable closing with ESC key
    }).then((result) => {
      if (result.isConfirmed) {
        stopFlashingAlert();  // Stop flashing when user clicks OK
      }
    });
  }, 1000);  // Flash every second
}

function stopFlashingAlert() {
  if (flashingInterval) {
    clearInterval(flashingInterval);  // Stop flashing interval
    flashingInterval = null;
    lastAlertState = null;
    Swal.close();  // Close any open alerts immediately
  }
  if (alertTimer) {
    clearTimeout(alertTimer);  // Cancel re-alert timer if the alert is dismissed
    alertTimer = null;
  }
}

function scheduleReAlert() {
  if (alertTimer) {
    clearTimeout(alertTimer);  // Clear any existing re-alert
  }
  
  alertTimer = setTimeout(async () => {
    try {
      const response = await fetch('/api/get-latest-water-level/');
      const data = await response.json();

      if (data.error) {
        console.warn('No water data yet for re-alert');
      } else {
        const waterLevel = data.water_level;
        if (waterLevel < 20 || waterLevel > 80) {
          // Re-alert after 1 minute if still critical
          startFlashing(waterLevel < 20 ? '⚠️ Water level is too low!' : '⚠️ Water level is too high!');
        } else {
          stopFlashingAlert();  // Stop alert if back to normal range
        }
      }
    } catch (error) {
      console.error('Error fetching water data for re-alert:', error);
    }
  }, 60000);  // 1 minute interval for re-alert
}

// Start the loop to check water level every 10 seconds (or adjust as needed)
checkingInterval = setInterval(checkWaterLevel, 10000);
