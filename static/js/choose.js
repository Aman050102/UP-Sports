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

// สนามย่อยของ outdoor
const OUTDOOR_SUBS = [
  { k: "tennis", name: "เทนนิส" },
  { k: "basketball", name: "บาสเก็ตบอล" },
  { k: "futsal", name: "ฟุตซอล" },
  { k: "volleyball", name: "วอลเลย์บอล" },
  { k: "sepak_takraw", name: "เซปักตะกร้อ" },
];

// === format วัน–เวลาไทย (locked Asia/Bangkok) ===
function formatNow() {
  const currentDate = new Date();
  return currentDate.toLocaleString("th-TH", {
    dateStyle: "long",
    timeStyle: "medium",
    timeZone: "Asia/Bangkok",
  });
}

// === clock updater ===
function startClock() {
  const el = $("sessionText");
  if (!el) return;
  const tick = () => (el.textContent = formatNow());
  tick(); // แสดงครั้งแรกทันที
  setInterval(tick, 1000); // อัปเดตทุกวินาที
}

// === init UI ===
(function init() {
  // นาฬิกา
  startClock();

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
      b.onclick = () => checkin("outdoor", s.k);
      gridOutdoor.appendChild(b);
    });
  }

  // ปุ่ม back
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
async function checkin(facility, sub = null) {
  const csrftoken = getCookie("csrftoken");
  const body = new URLSearchParams();
  body.set("facility", facility);
  body.set("action", "in");
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

    showDone();
  } catch (err) {
    console.error("checkin failed:", err);
    alert("เช็คอินไม่สำเร็จ กรุณาลองใหม่อีกครั้ง");
  }
}

function showDone() {
  const overlay = $("overlay");
  if (overlay) overlay.classList.add("show");
  setTimeout(() => {
    window.location.href = "/user/";
  }, 800);
}