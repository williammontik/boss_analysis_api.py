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
  <!-- (form contents unchanged) -->
  <!-- ... -->
</div>

<!-- 4) Spinner -->
<div id="loadingMessageBoss" style="display:none; text-align:center; margin-top:30px;">
  <!-- (spinner contents unchanged) -->
</div>

<!-- 5) Result -->
<div id="resultContainerBoss" style="display:none; margin-top:60px;">
  <!-- three-line gap above the header -->
  <br><br><br>
  <h4 style="text-align:center; font-size:28px; font-weight:bold; color:#5E9CA0; margin-bottom:20px;">
    🎉 AI Team Member Performance Insights:
  </h4>
  <!-- three-line gap below the header -->
  <br><br><br>
  <div id="bossResultContent" style="white-space:pre-wrap; font-size:16px; line-height:1.6;"></div>
  <div style="text-align:center; margin-top:20px;">
    <button id="resetButton" style="padding:14px; background:#2196F3; color:#fff; border:none; border-radius:10px; cursor:pointer;">
      🔄 Reset
    </button>
  </div>
</div>

<!-- 6) Script -->
<script>
document.addEventListener('DOMContentLoaded', () => {
  const simulateBtn = document.getElementById('simulateBossButton');
  const form = document.getElementById('bossForm');
  const pdpa = document.getElementById('pdpaCheckboxBoss');
  const spinner = document.getElementById('loadingMessageBoss');
  const resultDiv = document.getElementById('resultContainerBoss');
  const resultContent = document.getElementById('bossResultContent');

  // Enable form when PDPA is checked
  pdpa.addEventListener('change', () => {
    const fields = form.querySelectorAll('input, select, textarea, button[type="submit"]');
    fields.forEach(f => f.disabled = !pdpa.checked);
    form.style.opacity = pdpa.checked ? '1' : '0.3';
    form.style.pointerEvents = pdpa.checked ? 'auto' : 'none';
  });

  // Show form on Next
  simulateBtn.addEventListener('click', () => {
    document.getElementById('hiddenFormBoss').classList.add('show');
    document.getElementById('hiddenFormBoss').style.display = 'block';
  });

  // Populate DOB selects (unchanged)
  // ...

  form.addEventListener('submit', async e => {
    e.preventDefault();
    spinner.style.display = 'block';
    resultDiv.style.display = 'none';
    resultContent.innerHTML = '';

    const get = id => document.getElementById(id).value;
    const payload = { /* gather your form fields as before */ };

    try {
      const res = await fetch('https://boss-analysis-api.onrender.com/boss_analyze', {
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
      } else {
        resultContent.innerHTML = data.analysis;
      }
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
