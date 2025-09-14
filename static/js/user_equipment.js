// static/js/user_equipment.js
(() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  const sel = $("#equipment");
  const qty = $("#qty");
  const btnInc = $$('.qty-btn[data-delta="1"]');
  const btnDec = $$('.qty-btn[data-delta="-1"]');
  const btnConfirm = $("#confirmBtn");
  const sheetBorrow = $("#sheetBorrow");

  const btnBorrowTab = $("#btnBorrow");
  const btnReturnTab = $("#btnReturn");

  // อ่าน stock จากด้านขวา
  const stock = {};
  $$("#stockList li").forEach((li) => {
    const name = li.querySelector("span")?.textContent.trim();
    const left = parseInt(li.querySelector("b")?.textContent.replace(/,/g, ""), 10) || 0;
    stock[name] = left;
  });

  function getCookie(name) {
    const v = `; ${document.cookie}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return p.pop().split(";").shift();
    return "";
  }
  const CSRF = getCookie("csrftoken") || (document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "");

  function clampQty() {
    let v = parseInt(qty.value, 10);
    if (!Number.isFinite(v) || v < 1) v = 1;
    qty.value = String(v);
  }

  function updateRow(name, newLeft) {
    const li = $$("#stockList li").find((li) => li.querySelector("span")?.textContent.trim() === name);
    if (li) li.querySelector("b").textContent = Number(newLeft).toLocaleString();
  }

  function openSheet(el) {
    if (!el) return;
    el.setAttribute("aria-hidden", "false");
    setTimeout(() => el.setAttribute("aria-hidden", "true"), 1200);
  }

  async function callAPI(url, payload) {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF,
      },
      body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data?.message || "เกิดข้อผิดพลาดจากเซิร์ฟเวอร์");
    return data;
  }

  // events
  btnInc.forEach((b)=> b.addEventListener("click", ()=>{ qty.value = String((parseInt(qty.value,10)||1)+1); }));
  btnDec.forEach((b)=> b.addEventListener("click", ()=>{ qty.value = String(Math.max(1,(parseInt(qty.value,10)||1)-1)); }));
  qty.addEventListener("input", clampQty);
  qty.addEventListener("blur", clampQty);

  btnConfirm?.addEventListener("click", async () => {
    clampQty();
    const name = sel.value;
    const n = parseInt(qty.value, 10) || 1;
    if (!name) return alert("กรุณาเลือกอุปกรณ์");

    btnConfirm.disabled = true;
    try {
      if (!window.BORROW_API) {
        // โหมดออฟไลน์: ตัดจาก client
        if (n > (stock[name] || 0)) throw new Error(`สต็อก "${name}" คงเหลือ ${stock[name] || 0} ชิ้น`);
        stock[name] -= n;
        updateRow(name, stock[name]);
        openSheet(sheetBorrow);
        return;
      }

      const res = await callAPI(window.BORROW_API, { equipment: name, qty: n });
      // ใช้ค่า stock จาก backend ถ้ามี
      stock[name] = typeof res.stock === "number" ? res.stock : Math.max(0, (stock[name] || 0) - n);
      updateRow(name, stock[name]);
      openSheet(sheetBorrow);
    } catch (err) {
      alert(err.message || "ไม่สามารถทำรายการยืมได้");
    } finally {
      btnConfirm.disabled = false;
    }
  });

  // สลับไปหน้า “คืน”
  btnReturnTab?.addEventListener("click", () => {
    const href = document.querySelector('a[href*="user_equipment_return"]')?.getAttribute("href");
    if (href) location.href = href;
    else location.href = "/user/equipment/return/";
  });
})();