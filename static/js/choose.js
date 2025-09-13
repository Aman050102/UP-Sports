// === helpers ===
const $ = (id) => document.getElementById(id);

// อ่านค่า csrftoken จาก cookie (สำหรับ Django)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

// ตัวเลือกระดับบน
const TOP = [
  { k: "outdoor", name: "สนามกลางแจ้ง", isOutdoor: true },
  { k: "badminton", name: "สนามแบดมินตัน" },
  { k: "track", name: "สนามลู่-ลาน" },
  { k: "pool", name: "สระว่ายน้ำ" },
];

// สนามย่อยของ outdoor (จะบันทึกเป็น facility=outdoor และแนบ sub แค่เพื่อแสดงผล/อนาคต)
const OUTDOOR_SUBS = [
  { k: "tennis", name: "เทนนิส" },
  { k: "basketball", name: "บาสเก็ตบอล" },
  { k: "futsal", name: "ฟุตซอล" },
  { k: "volleyball", name: "วอลเลย์บอล" },
  { k: "sepak_takraw", name: "เซปักตะกร้อ" },
];

// === init UI ===
(function init() {
  // วันที่ session (สำหรับโชว์ใน UI เฉย ๆ ตอนนี้ backend ไม่ได้ใช้)
  const today = new Date().toISOString().slice(0, 10);
  if ($("session")) $("session").value = today;

  // ปุ่มชั้นบน
  const gridTop = $("grid-top");
  if (gridTop) {
    TOP.forEach((f) => {
      const b = document.createElement("button");
      b.className = "btn";
      b.type = "button";
      b.textContent = f.name;
      b.onclick = () => onTopClick(f);
      gridTop.appendChild(b);
    });
  }

  // ปุ่มสนามย่อย outdoor
  const gridOutdoor = $("grid-outdoor");
  if (gridOutdoor) {
    OUTDOOR_SUBS.forEach((s) => {
      const b = document.createElement("button");
      b.className = "btn";
      b.type = "button";
      b.textContent = s.name;
      b.onclick = () => checkin("outdoor", s.k); // บันทึกเป็น outdoor + sub
      gridOutdoor.appendChild(b);
    });
  }

  const backBtn = $("btnBack");
  if (backBtn) {
    backBtn.onclick = () => {
      $("panel-outdoor").classList.add("hidden");
      $("panel-top").classList.remove("hidden");
    };
  }
})();

function onTopClick(f) {
  if (f.isOutdoor) {
    $("panel-top").classList.add("hidden");
    $("panel-outdoor").classList.remove("hidden");
  } else {
    checkin(f.k, null);
  }
}

// === core: เรียก API Django ===
// ใช้ POST /api/check-event/ { facility, action: "in" } พร้อม CSRF
async function checkin(facility, sub = null) {
  const csrftoken = getCookie("csrftoken");
  const body = new URLSearchParams();
  body.set("facility", facility);
  body.set("action", "in");
  // sub ยังไม่ได้เก็บใน DB; แนบไว้เผื่ออนาคต/ดีบัก ฝั่ง backend จะเพิกเฉยเอง
  if (sub) body.set("sub", sub);

  try {
    const res = await fetch("/api/check-event/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken || "",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body: body.toString(),
      credentials: "same-origin",
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`HTTP ${res.status}: ${txt}`);
    }

    // แสดง overlay แล้วพาไปหน้าเมนูผู้ใช้
    showDone();
  } catch (err) {
    console.error("checkin failed:", err);
    alert("เช็คอินไม่สำเร็จ กรุณาลองใหม่อีกครั้ง");
  }
}

function showDone() {
  const overlay = $("overlay");
  if (overlay) overlay.classList.add("show");

  // เดิมคุณ redirect ไป /user_menu.html (ซึ่งไม่มี URL)
  // ใน Django ให้พาไป path จริงคือ /user/
  setTimeout(() => {
    window.location.href = "/user/";
  }, 800);
}

/* -------------------------------------------------------
  หมายเหตุสำคัญ
  - endpoint ที่ถูกต้องตาม backend ปัจจุบันคือ /api/check-event/
  - facility ที่ backend รองรับ: outdoor | badminton | pool | track
  - ถ้าต้องการเก็บประเภทสนามย่อย (เช่น tennis, futsal)
    ให้เพิ่ม field ใหม่ในโมเดลหรือสร้างตาราง CheckinDetail
    แล้วปรับ view api_check_event ให้อ่านพารามิเตอร์ "sub"
-------------------------------------------------------- */
