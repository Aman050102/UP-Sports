const id = k => document.getElementById(k);

// รายการปุ่ม
const TOP = [
    { k: 'outdoor', name: 'สนามกลางแจ้ง', isOutdoor: true },
    { k: 'badminton', name: 'สนามแบดมินตัน' },
    { k: 'track', name: 'สนามลู่-ลาน' },
    { k: 'pool', name: 'สระว่ายน้ำ' },
];
const OUTDOOR_SUBS = [
    { k: 'tennis', name: 'เทนนิส' },
    { k: 'basketball', name: 'บาสเก็ตบอล' },
    { k: 'futsal', name: 'ฟุตซอล' },
    { k: 'volleyball', name: 'วอลเลย์บอล' },
    { k: 'sepak_takraw', name: 'เซปักตะกร้อ' },
];

(function init() {
    const u = new URL(location.href);
    id('session').value = u.searchParams.get('session') || new Date().toISOString().slice(0, 10);

    // ปุ่มชั้นบน
    const gridTop = id('grid-top');
    TOP.forEach(f => {
        const b = document.createElement('button');
        b.className = 'btn'; b.type = 'button';
        b.textContent = f.name; b.onclick = () => onTopClick(f);
        gridTop.appendChild(b);
    });

    // ปุ่มสนามย่อย outdoor
    const gridOutdoor = id('grid-outdoor');
    OUTDOOR_SUBS.forEach(s => {
        const b = document.createElement('button');
        b.className = 'btn'; b.type = 'button';
        b.textContent = s.name; b.onclick = () => checkin(s.k);
        gridOutdoor.appendChild(b);
    });

    id('btnBack').onclick = () => {
        id('panel-outdoor').classList.add('hidden');
        id('panel-top').classList.remove('hidden');
    };
})();

function onTopClick(f) {
    if (f.isOutdoor) {
        id('panel-top').classList.add('hidden');
        id('panel-outdoor').classList.remove('hidden');
    } else {
        checkin(f.k);
    }
}

// ยิง /checkin เป็น pixel (ต้องล็อกอินแล้ว – middleware จัดการ)
function checkin(facility) {
    const session = id('session').value;

    // ถ้า router map /checkin -> public/checkin/pixel.php ให้ใช้ '/checkin'
    // ถ้าเสิร์ฟไฟล์ตรง ให้ใช้ '/checkin/pixel.php'
    const url = new URL('/checkin', location.origin); // หรือ '/checkin/pixel.php'
    url.searchParams.set('facility', facility);
    url.searchParams.set('session', session);
    url.searchParams.set('format', 'pixel');

    const img = new Image(1, 1);
    img.onload = showDone;
    img.onerror = showDone;
    img.src = url.toString();
}

function showDone() {
    id('overlay').classList.add('show');
    // ทุกครั้งที่เช็คอินเสร็จ -> ออกจากระบบ (ต้องล็อกอินใหม่ก่อนเช็คอินครั้งต่อไป)
    setTimeout(() => {
        window.location.href = '/auth/logout.php';
    }, 1000);
}