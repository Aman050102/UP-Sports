// ===== Helper =====
const $ = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => Array.from(p.querySelectorAll(s));
const ymd = d => new Date(d).toISOString().slice(0, 10);
const fmtTime = iso => new Date(iso).toLocaleString([], { hour:'2-digit', minute:'2-digit' });

const FAC_NAME = {
  outdoor: 'สนามกลางแจ้ง',
  badminton: 'สนามแบดมินตัน',
  pool: 'สระว่ายน้ำ',
  track: 'ลู่และลาน',
};

let allRows = [];
let filtered = [];
let facilityFilter = 'all';
let pie;

// ====== fetch ======
async function fetchCheckins(params){
  const u = new URL(window.APP.API_CHECKINS_URL, location.origin);
  Object.entries(params).forEach(([k,v]) => v!=null && u.searchParams.set(k,v));
  const res = await fetch(u.toString(), {headers: {'Accept':'application/json'}});
  return res.ok ? res.json() : [];
}

// ====== load/apply/render ======
async function load(){
  const from = $('#from').value || ymd(new Date());
  const to   = $('#to').value   || ymd(new Date());
  const facility = facilityFilter === 'all' ? '' : facilityFilter;
  allRows = await fetchCheckins({ from, to, facility });
  applyFilters();
}

function applyFilters(){
  const q = ($('#q')?.value || '').trim().toLowerCase();
  filtered = allRows.filter(r => {
    const okFac = (facilityFilter === 'all' || r.facility === facilityFilter);
    const bag = (FAC_NAME[r.facility] || r.facility).toLowerCase();
    return okFac && (!q || bag.includes(q));
  });
  render();
}

function render(){
  // ตาราง
  const tb = $('#table tbody'); if(!tb) return;
  tb.innerHTML = '';
  filtered.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${fmtTime(r.ts)}</td>
      <td>${r.session_date}</td>
      <td>${FAC_NAME[r.facility] || r.facility}</td>
      <td></td><td></td><td></td><td></td>`;
    tb.appendChild(tr);
  });

  // ตัวเลข
  const counts = { total: filtered.length, outdoor:0, badminton:0, pool:0, track:0 };
  filtered.forEach(r => { if(counts[r.facility] != null) counts[r.facility]++; });
  $('#st-total').textContent = String(counts.total);
  $('#st-outdoor').textContent = String(counts.outdoor);
  $('#st-badminton').textContent = String(counts.badminton);
  $('#st-pool').textContent = String(counts.pool);
  $('#st-track').textContent = String(counts.track);

  // พายชาร์ต
  const ctx = $('#pieChart');
  const data = [
    counts.outdoor, counts.badminton, counts.pool, counts.track
  ];
  const labels = ['สนามกลางแจ้ง','สนามแบดมินตัน','สระว่ายน้ำ','ลู่และลาน'];

  if(pie) pie.destroy();
  pie = new Chart(ctx, {
    type:'pie',
    data:{
      labels,
      datasets:[{
        data,
        backgroundColor:['#2e7d32','#1565c0','#0f766e','#ef6c00'],
        borderWidth:0
      }]
    },
    options:{ plugins:{ legend:{ position:'right' } } }
  });
}

// ====== Export helpers ======
function rowsForExport(){
  // สรุปเป็น "วันที่ / ชื่อสนาม / จำนวนคนเข้าใช้"
  const map = new Map(); // key = date|facility
  filtered.forEach(r => {
    const key = `${r.session_date}|${r.facility}`;
    map.set(key, (map.get(key) || 0) + 1);
  });
  const rows = [];
  for(const [k, count] of map.entries()){
    const [date, fac] = k.split('|');
    rows.push({ 'วันที่ (session)':date, 'ชื่อสนาม': (FAC_NAME[fac] || fac), 'จำนวนคนเข้าใช้': count });
  }
  rows.sort((a,b)=> a['วันที่ (session)'].localeCompare(b['วันที่ (session)']) ||
                    a['ชื่อสนาม'].localeCompare(b['ชื่อสนาม']));
  return rows;
}

// Excel
$('#btnExcel')?.addEventListener('click', () => {
  const ws = XLSX.utils.json_to_sheet(rowsForExport());
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Counts');
  XLSX.writeFile(wb, `checkins_${$('#from').value || ''}_${$('#to').value || ''}.xlsx`);
});

// PDF
$('#btnPDF')?.addEventListener('click', () => {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation:'p', unit:'pt', format:'a4' });
  const data = rowsForExport();
  doc.setFont('Helvetica',''); doc.setFontSize(12);
  doc.text(`รายงานผู้เข้าใช้สนามกีฬา (ช่วง ${$('#from').value || ''} - ${$('#to').value || ''})`, 40, 40);
  const head = [['วันที่ (session)','ชื่อสนาม','จำนวนคนเข้าใช้']];
  const body = data.map(o => [o['วันที่ (session)'], o['ชื่อสนาม'], o['จำนวนคนเข้าใช้']]);
  doc.autoTable({ head, body, startY: 60, styles:{ fontSize:10 } });
  doc.save(`checkins_${$('#from').value || ''}_${$('#to').value || ''}.pdf`);
});

// DOCX
$('#btnDoc')?.addEventListener('click', async () => {
  const { Document, Packer, Paragraph, Table, TableRow, TableCell, WidthType, HeadingLevel, AlignmentType } = docx;
  const rows = rowsForExport();
  const headerCells = ['วันที่ (session)','ชื่อสนาม','จำนวนคนเข้าใช้']
    .map(t => new TableCell({ children:[ new Paragraph({ text:t, bold:true }) ] }));
  const tableRows = [new TableRow({ children: headerCells })];
  rows.forEach(r => {
    tableRows.push(new TableRow({
      children: [r['วันที่ (session)'], r['ชื่อสนาม'], r['จำนวนคนเข้าใช้']]
        .map(v => new TableCell({ children: [ new Paragraph(String(v)) ] }))
    }));
  });
  const table = new Table({ width:{ size:100, type: WidthType.PERCENT }, rows: tableRows });
  const docxDoc = new Document({
    sections:[{
      children:[
        new Paragraph({ text:'รายงานผู้เข้าใช้สนามกีฬา', heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER }),
        new Paragraph(`ช่วง ${$('#from').value || ''} - ${$('#to').value || ''}`),
        table
      ]
    }]
  });
  const blob = await Packer.toBlob(docxDoc);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `checkins_${$('#from').value || ''}_${$('#to').value || ''}.docx`;
  a.click();
});

// พิมพ์
$('#btnPrint')?.addEventListener('click', () => window.print());

// Events
$('#q')?.addEventListener('input', applyFilters);
$$('#chips .chip').forEach(ch => ch.addEventListener('click', () => {
  $$('#chips .chip').forEach(x => x.classList.remove('selected'));
  ch.classList.add('selected');
  facilityFilter = ch.dataset.k;
  load();
}));

// เริ่มต้น
window.addEventListener('load', load);