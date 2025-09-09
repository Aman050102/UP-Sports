const $  = (s,p=document)=>p.querySelector(s);
    const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));
    const FAC_NAME = { outdoor:'สนามกลางแจ้ง', badminton:'สนามแบดมินตัน', pool:'สระว่ายน้ำ', track:'ลู่และลาน' };
    const COLORS   = { outdoor:getCss('--outdoor'), badminton:getCss('--badminton'), pool:getCss('--pool'), track:getCss('--track') };
    function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
    function ymd(d){ return new Date(d).toISOString().slice(0,10); }
    function fmtTime(iso){ const d = new Date(iso); return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}); }
    const today = ymd(new Date()); $('#from').value=today; $('#to').value=today;

    let rows = [];               // หลังกรองชื่อ
    let facilityFilter = 'all';  // all | outdoor | badminton | pool | track
    let chart;

    // ===== helpers: bucket =====
    function pad2(n){return String(n).padStart(2,'0');}
    function bucketKey(date, mode){
      const y = date.getFullYear(), m = pad2(date.getMonth()+1), d = pad2(date.getDate());
      if(mode==='hour') return `${pad2(date.getHours())}:00`;
      if(mode==='day')  return `${y}-${m}-${d}`;
      if(mode==='month')return `${y}-${m}`;
      return String(y); // year
    }
    function sortedLabels(mode, fromISO, toISO){
      const from = new Date(fromISO), to = new Date(toISO);
      const labels = [];
      const cur = new Date(from);
      if(mode==='hour'){
        for(let h=0; h<24; h++) labels.push(pad2(h)+':00');
      }else if(mode==='day'){
        while(cur <= to){ labels.push(`${cur.getFullYear()}-${pad2(cur.getMonth()+1)}-${pad2(cur.getDate())}`); cur.setDate(cur.getDate()+1); }
      }else if(mode==='month'){
        while(cur <= to){ labels.push(`${cur.getFullYear()}-${pad2(cur.getMonth()+1)}`); cur.setMonth(cur.getMonth()+1); }
      }else{
        while(cur.getFullYear() <= to.getFullYear()){ labels.push(String(cur.getFullYear())); cur.setFullYear(cur.getFullYear()+1); }
      }
      return labels;
    }

    async function fetchRows(){
      const qs = new URLSearchParams({
        from: $('#from').value, to: $('#to').value,
        facility: (facilityFilter==='all' ? '' : facilityFilter)
      }).toString();
      const res = await fetch("{% url 'api_checkins' %}?"+qs);
      const data = res.ok ? await res.json() : [];
      // คาดหวัง: { ts, session_date, facility, action?: 'in'|'out' }
      return data.map(r => ({ ...r, action: r.action || (r.facility==='pool' ? 'in' : 'in') }));
    }

    async function load(){
      const q = ($('#q').value||'').toLowerCase();
      const raw = await fetchRows();

      rows = raw.filter(r => {
        const name = (FAC_NAME[r.facility]||r.facility).toLowerCase();
        return !q || name.includes(q);
      });

      renderCountsAndTable();
      renderChart();
      updateBigBox();
    }

    function updateTableHeader(){
      const thead = $('#thead');
      const headText = $('#tableHeadText');
      if (facilityFilter === 'pool'){
        thead.innerHTML = '<tr><th>เวลาเข้า</th><th>เวลาออก</th><th>วันที่ (session)</th><th>สนาม</th></tr>';
        headText.textContent = 'เวลาเข้า   เวลาออก   วันที่ (session)   สนาม';
      } else {
        thead.innerHTML = '<tr><th>เวลา</th><th>วันที่ (session)</th><th>สนาม</th></tr>';
        headText.textContent = 'เวลา     วันที่ (session)     สนาม';
      }
    }

    function renderCountsAndTable(){
      updateTableHeader();
      const tb = $('#table tbody'); tb.innerHTML='';
      rows.forEach(r=>{
        const tr = document.createElement('tr');
        if (facilityFilter === 'pool'){
          tr.innerHTML = `<td>${r.action==='in' ? fmtTime(r.ts) : '-'}</td>
                          <td>${r.action==='out'? fmtTime(r.ts) : '-'}</td>
                          <td>${r.session_date}</td>
                          <td>${FAC_NAME[r.facility]||r.facility}</td>`;
        }else{
          tr.innerHTML = `<td>${fmtTime(r.ts)}</td>
                          <td>${r.session_date}</td>
                          <td>${FAC_NAME[r.facility]||r.facility}</td>`;
        }
        tb.appendChild(tr);
      });

      const c = countByFacility(rows);
      $('#st-outdoor').textContent = c.outdoor;
      $('#st-badminton').textContent = c.badminton;
      $('#st-pool').textContent = c.pool;
      $('#st-track').textContent = c.track;
      $('#st-total').textContent = c.total;
    }

    function countByFacility(list){
      const c = { outdoor:0, badminton:0, pool:0, track:0 };
      list.forEach(r => { if (c[r.facility]!==undefined) c[r.facility]++; });
      return { ...c, total: c.outdoor+c.badminton+c.pool+c.track };
    }

    function updateBigBox(){
      const title = facilityFilter==='all' ? 'สนามทั้งหมด' : (FAC_NAME[facilityFilter]||'สนาม');
      $('#bigbox').firstChild.nodeValue = ' ' + title + ' ';
      const c = countByFacility(rows);
      $('#bigcount').textContent = facilityFilter==='all' ? c.total : (c[facilityFilter]||0);
    }

    function renderChart(){
      const ctx = $('#chart').getContext('2d');
      if(chart) chart.destroy();

      const timeMode = $('#timeMode').value;
      const from = $('#from').value, to = $('#to').value;

      // 1) “ทั้งหมด” → PIE
      if (facilityFilter === 'all'){
        const c = countByFacility(rows);
        chart = new Chart(ctx,{
          type: 'pie',
          data:{
            labels: [FAC_NAME.outdoor, FAC_NAME.badminton, FAC_NAME.pool, FAC_NAME.track],
            datasets:[{ data:[c.outdoor,c.badminton,c.pool,c.track],
                        backgroundColor:[COLORS.outdoor,COLORS.badminton,COLORS.pool,COLORS.track] }]
          },
          options:{
            responsive:true,
            maintainAspectRatio:false,
            plugins:{ legend:{ position:'right', labels:{ usePointStyle:true } } }
          }
        });
        return;
      }

      // 2) สนามเฉพาะ → กราฟเวลาตามโหมด
      const labels = sortedLabels(timeMode, from, to);
      const dataIn  = new Array(labels.length).fill(0);
      const dataOut = new Array(labels.length).fill(0);

      // นับตาม bucket
      rows.forEach(r=>{
        const d = new Date(r.ts);
        const key = bucketKey(d, timeMode);
        const idx = labels.indexOf(key);
        if (idx === -1) return;
        if (facilityFilter === 'pool'){
          (r.action === 'out' ? dataOut : dataIn)[idx] += 1;
        }else{
          dataIn[idx] += 1; // สนามอื่นนับ “เข้า” อย่างเดียว
        }
      });

      // วาด
      if (facilityFilter === 'pool'){
        chart = new Chart(ctx,{
          type:'bar',
          data:{
            labels,
            datasets:[
              { label:'เข้า (Check-in)', data:dataIn,  backgroundColor:COLORS.pool },
              { label:'ออก (Check-out)', data:dataOut, backgroundColor:'#5bc0b7' }
            ]
          },
          options:{
            responsive:true, maintainAspectRatio:false,
            scales:{ y:{ beginAtZero:true, ticks:{ precision:0 } } },
            plugins:{ legend:{ position:'top' } }
          }
        });
      } else {
        const color = COLORS[facilityFilter] || '#888';
        chart = new Chart(ctx,{
          type:'bar',
          data:{ labels, datasets:[{ label:`จำนวนเข้าใช้ (${labelForMode(timeMode)})`, data:dataIn, backgroundColor:color }] },
          options:{
            responsive:true, maintainAspectRatio:false,
            scales:{ y:{ beginAtZero:true, ticks:{ precision:0 } } },
            plugins:{ legend:{ display:true } }
          }
        });
      }
    }

    function labelForMode(m){
      if(m==='hour') return 'รายชั่วโมง';
      if(m==='day')  return 'รายวัน';
      if(m==='month')return 'รายเดือน';
      return 'รายปี';
    }

    // ===== Export =====
    function rowsForExport(){
      const map = new Map(); // key: date|facility
      rows.forEach(r=>{
        const key = `${r.session_date}|${r.facility}`;
        map.set(key,(map.get(key)||0)+1);
      });
      const arr = [];
      for(const [k,n] of map){
        const [d,f] = k.split('|');
        arr.push({ 'วันที่ (session)': d, 'ชื่อสนาม': (FAC_NAME[f]||f), 'จำนวนคนเข้าใช้': n });
      }
      arr.sort((a,b)=>a['วันที่ (session)'].localeCompare(b['วันที่ (session)'])
        || a['ชื่อสนาม'].localeCompare(b['ชื่อสนาม']));
      return arr;
    }

    $('#btnExcel').addEventListener('click', ()=>{
      const ws = XLSX.utils.json_to_sheet(rowsForExport());
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Counts');
      XLSX.writeFile(wb, `checkins_${$('#from').value}_${$('#to').value}${facilitySuffix()}.xlsx`);
    });
    $('#btnPDF').addEventListener('click', ()=>{
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({orientation:'p', unit:'pt', format:'a4'});
      const data = rowsForExport();
      doc.setFont('Helvetica',''); doc.setFontSize(12);
      doc.text(`รายงานผู้เข้าใช้สนามกีฬา (ช่วง ${$('#from').value} - ${$('#to').value})`, 40, 40);
      if (facilityFilter!=='all') doc.text(`สนาม: ${FAC_NAME[facilityFilter]}`, 40, 58);
      const head = [['วันที่ (session)','ชื่อสนาม','จำนวนคนเข้าใช้']];
      const body = data.map(r=>[r['วันที่ (session)'], r['ชื่อสนาม'], r['จำนวนคนเข้าใช้']]);
      doc.autoTable({ head, body, startY:(facilityFilter==='all'?60:78), styles:{ fontSize:10 } });
      doc.save(`checkins_${$('#from').value}_${$('#to').value}${facilitySuffix()}.pdf`);
    });
    $('#btnDoc').addEventListener('click', async ()=>{
      const { Document, Packer, Paragraph, Table, TableRow, TableCell, WidthType, HeadingLevel } = docx;
      const arr = rowsForExport();
      const head = ['วันที่ (session)','ชื่อสนาม','จำนวนคนเข้าใช้']
        .map(t=>new TableCell({ children:[new Paragraph({text:t})] }));
      const trs = [new TableRow({children:head})];
      arr.forEach(r=>{
        trs.push(new TableRow({children:[
          new TableCell({children:[new Paragraph(String(r['วันที่ (session)']))]}),
          new TableCell({children:[new Paragraph(String(r['ชื่อสนาม']))]}),
          new TableCell({children:[new Paragraph(String(r['จำนวนคนเข้าใช้']))]}),
        ]}));
      });
      const table = new Table({ width:{size:100,type:WidthType.PERCENT}, rows:trs });
      const doc = new Document({ sections:[{ children:[
        new Paragraph({ text:'รายงานผู้เข้าใช้สนามกีฬา', heading:HeadingLevel.HEADING_1 }),
        new Paragraph(`ช่วง ${$('#from').value} - ${$('#to').value}${facilityFilter==='all'?'':(' · '+FAC_NAME[facilityFilter])}`),
        table
      ]}]});
      const blob = await Packer.toBlob(doc);
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `checkins_${$('#from').value}_${$('#to').value}${facilitySuffix()}.docx`;
      a.click();
    });
    $('#btnPrint').addEventListener('click', ()=>window.print());
    function facilitySuffix(){ return facilityFilter==='all' ? '' : `_${facilityFilter}`; }

    // Events
    $('#from').addEventListener('change', load);
    $('#to').addEventListener('change', load);
    $('#timeMode').addEventListener('change', load);
    $('#q').addEventListener('input', ()=>load());
    $$('#chips .chip').forEach(ch=>ch.addEventListener('click',()=>{
      $$('#chips .chip').forEach(x=>x.classList.remove('selected'));
      ch.classList.add('selected');
      facilityFilter = ch.dataset.k;
      load();
    }));
    document.addEventListener('DOMContentLoaded', load);