(() => {
  // ===== selectors =====
  const qtyInput   = document.getElementById("qty");
  const equipInput = document.getElementById("equipment");
  const bBorrow    = document.getElementById("btnBorrow");
  const bReturn    = document.getElementById("btnReturn");
  const confirmBtn = document.getElementById("confirmBtn");
  const submitBtn  = document.getElementById("submitBtn"); // ปุ่มซ้าย (ถ้ามี)

  // ===== state =====
  const MODES = { borrow: "borrow", ret: "return" };
  let currentMode = MODES.borrow;

  // ===== helpers =====
  function setMode(m){
    currentMode = m;
    const isBorrow = m === MODES.borrow;
    bBorrow?.classList.toggle("active", isBorrow);
    bBorrow?.setAttribute("aria-selected", String(isBorrow));
    bReturn?.classList.toggle("active", !isBorrow);
    bReturn?.setAttribute("aria-selected", String(!isBorrow));
    if (confirmBtn) confirmBtn.textContent = isBorrow ? "ทำการยืม" : "ทำการคืน";
  }
  function clampQty(n){
    n = parseInt(n || "1", 10);
    if (Number.isNaN(n) || n < 1) n = 1;
    return n;
  }
  function openSheet(id){
    const el = document.getElementById(id);
    if (!el) return;
    el.setAttribute("aria-hidden", "false");
    setTimeout(() => el.setAttribute("aria-hidden", "true"), 1600);
  }
  function getCookie(name){
    const pair = document.cookie.split(";").map(s => s.trim())
      .find(s => s.startsWith(name + "="));
    return pair ? decodeURIComponent(pair.slice(name.length + 1)) : "";
  }
  async function postBorrowReturn({action, equipment, qty}){
    const res = await fetch("/api/borrow-return/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ action, equipment, qty })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return data;
  }

  // ===== init =====
  setMode(MODES.borrow);

  // Toggle โหมด
  bBorrow?.addEventListener("click", () => setMode(MODES.borrow));
  bReturn?.addEventListener("click", () => setMode(MODES.ret));

  // ปุ่ม +/-
  document.querySelectorAll(".qty-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const delta = parseInt(btn.dataset.delta, 10) || 0;
      qtyInput.value = String(clampQty(qtyInput.value) + delta);
    });
  });

  // ปุ่มยืนยันหลัก
  confirmBtn?.addEventListener("click", async (e) => {
    e.preventDefault();
    const equipment = (equipInput?.value || "").trim();
    const qty = clampQty(qtyInput?.value || "1");
    if (!equipment) { alert("กรุณาเลือกอุปกรณ์"); return; }

    try {
      await postBorrowReturn({
        action: currentMode === MODES.borrow ? "borrow" : "return",
        equipment,
        qty
      });

      // แสดงแผ่นสำเร็จตามโหมด
      openSheet(currentMode === MODES.borrow ? "sheetBorrow" : "sheetReturn");

      // ถ้าต้องอัปเดต “คงเหลือ” ด้านขวา ให้เรียกฟังก์ชันรีเฟรชของคุณต่อที่นี่
      // refreshStockTable?.();

    } catch (err) {
      alert("ไม่สามารถบันทึกได้: " + (err?.message || "unknown"));
    }
  });

  // ปุ่มยืนยันรอง (ฝั่งซ้าย) ให้ทำงานเหมือนกัน
  submitBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    confirmBtn?.click();
  });
})();
