document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById('waterCanvas');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
  
    let waterLevel = 0.7;
    let waveOffset = 0;
  
    function drawWaterWave(level, offset) {
        ctx.clearRect(0, 0, width, height);
      
        // Tank shape (rounded top & bottom)
        const radius = 20;
      
        ctx.save(); // Save canvas state for clipping
      
        // Create rounded tank shape
        ctx.beginPath();
        ctx.moveTo(radius, 0);
        ctx.lineTo(width - radius, 0);
        ctx.quadraticCurveTo(width, 0, width, radius);
        ctx.lineTo(width, height - radius);
        ctx.quadraticCurveTo(width, height, width - radius, height);
        ctx.lineTo(radius, height);
        ctx.quadraticCurveTo(0, height, 0, height - radius);
        ctx.lineTo(0, radius);
        ctx.quadraticCurveTo(0, 0, radius, 0);
        ctx.closePath();
      
        // Clip the wave inside the tank
        ctx.clip();
      
        // Draw background inside tank
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, width, height);
      
        // Wave parameters
        const amplitude = 10;
        const frequency = 0.05;
        const waterHeight = height * (1 - level);
      
        // Draw water wave
        ctx.beginPath();
        ctx.moveTo(0, height);
        for (let x = 0; x <= width; x++) {
          const y = amplitude * Math.sin(frequency * x + offset) + waterHeight;
          ctx.lineTo(x, y);
        }
        ctx.lineTo(width, height);
        ctx.closePath();
      
        // Wave gradient
        const gradient = ctx.createLinearGradient(0, waterHeight, 0, height);
        gradient.addColorStop(0, '#00bfff');
        gradient.addColorStop(1, '#0066cc');
        ctx.fillStyle = gradient;
        ctx.fill();
      
        ctx.restore(); // Restore state (unclip)
      
        // Tank outline
        ctx.strokeStyle = '#999';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(radius, 0);
        ctx.lineTo(width - radius, 0);
        ctx.quadraticCurveTo(width, 0, width, radius);
        ctx.lineTo(width, height - radius);
        ctx.quadraticCurveTo(width, height, width - radius, height);
        ctx.lineTo(radius, height);
        ctx.quadraticCurveTo(0, height, 0, height - radius);
        ctx.lineTo(0, radius);
        ctx.quadraticCurveTo(0, 0, radius, 0);
        ctx.closePath();
        ctx.stroke();
      
        // Water level label
        ctx.fillStyle = '#000';
        ctx.font = '20px Arial';
        ctx.fillText(`Level: ${(level * 100).toFixed(0)}%`, 20, 30);
      }
      
      
  
    function animate() {
      waveOffset += 0.08;
      drawWaterWave(waterLevel, waveOffset);
      requestAnimationFrame(animate);
    }
  
    animate();
  
    function updateWaterLevel() {
      fetch('/api/get-latest-water-level/')
        .then((res) => res.json())
        .then((data) => {
          if (data.water_level !== undefined) {
            waterLevel = Math.min(Math.max(data.water_level / 100, 0), 1);
          }
        })
        .catch((err) => {
          console.error('Failed to fetch water level:', err);
        });
    }
  
    setInterval(updateWaterLevel, 2000);
  });
  