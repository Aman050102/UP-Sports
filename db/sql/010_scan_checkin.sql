-- Sports Facility Management - Supabase/Postgres schema (Integrated, Production‑ready)
-- Safe to run in Supabase SQL Editor (idempotent where possible)
--
-- This file merges your original schema + seeds and adds:
--    • Scan-based Check-in/Check-out via email domain whitelist + per-user PIN (hashed)
--    • Constraints to prevent bad data (double open sessions, checkout before checkin)
--    • RPCs: rpc_scan_check_in / rpc_scan_check_out
--    • Admin utility: admin_set_scan_code, and domain checker
--    • (Optional) equipment loan stock maintenance triggers – commented; enable if needed
--
-- Notes:
--    • Replace 'university.ac.th' below with your real university domain.
--    • Call admin_set_scan_code from a server environment using the Service Role key.
--    • The RPCs are SECURITY DEFINER and validate domain + PIN before writing.
--
-- -----------------------------------------------------------------------------
-- 0) ENUM types
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_type') THEN
    CREATE TYPE user_type AS ENUM ('STUDENT', 'STAFF');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'loan_status') THEN
    CREATE TYPE loan_status AS ENUM ('BORROWED', 'RETURNED');
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 1) Core tables (original)
CREATE TABLE IF NOT EXISTS public.users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  first_name  VARCHAR(100) NOT NULL,
  last_name   VARCHAR(100) NOT NULL,
  user_type   user_type    NOT NULL,
  email       VARCHAR(255) NOT NULL UNIQUE,
  department  VARCHAR(120),
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.sport_facility (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_name VARCHAR(150) NOT NULL,
  location      VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.equipment (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  equipment_name VARCHAR(150) NOT NULL,
  quantity       INT NOT NULL CHECK (quantity >= 0),
  available      INT NOT NULL CHECK (available >= 0),
  in_use         INT NOT NULL CHECK (in_use >= 0),
  maintenance    INT NOT NULL CHECK (maintenance >= 0),
  CONSTRAINT equipment_qty_consistency CHECK (quantity = available + in_use + maintenance)
);

CREATE TABLE IF NOT EXISTS public.equipment_loan (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id      BIGINT NOT NULL REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  equipment_id BIGINT NOT NULL REFERENCES public.equipment(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  loan_time    TIMESTAMPTZ NOT NULL,
  return_time  TIMESTAMPTZ,
  status       loan_status NOT NULL,
  CONSTRAINT equipment_loan_return_consistency CHECK (
    (status = 'BORROWED' AND return_time IS NULL) OR
    (status = 'RETURNED' AND return_time IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS public.usage_log (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id       BIGINT NOT NULL REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  facility_id   BIGINT NOT NULL REFERENCES public.sport_facility(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  checkin_time  TIMESTAMPTZ NOT NULL,
  checkout_time TIMESTAMPTZ
);

-- Helpful indexes (original)
CREATE INDEX IF NOT EXISTS idx_equipment_loan_user ON public.equipment_loan(user_id);
CREATE INDEX IF NOT EXISTS idx_equipment_loan_equipment ON public.equipment_loan(equipment_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_user ON public.usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_facility ON public.usage_log(facility_id);

-- Natural key protections
CREATE UNIQUE INDEX IF NOT EXISTS idx_uq_sport_facility_name ON public.sport_facility (facility_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_uq_equipment_name     ON public.equipment (equipment_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_uq_equipment_loan_user_equipment_loantime
  ON public.equipment_loan (user_id, equipment_id, loan_time);
CREATE UNIQUE INDEX IF NOT EXISTS idx_uq_usage_log_user_facility_checkin
  ON public.usage_log (user_id, facility_id, checkin_time);

-- -----------------------------------------------------------------------------
-- 2) Seed data (idempotent)
INSERT INTO public.users (first_name,last_name,user_type,email,department) VALUES
  ('Achiraya','Keawgunga','STUDENT','achiraya@example.com','ICT'),
  ('Hathayachon','Tansakul','STUDENT','hathayachon@example.com','ICT'),
  ('Aman','Aligae','STUDENT','aman@example.com','ICT'),
  ('Amornporn','Onkhoksung','STUDENT','amornporn@example.com','ICT'),
  ('Nicha','Sukdee','STAFF','nicha@university.ac.th','Sports Center'),
  ('Krit','Phasuk','STAFF','krit@university.ac.th','Facility Mgmt'),
  ('Ploy','Rattanaporn','STUDENT','ploy@example.com','ICT'),
  ('Mark','Sophon','STUDENT','mark@example.com','Engineering')
ON CONFLICT (email) DO NOTHING;

INSERT INTO public.sport_facility (facility_name, location) VALUES
  ('Badminton Dome A','Complex 1'),
  ('Outdoor Tennis Court','Complex 2'),
  ('Fitness Room','Main Building 2F')
ON CONFLICT (facility_name) DO NOTHING;

INSERT INTO public.equipment (equipment_name, quantity, available, in_use, maintenance) VALUES
  ('Badminton Racket',20,14,5,1),
  ('Shuttlecocks Tube',30,20,8,2),
  ('Tennis Racket',12,8,3,1),
  ('Tennis Balls (can)',24,18,6,0),
  ('Yoga Mat',15,12,2,1),
  ('Dumbbell Set',10,7,3,0),
  ('Stopwatch',6,6,0,0),
  ('Jump Rope',10,9,1,0)
ON CONFLICT (equipment_name) DO NOTHING;

INSERT INTO public.equipment_loan (user_id, equipment_id, loan_time, return_time, status)
SELECT  u.id, e.id,
        x.loan_time::timestamptz,
        x.return_time::timestamptz,
        x.status::loan_status
FROM (
  VALUES
    ('achiraya@example.com','Badminton Racket','2025-09-11 08:30:00','2025-09-11 09:45:00','RETURNED'),
    ('hathayachon@example.com','Shuttlecocks Tube','2025-09-11 08:20:00','2025-09-11 09:30:00','RETURNED'),
    ('aman@example.com','Tennis Racket','2025-09-11 10:00:00',NULL,'BORROWED'),
    ('ploy@example.com','Tennis Balls (can)','2025-09-11 07:50:00','2025-09-11 08:40:00','RETURNED'),
    ('mark@example.com','Yoga Mat','2025-09-11 09:10:00',NULL,'BORROWED'),
    ('nicha@university.ac.th','Dumbbell Set','2025-09-11 09:20:00',NULL,'BORROWED')
) AS x(email, equipment_name, loan_time, return_time, status)
JOIN public.users u      ON u.email = x.email
JOIN public.equipment e  ON e.equipment_name = x.equipment_name
ON CONFLICT (user_id, equipment_id, loan_time) DO NOTHING;

INSERT INTO public.usage_log (user_id, facility_id, checkin_time, checkout_time)
SELECT  u.id, f.id,
        x.checkin_time::timestamptz,
        x.checkout_time::timestamptz
FROM (
  VALUES
    ('achiraya@example.com','Badminton Dome A','2025-09-11 07:30:00','2025-09-11 09:00:00'),
    ('hathayachon@example.com','Badminton Dome A','2025-09-11 07:40:00','2025-09-11 09:10:00'),
    ('ploy@example.com','Outdoor Tennis Court','2025-09-11 07:10:00','2025-09-11 08:20:00'),
    ('mark@example.com','Fitness Room','2025-09-11 09:30:00','2025-09-11 10:30:00'),
    ('nicha@university.ac.th','Fitness Room','2025-09-11 10:15:00',NULL)
) AS x(email, facility_name, checkin_time, checkout_time)
JOIN public.users u           ON u.email = x.email
JOIN public.sport_facility f  ON f.facility_name = x.facility_name
ON CONFLICT (user_id, facility_id, checkin_time) DO NOTHING;

-- Views (original + helpful)
CREATE OR REPLACE VIEW public.vw_current_loans AS
SELECT u.first_name, u.last_name, e.equipment_name, l.loan_time
FROM public.equipment_loan l
JOIN public.users u ON u.id = l.user_id
JOIN public.equipment e ON e.id = l.equipment_id
WHERE l.status = 'BORROWED';

CREATE OR REPLACE VIEW public.vw_current_facility_presence AS
SELECT
  f.facility_name,
  u.first_name, u.last_name, u.email,
  ul.checkin_time
FROM public.usage_log ul
JOIN public.users u ON u.id = ul.user_id
JOIN public.sport_facility f ON f.id = ul.facility_id
WHERE ul.checkout_time IS NULL;

-- -----------------------------------------------------------------------------
-- 3) Extensions & supporting tables for scan gating
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for crypt / gen_salt

CREATE TABLE IF NOT EXISTS public.allowed_email_domain (
  domain text PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Replace with your real university domain(s)
INSERT INTO public.allowed_email_domain(domain) VALUES
  ('university.ac.th')
ON CONFLICT DO NOTHING;

-- CREATE TABLE to store hashed PIN per user
CREATE TABLE IF NOT EXISTS public.user_scan_code (
  user_id    bigint PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
  code_hash  text   NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_user_scan_code_touch ON public.user_scan_code;
CREATE TRIGGER trg_user_scan_code_touch
BEFORE UPDATE ON public.user_scan_code
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

-- -----------------------------------------------------------------------------
-- 4) Data quality for usage_log (scan presence)
ALTER TABLE public.usage_log
  DROP CONSTRAINT IF EXISTS chk_usage_checkout_after_checkin;
ALTER TABLE public.usage_log
  ADD  CONSTRAINT chk_usage_checkout_after_checkin
  CHECK (checkout_time IS NULL OR checkout_time > checkin_time);

-- One open session per (user, facility)
CREATE UNIQUE INDEX IF NOT EXISTS uq_open_usage_per_user_facility
ON public.usage_log (user_id, facility_id)
WHERE checkout_time IS NULL;

-- -----------------------------------------------------------------------------
-- 5) Utilities & RPCs
-- 5.1 Domain checker
CREATE OR REPLACE FUNCTION public.is_email_domain_allowed(p_email text)
RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.allowed_email_domain d
    WHERE lower(split_part(p_email, '@', 2)) = lower(d.domain)
  );
$$;

-- 5.2 Admin: set/change PIN (store as hash)
CREATE OR REPLACE FUNCTION public.admin_set_scan_code(p_email text, p_plain_code text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_user_id bigint;
BEGIN
  SELECT id INTO v_user_id FROM public.users WHERE email = p_email;
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'USER_NOT_FOUND';
  END IF;

  INSERT INTO public.user_scan_code (user_id, code_hash)
  VALUES (v_user_id, crypt(p_plain_code, gen_salt('bf')))
  ON CONFLICT (user_id) DO UPDATE
    SET code_hash = EXCLUDED.code_hash,
        updated_at = now();
END;
$$;

-- 5.3 RPC: scan Check-in
CREATE OR REPLACE FUNCTION public.rpc_scan_check_in(
  p_email         text,
  p_plain_code    text,
  p_facility_name text
) RETURNS public.usage_log
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_user_id     bigint;
  v_facility_id bigint;
  v_hash        text;
  rec           public.usage_log;
BEGIN
  IF NOT public.is_email_domain_allowed(p_email) THEN
    RAISE EXCEPTION 'EMAIL_DOMAIN_NOT_ALLOWED';
  END IF;

  SELECT id INTO v_user_id FROM public.users WHERE email = p_email;
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'USER_NOT_FOUND';
  END IF;

  SELECT id INTO v_facility_id FROM public.sport_facility WHERE facility_name = p_facility_name;
  IF v_facility_id IS NULL THEN
    RAISE EXCEPTION 'FACILITY_NOT_FOUND';
  END IF;

  SELECT code_hash INTO v_hash FROM public.user_scan_code WHERE user_id = v_user_id;
  IF v_hash IS NULL THEN
    RAISE EXCEPTION 'CODE_NOT_SET';
  END IF;
  IF crypt(p_plain_code, v_hash) <> v_hash THEN
    RAISE EXCEPTION 'INVALID_CODE';
  END IF;

  INSERT INTO public.usage_log (user_id, facility_id, checkin_time)
  VALUES (v_user_id, v_facility_id, now())
  RETURNING * INTO rec;

  RETURN rec;
END;
$$;

-- 5.4 RPC: scan Check-out
CREATE OR REPLACE FUNCTION public.rpc_scan_check_out(
  p_email         text,
  p_plain_code    text,
  p_facility_name text
) RETURNS public.usage_log
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_user_id     bigint;
  v_facility_id bigint;
  v_hash        text;
  rec           public.usage_log;
BEGIN
  IF NOT public.is_email_domain_allowed(p_email) THEN
    RAISE EXCEPTION 'EMAIL_DOMAIN_NOT_ALLOWED';
  END IF;

  SELECT id INTO v_user_id FROM public.users WHERE email = p_email;
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'USER_NOT_FOUND';
  END IF;

  SELECT id INTO v_facility_id FROM public.sport_facility WHERE facility_name = p_facility_name;
  IF v_facility_id IS NULL THEN
    RAISE EXCEPTION 'FACILITY_NOT_FOUND';
  END IF;

  SELECT code_hash INTO v_hash FROM public.user_scan_code WHERE user_id = v_user_id;
  IF v_hash IS NULL THEN
    RAISE EXCEPTION 'CODE_NOT_SET';
  END IF;
  IF crypt(p_plain_code, v_hash) <> v_hash THEN
    RAISE EXCEPTION 'INVALID_CODE';
  END IF;

  UPDATE public.usage_log
     SET checkout_time = now()
   WHERE user_id = v_user_id
     AND facility_id = v_facility_id
     AND checkout_time IS NULL
  RETURNING * INTO rec;

  RETURN rec; -- NULL if no open session
END;
$$;

-- -----------------------------------------------------------------------------
-- 6) (Optional) Equipment auto stock maintenance triggers
-- Enable if you want automatic available/in_use adjustments on loan/return.
-- This does NOT modify historical seed rows; only affects new changes.
/*
CREATE OR REPLACE FUNCTION public.equipment_on_borrow()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  -- only when moving into BORROWED state on insert
  IF NEW.status = 'BORROWED' THEN
    UPDATE public.equipment
       SET available = available - 1,
           in_use    = in_use + 1
     WHERE id = NEW.equipment_id
       AND available > 0;
    -- Ensure constraint still holds
    PERFORM 1 FROM public.equipment WHERE id = NEW.equipment_id AND available >= 0;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'NO_STOCK_AVAILABLE';
    END IF;
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION public.equipment_on_return()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  -- only when changing BORROWED -> RETURNED
  IF OLD.status = 'BORROWED' AND NEW.status = 'RETURNED' THEN
    UPDATE public.equipment
       SET available = available + 1,
           in_use    = in_use - 1
     WHERE id = NEW.equipment_id;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_equipment_loan_insert ON public.equipment_loan;
CREATE TRIGGER trg_equipment_loan_insert
AFTER INSERT ON public.equipment_loan
FOR EACH ROW EXECUTE FUNCTION public.equipment_on_borrow();

DROP TRIGGER IF EXISTS trg_equipment_loan_update ON public.equipment_loan;
CREATE TRIGGER trg_equipment_loan_update
AFTER UPDATE ON public.equipment_loan
FOR EACH ROW EXECUTE FUNCTION public.equipment_on_return();
*/

-- -----------------------------------------------------------------------------
-- 7) (Optional) Quick test helpers (COMMENT OUT in production)
-- select public.admin_set_scan_code('nicha@university.ac.th', '123456');
-- select public.rpc_scan_check_in('nicha@university.ac.th', '123456', 'Fitness Room');
-- select public.rpc_scan_check_out('nicha@university.ac.th', '123456', 'Fitness Room');
