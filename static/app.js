const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const monthSelect = document.getElementById("monthSelect");
const yearSelect = document.getElementById("yearSelect");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const downloadBtn = document.getElementById("downloadBtn");
const sampleBtn = document.getElementById("sampleBtn");
const wipeBtn = document.getElementById("wipeBtn");
const uploadStatus = document.getElementById("uploadStatus");
const rowCount = document.getElementById("rowCount");
const tbody = document.querySelector("#studentsTable tbody");

const filterName = document.getElementById("filterName");
const filterRoll = document.getElementById("filterRoll");
const filterBatch = document.getElementById("filterBatch");
const filterSemester = document.getElementById("filterSemester");
const filterStatus = document.getElementById("filterStatus");

let fullData = [];

// Populate Month/Year dropdowns
function initDateSelects() {
  MONTH_NAMES.forEach((name, i) => {
    const opt = document.createElement("option");
    opt.value = String(i + 1);
    opt.textContent = name;
    monthSelect.appendChild(opt);
  });
  const now = new Date();
  const currentYear = now.getFullYear();
  for (let y = currentYear - 2; y <= currentYear + 2; y++) {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    yearSelect.appendChild(opt);
  }
  monthSelect.value = String(now.getMonth() + 1);
  yearSelect.value = String(currentYear);
}

async function loadBatches() {
  const res = await fetch("/api/batches");
  const { batches, semesters } = await res.json();
  // Reset to just the "All" option so repeated calls don't duplicate entries
  filterBatch.innerHTML = '<option value="">All Batches</option>';
  filterSemester.innerHTML = '<option value="">All Semesters</option>';
  batches.forEach(b => {
    const o = document.createElement("option");
    o.value = b; o.textContent = b;
    filterBatch.appendChild(o);
  });
  semesters.forEach(s => {
    const o = document.createElement("option");
    o.value = s; o.textContent = s;
    filterSemester.appendChild(o);
  });
}

async function loadStudents() {
  const m = monthSelect.value;
  const y = yearSelect.value;
  const res = await fetch(`/api/students?month=${m}&year=${y}`);
  if (!res.ok) {
    rowCount.textContent = "Error loading students.";
    return;
  }
  fullData = await res.json();
  render();
}

function getFiltered() {
  const nameQ = filterName.value.trim().toLowerCase();
  const rollQ = filterRoll.value.trim().toLowerCase();
  const batchQ = filterBatch.value;
  const semQ = filterSemester.value;
  const statusQ = filterStatus.value;

  return fullData.filter(r => {
    if (nameQ && !r.name.toLowerCase().includes(nameQ)) return false;
    if (rollQ && !r.roll_number.toLowerCase().includes(rollQ)) return false;
    if (batchQ && r.batch_name !== batchQ) return false;
    if (semQ && r.semester !== semQ) return false;
    if (statusQ && r.status !== statusQ) return false;
    return true;
  });
}

function render() {
  const rows = getFiltered();
  tbody.innerHTML = "";
  updateStats(rows);

  const emptyState = document.getElementById("emptyState");
  if (emptyState) emptyState.hidden = fullData.length > 0;

  for (const r of rows) {
    const tr = document.createElement("tr");
    if (r.status === "Unpaid") tr.classList.add("defaulter");
    tr.innerHTML = `
      <td>${escapeHtml(r.name)}</td>
      <td>${escapeHtml(r.roll_number)}</td>
      <td>${escapeHtml(r.batch_name)}</td>
      <td>${escapeHtml(r.semester)}</td>
      <td><span class="status-badge ${r.status === "Paid" ? "paid" : "unpaid"}">${r.status}</span></td>
      <td>${r.amount_paid != null ? r.amount_paid.toFixed(2) : "—"}</td>
      <td>${formatDate(r.payment_date) || "—"}</td>
      <td><button class="row-delete" data-id="${r.student_id}" title="Delete student">🗑</button></td>
    `;
    tbody.appendChild(tr);
  }
  rowCount.textContent = `Showing ${rows.length} of ${fullData.length} students.`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function updateStats(visibleRows) {
  const total = visibleRows.length;
  const paid = visibleRows.filter(r => r.status === "Paid").length;
  const unpaid = total - paid;
  const collected = visibleRows.reduce((s, r) => s + (r.amount_paid || 0), 0);
  const pct = n => (total ? Math.round((n / total) * 100) : 0);

  document.getElementById("statTotal").textContent = total.toLocaleString();
  document.getElementById("statPaid").textContent = paid.toLocaleString();
  document.getElementById("statPaidPct").textContent = `${pct(paid)}% of filtered`;
  document.getElementById("statUnpaid").textContent = unpaid.toLocaleString();
  document.getElementById("statUnpaidPct").textContent = `${pct(unpaid)}% of filtered`;
  document.getElementById("statCollected").textContent =
    "₹" + collected.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  const m = MONTH_NAMES[+monthSelect.value - 1];
  document.getElementById("statPeriod").textContent = `${m} ${yearSelect.value}`;
}

function formatDate(iso) {
  if (!iso) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : iso;
}

function downloadCsv() {
  const rows = getFiltered();
  const headers = ["Name", "Roll No", "Batch", "Semester", "Fee Status", "Amount Paid", "Payment Date"];
  const lines = [headers.join(",")];
  for (const r of rows) {
    const cells = [
      r.name, r.roll_number, r.batch_name, r.semester, r.status,
      r.amount_paid != null ? r.amount_paid.toFixed(2) : "",
      formatDate(r.payment_date),
    ].map(csvEscape);
    lines.push(cells.join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `fees_${MONTH_NAMES[+monthSelect.value - 1]}_${yearSelect.value}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function csvEscape(v) {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);

  const bar = document.getElementById("progressBar");
  const fill = document.getElementById("progressFill");
  bar.hidden = false;
  fill.style.width = "0%";
  fill.textContent = "0%";
  fill.classList.remove("processing");
  uploadStatus.textContent = `Uploading ${(file.size / 1024).toFixed(1)} KB…`;

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/upload-fees");

  xhr.upload.addEventListener("progress", e => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      fill.style.width = pct + "%";
      fill.textContent = pct + "%";
    }
  });

  let processingStartedAt = null;
  let processingTimer = null;
  xhr.upload.addEventListener("load", () => {
    fill.style.width = "100%";
    fill.textContent = "Processing…";
    fill.classList.add("processing");
    processingStartedAt = Date.now();
    processingTimer = setInterval(() => {
      const secs = Math.floor((Date.now() - processingStartedAt) / 1000);
      uploadStatus.textContent = `Server processing rows… (${secs}s)`;
    }, 500);
  });

  xhr.addEventListener("loadend", async () => {
    if (processingTimer) clearInterval(processingTimer);
    bar.hidden = true;
    fill.classList.remove("processing");

    let data = {};
    try { data = JSON.parse(xhr.responseText); } catch {}
    if (xhr.status < 200 || xhr.status >= 300) {
      uploadStatus.textContent = `Upload failed (HTTP ${xhr.status}): ${data.error || xhr.statusText}`;
      return;
    }
    uploadStatus.textContent =
      `Upload done. Inserted: ${data.inserted}, Updated: ${data.updated}, New students created: ${data.new_students_created ?? 0}` +
      (data.parse_errors?.length ? ` — ${data.parse_errors.length} parse error(s)` : "");
    await loadStudents();
  });

  xhr.addEventListener("error", () => {
    if (processingTimer) clearInterval(processingTimer);
    bar.hidden = true;
    uploadStatus.textContent = "Upload failed — network error.";
  });

  xhr.send(fd);
}

// Wire events
[monthSelect, yearSelect].forEach(el => el.addEventListener("change", loadStudents));
[filterName, filterRoll, filterBatch, filterSemester, filterStatus].forEach(el =>
  el.addEventListener("input", render)
);
uploadBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => {
  if (e.target.files[0]) uploadFile(e.target.files[0]);
  e.target.value = "";
});
downloadBtn.addEventListener("click", downloadCsv);
sampleBtn.addEventListener("click", downloadSampleCsv);
wipeBtn.addEventListener("click", wipeAll);

tbody.addEventListener("click", async (e) => {
  const btn = e.target.closest(".row-delete");
  if (!btn) return;
  const id = btn.dataset.id;
  const row = btn.closest("tr");
  const name = row?.cells[0]?.innerText || `student ${id}`;
  if (!confirm(`Delete ${name}? This also removes all their fee records.`)) return;
  const res = await fetch(`/api/students/${id}`, { method: "DELETE" });
  if (!res.ok) {
    alert(`Delete failed (HTTP ${res.status})`);
    return;
  }
  await loadStudents();
});

async function wipeAll() {
  if (!confirm("This will PERMANENTLY delete ALL students and ALL fee records. The database will be left empty. Continue?")) return;
  const typed = prompt('Type DELETE (in capitals) to confirm:');
  if (typed !== "DELETE") {
    uploadStatus.textContent = "Wipe cancelled.";
    return;
  }
  uploadStatus.textContent = "Wiping…";
  const res = await fetch("/api/wipe-all", { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    uploadStatus.textContent = `Wipe failed: ${data.error || "unknown error"}`;
    return;
  }
  uploadStatus.textContent = `Wiped. Deleted ${data.deleted_students} students and ${data.deleted_fees} fee records. Upload a CSV to add data.`;
  await loadBatches();
  await loadStudents();
}

function downloadSampleCsv() {
  const headers = ["roll_number", "name", "batch_name", "semester", "month", "year", "amount_paid", "payment_date"];
  const examples = [
    ["CSE24001", "Aarav Sharma", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 1", "5", "2026", "15000", "01/05/2026"],
    ["NEW001",   "New Student",  "2025 - Aug - B.Tech ME",  "B.Tech ME - Sem 1",  "5", "2026", "14000", "02/05/2026"],
  ];
  const lines = [headers.join(","), ...examples.map(r => r.map(csvEscape).join(","))];
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "fees_sample.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// Boot
initDateSelects();
loadBatches().then(loadStudents);
