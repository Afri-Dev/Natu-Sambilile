// Dashboard Charts - LearnHub Admin

document.addEventListener('DOMContentLoaded', function() {
  // Check if the enrollment chart container exists
  const enrollmentChartEl = document.getElementById('enrollmentChart');
  if (enrollmentChartEl) {
    initEnrollmentChart(enrollmentChartEl);
  }
  
  // Check if the course completion chart container exists
  const completionChartEl = document.getElementById('completionChart');
  if (completionChartEl) {
    initCompletionChart(completionChartEl);
  }
  
  // Check if categories chart exists
  const categoriesChartEl = document.getElementById('categoriesChart');
  if (categoriesChartEl) {
    initCategoriesChart(categoriesChartEl);
  }
});

function initEnrollmentChart(chartElement) {
  // Get the data from the data attribute if available
  let labels = [];
  let data = [];
  
  try {
    const monthlyData = JSON.parse(chartElement.dataset.enrollments || '[]');
    if (monthlyData && monthlyData.length) {
      // Data is available from backend
      labels = monthlyData.map(item => item.month);
      data = monthlyData.map(item => item.count);
    } else {
      // Fallback sample data
      labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      data = [65, 59, 80, 81, 56, 55, 40, 65, 59, 80, 81, 56];
    }
  } catch (e) {
    console.error('Error parsing enrollment data:', e);
    // Fallback sample data
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    data = [65, 59, 80, 81, 56, 55, 40, 65, 59, 80, 81, 56];
  }
  
  // Get chart colors based on the current theme
  const isDarkMode = document.documentElement.classList.contains('dark');
  const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
  const textColor = isDarkMode ? '#e5e7eb' : '#374151';
  
  // Initialize the chart
  const ctx = chartElement.getContext('2d');
  const gradientFill = ctx.createLinearGradient(0, 0, 0, chartElement.height);
  gradientFill.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
  gradientFill.addColorStop(1, 'rgba(59, 130, 246, 0.1)');
  
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Monthly Enrollments',
        data: data,
        backgroundColor: gradientFill,
        borderColor: '#3b82f6',
        borderWidth: 2,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
          titleColor: isDarkMode ? '#e5e7eb' : '#111827',
          bodyColor: isDarkMode ? '#d1d5db' : '#4b5563',
          borderColor: isDarkMode ? '#374151' : '#e5e7eb',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 6,
          displayColors: false,
          callbacks: {
            title: function(tooltipItems) {
              return tooltipItems[0].label;
            },
            label: function(context) {
              return 'Enrollments: ' + context.raw;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: textColor
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor,
            precision: 0
          }
        }
      }
    }
  });
  
  // Update chart on theme change
  document.addEventListener('themeChanged', () => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    chart.options.scales.x.ticks.color = isDarkMode ? '#e5e7eb' : '#374151';
    chart.options.scales.y.ticks.color = isDarkMode ? '#e5e7eb' : '#374151';
    chart.options.scales.y.grid.color = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    chart.update();
  });
}

function initCompletionChart(chartElement) {
  // Get the data from the data attribute if available
  let completionRate = 0;
  
  try {
    completionRate = parseFloat(chartElement.dataset.completion || 0);
  } catch (e) {
    console.error('Error parsing completion data:', e);
    completionRate = 75; // Fallback value
  }
  
  // Get chart colors based on the current theme
  const isDarkMode = document.documentElement.classList.contains('dark');
  
  // Initialize the chart
  const ctx = chartElement.getContext('2d');
  
  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Completed', 'Incomplete'],
      datasets: [{
        data: [completionRate, 100 - completionRate],
        backgroundColor: ['#10b981', isDarkMode ? '#1f2937' : '#e5e7eb'],
        borderWidth: 0,
        cutout: '75%',
        borderRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      }
    }
  });
  
  // Add completion text in the center
  Chart.register({
    id: 'completionText',
    beforeDraw: function(chart) {
      const width = chart.width;
      const height = chart.height;
      const ctx = chart.ctx;
      
      ctx.restore();
      ctx.font = 'bold 1.25rem sans-serif';
      ctx.fillStyle = isDarkMode ? '#e5e7eb' : '#111827';
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      
      const text = `${completionRate}%`;
      ctx.fillText(text, width / 2, height / 2);
      ctx.save();
    }
  });
  
  // Update chart on theme change
  document.addEventListener('themeChanged', () => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    chart.data.datasets[0].backgroundColor = ['#10b981', isDarkMode ? '#1f2937' : '#e5e7eb'];
    chart.update();
  });
}

function initCategoriesChart(chartElement) {
  // Get the data from the data attribute if available
  let labels = [];
  let data = [];
  
  try {
    const categoriesData = JSON.parse(chartElement.dataset.categories || '[]');
    if (categoriesData && categoriesData.length) {
      // Data is available from backend
      labels = categoriesData.map(item => item.name);
      data = categoriesData.map(item => item.count);
    } else {
      // Fallback sample data
      labels = ['Web Development', 'Data Science', 'Mobile Apps', 'UI/UX Design', 'DevOps'];
      data = [42, 35, 28, 21, 15];
    }
  } catch (e) {
    console.error('Error parsing categories data:', e);
    // Fallback sample data
    labels = ['Web Development', 'Data Science', 'Mobile Apps', 'UI/UX Design', 'DevOps'];
    data = [42, 35, 28, 21, 15];
  }
  
  // Get chart colors based on the current theme
  const isDarkMode = document.documentElement.classList.contains('dark');
  const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
  const textColor = isDarkMode ? '#e5e7eb' : '#374151';
  
  // Color palette for categories
  const colorPalette = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#f97316', // orange
    '#14b8a6', // teal
    '#ef4444', // red
    '#6366f1'  // indigo
  ];
  
  // Ensure we have enough colors for all categories
  while (colorPalette.length < labels.length) {
    colorPalette.push(...colorPalette);
  }
  
  // Initialize the chart
  const ctx = chartElement.getContext('2d');
  
  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Courses per Category',
        data: data,
        backgroundColor: colorPalette.slice(0, labels.length),
        borderRadius: 4,
        maxBarThickness: 40
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
          titleColor: isDarkMode ? '#e5e7eb' : '#111827',
          bodyColor: isDarkMode ? '#d1d5db' : '#4b5563',
          borderColor: isDarkMode ? '#374151' : '#e5e7eb',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 6,
          displayColors: true,
          callbacks: {
            label: function(context) {
              return `${context.raw} courses`;
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor,
            precision: 0
          }
        },
        y: {
          grid: {
            display: false
          },
          ticks: {
            color: textColor
          }
        }
      }
    }
  });
  
  // Update chart on theme change
  document.addEventListener('themeChanged', () => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    const newGridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const newTextColor = isDarkMode ? '#e5e7eb' : '#374151';
    
    chart.options.scales.x.ticks.color = newTextColor;
    chart.options.scales.y.ticks.color = newTextColor;
    chart.options.scales.x.grid.color = newGridColor;
    
    chart.options.plugins.tooltip.backgroundColor = isDarkMode ? '#1f2937' : '#ffffff';
    chart.options.plugins.tooltip.titleColor = isDarkMode ? '#e5e7eb' : '#111827';
    chart.options.plugins.tooltip.bodyColor = isDarkMode ? '#d1d5db' : '#4b5563';
    chart.options.plugins.tooltip.borderColor = isDarkMode ? '#374151' : '#e5e7eb';
    
    chart.update();
  });
} 