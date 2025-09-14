(() => {
  const $ = (s, el = document) => el.querySelector(s);

  const API = "/api/staff/borrow-records/";
  const listEl = $("#borrowList");
  const input = $("#studentId");
  const btnSearch = $("#btnSearch");

  function rowTemplate(r) {
    const borrowDate = r.action === "borrow" ? r.when : "";
    const returnDate =
      r.action === "return" ? r.when : r.action === "borrow" ? "-" : "";
    const li = document.createElement("li");
    li.className = "row";
    li.innerHTML = `
      <div>${r.student_id}</div>
      <div>${r.equipment}</div>
      <div>${r.qty}</div>
      <div>${borrowDate}</div>
      <div>${returnDate}</div>
    `;
    return li;
  }

  async function runSearch() {
    const params = new URLSearchParams();
    const q = (input.value || "").trim();
    if (q) params.set("student", q);

    const res = await fetch(
      API + (params.toString() ? "?" + params.toString() : ""),
    );
    const data = await res.json();
    if (!data.ok) return alert(data.message || "โหลดข้อมูลไม่สำเร็จ");

    listEl.innerHTML = "";
    (data.rows || []).forEach((r) => listEl.appendChild(rowTemplate(r)));
  }

  btnSearch?.addEventListener("click", runSearch);
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runSearch();
    }
  });

  runSearch();
})();
