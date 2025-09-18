-- 010_scan_checkin.sql  (delta add-ons for scan check-in/out)
create extension if not exists pgcrypto;

-- allowlist domain
create table if not exists public.allowed_email_domain (
  domain text primary key,
  created_at timestamptz not null default now()
);
insert into public.allowed_email_domain(domain) values ('up.ac.th')
on conflict do nothing;

-- hashed PIN per user
create table if not exists public.user_scan_code (
  user_id bigint primary key references public.users(id) on delete cascade,
  code_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists trg_user_scan_code_touch on public.user_scan_code;
create trigger trg_user_scan_code_touch
before update on public.user_scan_code
for each row execute function public.touch_updated_at();

-- data quality for usage_log
alter table public.usage_log
  drop constraint if exists chk_usage_checkout_after_checkin;
alter table public.usage_log
  add constraint chk_usage_checkout_after_checkin
  check (checkout_time is null or checkout_time > checkin_time);

create unique index if not exists uq_open_usage_per_user_facility
on public.usage_log (user_id, facility_id) where checkout_time is null;

-- helper
create or replace function public.is_email_domain_allowed(p_email text)
returns boolean language sql stable as $$
  select exists(
    select 1
    from public.allowed_email_domain d
    where lower(split_part(p_email,'@',2)) = lower(d.domain)
  );
$$;

-- admin: set/change PIN (hash)
create or replace function public.admin_set_scan_code(p_email text, p_plain_code text)
returns void language plpgsql security definer as $$
declare
  v_user_id bigint;
begin
  select id into v_user_id from public.users where email = p_email;
  if v_user_id is null then
    raise exception 'USER_NOT_FOUND';
  end if;

  insert into public.user_scan_code(user_id, code_hash)
  values (v_user_id, crypt(p_plain_code, gen_salt('bf')))
  on conflict (user_id) do update
    set code_hash = excluded.code_hash, updated_at = now();
end;
$$;

-- RPC: check-in
create or replace function public.rpc_scan_check_in(
  p_email text,
  p_plain_code text,
  p_facility_name text
) returns public.usage_log
language plpgsql security definer as $$
declare
  v_user_id bigint;
  v_facility_id bigint;
  v_hash text;
  rec public.usage_log;
begin
  if not public.is_email_domain_allowed(p_email) then
    raise exception 'EMAIL_DOMAIN_NOT_ALLOWED';
  end if;

  select id into v_user_id from public.users where email = p_email;
  if v_user_id is null then
    raise exception 'USER_NOT_FOUND';
  end if;

  select id into v_facility_id from public.sport_facility where facility_name = p_facility_name;
  if v_facility_id is null then
    raise exception 'FACILITY_NOT_FOUND';
  end if;

  select code_hash into v_hash from public.user_scan_code where user_id = v_user_id;
  if v_hash is null then
    raise exception 'CODE_NOT_SET';
  end if;
  if crypt(p_plain_code, v_hash) <> v_hash then
    raise exception 'INVALID_CODE';
  end if;

  insert into public.usage_log (user_id, facility_id, checkin_time)
  values (v_user_id, v_facility_id, now())
  returning * into rec;

  return rec;
end;
$$;

-- RPC: check-out
create or replace function public.rpc_scan_check_out(
  p_email text,
  p_plain_code text,
  p_facility_name text
) returns public.usage_log
language plpgsql security definer as $$
declare
  v_user_id bigint;
  v_facility_id bigint;
  v_hash text;
  rec public.usage_log;
begin
  if not public.is_email_domain_allowed(p_email) then
    raise exception 'EMAIL_DOMAIN_NOT_ALLOWED';
  end if;

  select id into v_user_id from public.users where email = p_email;
  if v_user_id is null then
    raise exception 'USER_NOT_FOUND';
  end if;

  select id into v_facility_id from public.sport_facility where facility_name = p_facility_name;
  if v_facility_id is null then
    raise exception 'FACILITY_NOT_FOUND';
  end if;

  select code_hash into v_hash from public.user_scan_code where user_id = v_user_id;
  if v_hash is null then
    raise exception 'CODE_NOT_SET';
  end if;
  if crypt(p_plain_code, v_hash) <> v_hash then
    raise exception 'INVALID_CODE';
  end if;

  update public.usage_log
     set checkout_time = now()
   where user_id = v_user_id
     and facility_id = v_facility_id
     and checkout_time is null
  returning * into rec;

  return rec; -- null = ไม่มี session ค้าง
end;
$$;

-- view: current presence
create or replace view public.vw_current_facility_presence as
select
  f.facility_name,
  u.first_name, u.last_name, u.email,
  ul.checkin_time
from public.usage_log ul
join public.users u on u.id = ul.user_id
join public.sport_facility f on f.id = ul.facility_id
where ul.checkout_time is null;
