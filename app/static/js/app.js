document.addEventListener("DOMContentLoaded", function () {
  // Dark mode toggle
  const toggle = document.getElementById("darkModeToggle");
  const root = document.documentElement;
  const saved = sessionStorage.getItem("csss-theme");
  if (saved === "dark") root.setAttribute("data-theme", "dark");
  if (toggle) {
    toggle.checked = root.getAttribute("data-theme") === "dark";
    toggle.addEventListener("change", function () {
      if (toggle.checked) {
        root.setAttribute("data-theme", "dark");
        sessionStorage.setItem("csss-theme", "dark");
      } else {
        root.removeAttribute("data-theme");
        sessionStorage.setItem("csss-theme", "light");
      }
    });
  }

  // Auto-dismiss alerts
  document.querySelectorAll(".alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      if (alert) alert.close();
    }, 6000);
  });

  // Multi-file photo preview
  const photoInput = document.getElementById("photos");
  const previewWrap = document.getElementById("photoPreview");
  if (photoInput && previewWrap) {
    photoInput.addEventListener("change", function () {
      previewWrap.innerHTML = "";
      Array.from(photoInput.files).forEach(function (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const img = document.createElement("img");
          img.src = e.target.result;
          img.className = "rounded border me-2 mb-2";
          img.style.width = "90px";
          img.style.height = "110px";
          img.style.objectFit = "cover";
          previewWrap.appendChild(img);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Compare checkboxes -> enable compare button
  const compareForm = document.getElementById("compareForm");
  if (compareForm) {
    const checks = compareForm.querySelectorAll(".compare-check");
    const btn = document.getElementById("compareBtn");
    function updateBtn() {
      const checked = compareForm.querySelectorAll(".compare-check:checked");
      if (btn) {
        btn.disabled = checked.length < 2;
        btn.textContent = "Compare (" + checked.length + ")";
      }
    }
    checks.forEach((c) => c.addEventListener("change", updateBtn));
    updateBtn();
  }

  // Bootstrap tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach((el) => new bootstrap.Tooltip(el));
});
