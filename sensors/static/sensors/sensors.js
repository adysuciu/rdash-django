(function () {
  const shell = document.querySelector(".app-shell");
  const refreshSeconds = Number(shell.dataset.refreshSeconds || 60);
  const errorNode = document.querySelector("#sensor-error");

  const baseLayout = {
    autosize: true,
    margin: { t: 20, r: 20, b: 48, l: 52 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    font: { color: "#172033" },
    xaxis: {
      gridcolor: "#e8eef6",
      tickformat: "%H:%M",
      type: "date",
    },
    yaxis: { gridcolor: "#e8eef6", zeroline: false },
  };

  const config = {
    displayModeBar: false,
    responsive: true,
  };

  async function loadReadings() {
    const response = await fetch("/api/sensors/readings/");
    if (!response.ok) {
      throw new Error("Sensor readings could not be loaded.");
    }
    return response.json();
  }

  function drawCharts(readings) {
    const timestamps = readings.map((reading) => new Date(reading.recorded_at));
    const temperatures = readings.map((reading) => reading.temperature);
    const humidity = readings.map((reading) => reading.humidity);

    Plotly.newPlot(
      "temperature-chart",
      [
        {
          x: timestamps,
          y: temperatures,
          type: "scatter",
          mode: "lines+markers",
          line: { color: "#e4572e", width: 3 },
          marker: { color: "#f5a524", size: 7 },
          name: "Temperature",
          hovertemplate: "%{x|%Y-%m-%d %H:%M}<br>%{y:.2f} C<extra></extra>",
        },
      ],
      { ...baseLayout, yaxis: { ...baseLayout.yaxis, title: "C" } },
      config,
    );

    Plotly.newPlot(
      "humidity-chart",
      [
        {
          x: timestamps,
          y: humidity,
          type: "scatter",
          mode: "lines+markers",
          line: { color: "#168aad", width: 3 },
          marker: { color: "#34d399", size: 7 },
          name: "Humidity",
          hovertemplate: "%{x|%Y-%m-%d %H:%M}<br>%{y:.2f}%<extra></extra>",
        },
      ],
      { ...baseLayout, yaxis: { ...baseLayout.yaxis, title: "%" } },
      config,
    );
  }

  function showError(message) {
    if (!message) {
      errorNode.hidden = true;
      errorNode.textContent = "";
      return;
    }

    errorNode.hidden = false;
    errorNode.textContent = message;
  }

  async function refresh() {
    try {
      const payload = await loadReadings();
      showError(payload.error);
      drawCharts(payload.readings);
    } catch (error) {
      showError(error.message);
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    refresh();
    window.setInterval(refresh, refreshSeconds * 1000);
  });
})();
