let live = true;
const chartTypeSelector = document.getElementById('chartType');
const toggleBtn = document.getElementById('toggle');
const ctx1 = document.getElementById('chart1').getContext('2d');
const ctx2 = document.getElementById('chart2').getContext('2d');
const ctx3 = document.getElementById('chart3').getContext('2d');

const behaviorData = [];
const behaviorLabels = [];
let lastMotionChange = null;

const chart1 = new Chart(ctx1, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Accel X', data: [], borderColor: '#ef4444', fill: false },
      { label: 'Accel Y', data: [], borderColor: '#22c55e', fill: false },
      { label: 'Accel Z', data: [], borderColor: '#3b82f6', fill: false }
    ]
  },
  options: defaultChartOptions()
});

const chart2 = new Chart(ctx2, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Gyro X', data: [], borderColor: '#eab308', fill: false },
      { label: 'Gyro Y', data: [], borderColor: '#10b981', fill: false },
      { label: 'Gyro Z', data: [], borderColor: '#6366f1', fill: false }
    ]
  },
  options: defaultChartOptions()
});

const chart3 = new Chart(ctx3, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Variance Z', data: [], borderColor: '#f59e0b', fill: false }
    ]
  },
  options: defaultChartOptions()
});

function defaultChartOptions() {
  return {
    responsive: true,
    animation: false,
    plugins: { legend: { labels: { color: '#f1f5f9' } } },
    scales: {
      x: { ticks: { color: '#f1f5f9' } },
      y: { beginAtZero: false, ticks: { color: '#f1f5f9' } }
    }
  };
}

function updateBehavior(behavior) {
  const index = behaviorLabels.indexOf(behavior);
  if (index === -1) {
    behaviorLabels.push(behavior);
    behaviorData.push(1);
  } else {
    behaviorData[index]++;
  }
  // Optionally chart behavior counts here in the future
}

toggleBtn.onclick = () => {
  live = !live;
  toggleBtn.textContent = live ? "Pause" : "Resume";
};

chartTypeSelector.onchange = () => {
  // Optionally implement chart switching in future versions
};

async function updateData() {
  if (!live) return;
  try {
    const res = await fetch('/data');
    const data = await res.json();
    const now = new Date().toLocaleTimeString();

    const { motion, summary, accel, gyro } = data;

    document.getElementById("motion").textContent = motion;
    document.getElementById("behavior").textContent = summary.behavior;
    document.getElementById("walking").textContent = summary.walking ? 'Yes' : 'No';
    document.getElementById("varz").textContent = summary.variance_z.toFixed(4);
    document.getElementById("status-time").textContent = now;

    // Update raw sensor data boxes
    document.getElementById("accel_x").textContent = accel.x.toFixed(2);
    document.getElementById("accel_y").textContent = accel.y.toFixed(2);
    document.getElementById("accel_z").textContent = accel.z.toFixed(2);
    document.getElementById("gyro_x").textContent = gyro.x.toFixed(2);
    document.getElementById("gyro_y").textContent = gyro.y.toFixed(2);
    document.getElementById("gyro_z").textContent = gyro.z.toFixed(2);

    // Chart updates
    [chart1, chart2, chart3].forEach(chart => {
      chart.data.labels.push(now);
    });
    chart1.data.datasets[0].data.push(accel.x);
    chart1.data.datasets[1].data.push(accel.y);
    chart1.data.datasets[2].data.push(accel.z);
    chart2.data.datasets[0].data.push(gyro.x);
    chart2.data.datasets[1].data.push(gyro.y);
    chart2.data.datasets[2].data.push(gyro.z);
    chart3.data.datasets[0].data.push(summary.variance_z);

    [chart1, chart2, chart3].forEach(chart => {
      if (chart.data.labels.length > 30) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(d => d.data.shift());
      }
      chart.update();
    });

    const logRow = document.createElement("tr");
    logRow.innerHTML = `<td>${now}</td><td>${motion}</td><td>${summary.behavior}</td><td>${summary.walking ? 'Yes' : 'No'}</td><td>${summary.variance_z.toFixed(4)}</td>`;
    const logBody = document.getElementById("logBody");
    logBody.prepend(logRow);
    if (logBody.children.length > 10) {
      logBody.removeChild(logBody.lastChild);
    }

    if (motion !== 'Stable') {
      lastMotionChange = new Date();
    }
    if (lastMotionChange) {
      document.getElementById("last-move").textContent = lastMotionChange.toLocaleTimeString();
    }

    updateBehavior(summary.behavior);
  } catch (err) {
    console.error("Data fetch error", err);
  }
}

setInterval(updateData, 500);
setInterval(() => {
  document.getElementById("status-time").textContent = new Date().toLocaleTimeString();
}, 1000);
