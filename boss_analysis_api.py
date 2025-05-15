<!-- === START WIDGET FOR BOSS === -->

<!-- 1) Styles -->
<style>
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  #hiddenFormBoss {
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.5s ease, transform 0.5s ease;
  }
  #hiddenFormBoss.show {
    opacity: 1;
    transform: translateY(0);
  }
  #resultContainerBoss {
    opacity: 0;
    transition: opacity 0.5s ease;
  }
  #resultContainerBoss.show {
    opacity: 1;
  }
</style>

<!-- 2) Next Button -->
<button id="simulateBossButton"
        style="padding:10px 20px; background:#5E9CA0; color:#fff; border:none; border-radius:8px; cursor:pointer;">
  Next
</button>

<!-- 3) Hidden Form -->
<div id="hiddenFormBoss" style="display:none; margin-top:20px;">
  <div style="margin-bottom:20px; font-size:16px; line-height:1.6; background:#f9f9f9; padding:20px; border-radius:8px; border-left:6px solid #5E9CA0;">
    <p style="font-size:18px; font-weight:bold; color:#5E9CA0;">
      We're here to uplift workplace performance through real-world insights. 😊
    </p>
    <p style="font-size:16px; font-style:italic; color:#555;">
      Rest assured, all data will be processed securely under PDPA regulations in Singapore, Malaysia, and Taiwan.
    </p>
  </div>

  <!-- PDPA Checkbox -->
  <div style="margin-bottom:20px; display:flex; align-items:center; font-size:16px;">
    <input type="checkbox" id="pdpaCheckboxBoss" style="margin-right:10px;">
    <label for="pdpaCheckboxBoss">
      I agree to share my data as per PDPA regulations.
    </label>
  </div>

  <!-- The Form -->
  <form id="bossForm" method="POST"
        style="display:flex; flex-direction:column; gap:20px; pointer-events:none; opacity:0.3;">
    <input type="text" id="memberName" placeholder="👤 Team Member Name (legal)" required disabled style="padding:12px;">
    <input type="text" id="position" placeholder="🏢 Role / Position" required disabled style="padding:12px;">
    <input type="text" id="department" placeholder="📂 Department (optional)" disabled style="padding:12px;">
    <input type="number" id="experience" placeholder="📅 Years of Experience" required min="0" disabled style="padding:12px;">
    <select id="sector" required disabled style="padding:12px;">
      <option value="">📌 Select Sector</option>
      <option>Indoor – Admin / HR / Ops / Finance</option>
      <option>Indoor – Technical / Engineering / IT</option>
      <option>Outdoor – Sales / BD / Retail</option>
      <option>Outdoor – Servicing / Logistics / Fieldwork</option>
    </select>
    <textarea id="challenge" placeholder="⚠️ Key Challenge" maxlength="200" required disabled style="padding:12px;"></textarea>
    <input type="text" id="focus" placeholder="🎯 Preferred Focus (e.g. Communication, Leadership)" required disabled style="padding:12px;">
    <input type="email" id="email" placeholder="📧 Email Address" required disabled style="padding:12px;">
    <select id="country" required disabled style="padding:12px;">
      <option value="">🌍 Select Country</option>
      <option>Singapore</option>
      <option>Malaysia</option>
      <option>Taiwan</option>
    </select>
    <div style="display:flex; gap:10px;">
      <select id="dob_day" required disabled style="flex:1; padding:12px;"><option value="">Day</option></select>
      <select id="dob_month" required disabled style="flex:1; padding:12px;"><option value="">Month</option></select>
      <select id="dob_year" required disabled style="flex:1; padding:12px;"><option value="">Year</option></select>
    </div>
    <input type="text" id="referrer" placeholder="💬 Referrer (if any)" disabled style="padding:12px;">
    <button type="submit" id="submitButtonBoss" disabled
            style="padding:14px; background:#5E9CA0; color:#fff; border:none; border-radius:10px; cursor:pointer;">
      🚀 Submit
    </button>
  </form>
</div>

<!-- 4) Spinner -->
<div id="loadingMessageBoss" style="display:none; text-align:center; margin-top:30px;">
  <div style="width:60px; height:60px; border:6px solid #ccc; border-top:6px solid #5E9CA0; border-radius:50%; animation:spin 1s linear infinite; margin:0 auto;"></div>
  <p style="color:#5E9CA0; margin-top:10px;">🔄 Processing… please wait…</p>
</div>

<!-- 5) Result -->
<div id="resultContainerBoss" style="display:none; margin-top:20px;">
  <h4 style="text-align:center; font-size:28px; font-weight:bold; color:#5E9CA0;">
    🎉 AI Team Member Performance Insights:
  </h4>
  <div id="bossCharts" style="max-width:700px; margin:0 auto 30px;"></div>
  <div id="bossResultContent" style="white-space:pre-wrap; font-size:16px; line-height:1.6;"></div>
  <div style="text-align:center; margin-top:20px;">
    <button id="resetButton" style="padding:14px; background:#2196F3; color:#fff; border:none; border-radius:10px; cursor:pointer;">
      🔄 Reset
    </button>
  </div>
</div>

<!-- 6) Chart.js + Script -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', () => {
  const simulateBtn = document.getElementById('simulateBossButton');
  simulateBtn.style.display = 'none';
  setTimeout(() => simulateBtn.style.display = 'inline-block', 30000);

  const form = document.getElementById('bossForm');
  const pdpa = document.getElementById('pdpaCheckboxBoss');
  const resultDiv = document.getElementById('resultContainerBoss');
  const spinner = document.getElementById('loadingMessageBoss');
  const chartsDiv = document.getElementById('bossCharts');
  const resultContent = document.getElementById('bossResultContent');

  pdpa.addEventListener('change', () => {
    const fields = form.querySelectorAll('input, select, textarea, button[type="submit"]');
    fields.forEach(f => f.disabled = !pdpa.checked);
    form.style.opacity = pdpa.checked ? '1' : '0.3';
    form.style.pointerEvents = pdpa.checked ? 'auto' : 'none';
  });

  simulateBtn.addEventListener('click', () => {
    document.getElementById('hiddenFormBoss').classList.add('show');
    document.getElementById('hiddenFormBoss').style.display = 'block';
  });

  const daySel = document.getElementById('dob_day');
  for (let d = 1; d <= 31; d++) daySel.innerHTML += `<option>${d}</option>`;
  const monthSel = document.getElementById('dob_month');
  ["January","February","March","April","May","June","July","August","September","October","November","December"]
    .forEach(m => monthSel.innerHTML += `<option>${m}</option>`);
  const yearSel = document.getElementById('dob_year');
  const thisYear = new Date().getFullYear();
  for (let y = thisYear - 65; y <= thisYear - 18; y++) yearSel.innerHTML += `<option>${y}</option>`;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    spinner.style.display = 'block';
    resultDiv.style.display = 'none';
    chartsDiv.innerHTML = '';
    resultContent.innerHTML = '';

    const get = id => document.getElementById(id).value;
    const payload = {
      memberName: get('memberName'),
      position: get('position'),
      department: get('department'),
      experience: get('experience'),
      sector: get('sector'),
      challenge: get('challenge'),
      focus: get('focus'),
      email: get('email'),
      country: get('country'),
      dob_day: get('dob_day'),
      dob_month: get('dob_month'),
      dob_year: get('dob_year'),
      referrer: get('referrer')
    };

    try {
      const res = await fetch('https://name-analysis-api-cdvl.onrender.com/boss_analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      spinner.style.display = 'none';
      resultDiv.style.display = 'block';
      requestAnimationFrame(() => resultDiv.classList.add('show'));

      if (data.error) {
        resultContent.innerHTML = '<p style="color:red;">⚠️ ' + data.error + '</p>';
        return;
      }

      data.metrics.forEach((m, idx) => {
        const c = document.createElement('canvas');
        c.height = 260;
        chartsDiv.appendChild(c);
        const ctx = c.getContext('2d');
        const palette = ['#5E9CA0', '#FF9F40', '#9966FF'];

        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: m.labels,
            datasets: [{
              label: m.title,
              data: m.values,
              backgroundColor: palette,
              borderColor: palette,
              borderWidth: 2,
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            plugins: {
              title: { display: true, text: m.title, font: { size: 18 } },
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                ticks: { stepSize: 20 },
                grid: { color: '#f0f0f0' }
              }
            }
          }
        });
      });

      resultContent.innerHTML = data.analysis;

    } catch (err) {
      console.error(err);
      spinner.style.display = 'none';
      resultDiv.style.display = 'block';
      resultContent.innerHTML = '<p style="color:red;">⚠️ Network/server error – check console.</p>';
    }
  });

  document.getElementById('resetButton').addEventListener('click', () => location.reload());
});
</script>

<!-- === END WIDGET FOR BOSS === -->
