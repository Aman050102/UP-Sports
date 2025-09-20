-- 020_seed_domains_and_pins.sql
insert into public.allowed_email_domain(domain) values ('up.ac.th')
on conflict do nothing;

-- เพิ่ม user (ถ้ายังไม่มี)
insert into public.users (first_name,last_name,user_type,email,department)
select * from (values
  ('Student','UP','STUDENT','67022951@up.ac.th','ICT'),
  ('Student','UP','STUDENT','67022940@up.ac.th','ICT')
) as t(first_name,last_name,user_type,email,department)
on conflict (email) do nothing;

-- ตั้ง PIN เดียวกันทุกคน
with ids(email,pin) as (values
  ('67022951@up.ac.th','123456'),
  ('67022940@up.ac.th','123456')
)
select public.admin_set_scan_code(email, pin) from ids;

-- หรือ (ถ้าชอบ) ให้ PIN = 6 ตัวท้ายของรหัสนิสิต
-- with ids(id) as (values ('67022951'),('67022940'))
-- select public.admin_set_scan_code(id || '@up.ac.th', right(id,6)) from ids;
