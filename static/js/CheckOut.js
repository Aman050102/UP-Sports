(function(){
      const openBtn   = document.getElementById('btn-open-checkout');
      const modal     = document.getElementById('checkout-modal');
      const okBtn     = document.getElementById('btn-confirm');
      const cancelBtn = document.getElementById('btn-cancel');
      const sheet     = document.getElementById('sheet-ok');

      function openModal(){ modal.setAttribute('aria-hidden','false'); }
      function closeModal(){ modal.setAttribute('aria-hidden','true'); }

      function showOk(){
        sheet.setAttribute('aria-hidden','false');
        setTimeout(()=> sheet.setAttribute('aria-hidden','true'), 1400);
      }

      openBtn?.addEventListener('click', openModal);
      cancelBtn?.addEventListener('click', closeModal);

      okBtn?.addEventListener('click', async () => {
        // TODO: เมื่อพร้อมเชื่อม backend ให้ fetch ไปยัง endpoint จริง
        // await fetch('{% url "pool_checkout_api" %}', {method:'POST', headers:{'X-CSRFToken': '{{ csrf_token }}'}});
        closeModal();
        showOk();
      });

      // ปิดเมื่อคลิกนอกการ์ด
      modal?.addEventListener('click', (e)=>{ if(e.target === modal) closeModal(); });
      // ปิดด้วย Esc
      window.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') closeModal(); });
    })();