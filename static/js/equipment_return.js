(() => {
  // -------- helpers --------
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  // อ่าน csrftoken จาก cookie (Django)
  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  }
  const CSRF = getCookie("csrftoken");

  // DOM refs
  const selEquip = $("#equipmentReturn");
  const inputQty = $("#qtyReturn");
  const btnMinus = $('.qty-btn[data-delta="-1"]');
  const btnPlus =  $('.qty-btn[data-delta="1"]');
  const btnConfirm = $("#btnReturnConfirm");
  const sheetReturn = $("#sheetReturn");
  const stockList = $("#stockList");

  // ปรับจำนวนด้วยปุ่ม +/−
  function clampQty(v) {
    const n = parseInt(v || "1", 10);
    return Math.max(1, Number.isFinite(n) ? n : 1);
  }
  btnMinus?.addEventListener("click", () => {
    inputQty.value = clampQty((+inputQty.value || 1) - 1);
  });
  btnPlus?.addEventListener("click", () => {
    inputQty.value = clampQty((+inputQty.value || 1) + 1);
  });
  inputQty?.addEventListener("input", () => {
    inputQty.value = clampQty(inputQty.value);
  });

  // ปุ่มปิด sheet (คลิกพื้นหลัง)
  sheetReturn?.addEventListener("click", (e) => {
    if (e.target === sheetReturn) {
      sheetReturn.setAttribute("aria-hidden", "true");
    }
  });

  // อัปเดตตัวเลขสต็อกในรายการฝั่งขวา
  function updateStockUI(name, newStock) {
    const li = $$(".stock-list li").find((li) => {
      const span = $("span", li);
      return span && span.textContent.trim() === name;
    });
    if (li) {
      const b = $("b", li);
      if (b) b.textContent = String(newStock);
    }
  }

  // โยน error ให้อ่านง่าย
  async function toJSONorThrow(resp) {
    let data = {};
    try { data = await resp.json(); } catch (_) {}
    if (!resp.ok) {
      const msg = data.message || data.error || `HTTP ${resp.status}`;
      const e = new Error(msg);
      e.status = resp.status;
      e.data = data;
      throw e;
    }
    return data;
  }

  // ทำการคืน
  async function doReturn() {
    const name = selEquip?.value?.trim();
    const qty = clampQty(inputQty?.value);

    if (!name) {
      alert("กรุณาเลือกอุปกรณ์");
      selEquip?.focus();
      return;
    }
    if (qty < 1) {
      alert("จำนวนไม่ถูกต้อง");
      inputQty?.focus();
      return;
    }

    btnConfirm.disabled = true;
    btnConfirm.textContent = "กำลังดำเนินการ...";

    try {
      const resp = await fetch(window.RETURN_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF,            // สำคัญกับ Django!
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ equipment: name, qty }),
        credentials: "same-origin",
      });
      const data = await toJSONorThrow(resp);

      // อัปเดต UI
      if (typeof data.stock === "number") {
        updateStockUI(name, data.stock);
      }
      inputQty.value = "1";
      sheetReturn?.setAttribute("aria-hidden", "false");
    } catch (err) {
      console.error(err);
      alert(err.message || "เกิดข้อผิดพลาดในการทำรายการ");
    } finally {
      btnConfirm.disabled = false;
      btnConfirm.textContent = "ทำการคืน";
    }
  }

  btnConfirm?.addEventListener("click", doReturn);

  // Enter เพื่อยืนยัน
  inputQty?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      doReturn();
    }
  });
})();