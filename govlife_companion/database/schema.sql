CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  login_id TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  department TEXT,
  job_type TEXT,
  date_of_joining TEXT,
  expected_retirement_date TEXT,
  monthly_salary REAL DEFAULT 0,
  city TEXT,
  family_size INTEGER DEFAULT 1,
  preferred_language TEXT DEFAULT 'English',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS salary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  month TEXT,
  amount REAL DEFAULT 0,
  source TEXT DEFAULT 'Salary',
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  expense_date TEXT,
  category TEXT,
  amount REAL DEFAULT 0,
  expense_type TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  loan_type TEXT,
  bank_name TEXT,
  loan_amount REAL DEFAULT 0,
  interest_rate REAL DEFAULT 0,
  emi_amount REAL DEFAULT 0,
  start_date TEXT,
  end_date TEXT,
  remaining_balance REAL DEFAULT 0,
  due_day INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS family_members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT,
  relation TEXT,
  date_of_birth TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  member_name TEXT,
  record_date TEXT,
  bp_systolic INTEGER,
  bp_diastolic INTEGER,
  sugar REAL,
  weight REAL,
  medicine TEXT,
  reminder_date TEXT,
  appointment_date TEXT,
  checkup_date TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS education (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  child_name TEXT,
  institution TEXT,
  class_course TEXT,
  fee_amount REAL DEFAULT 0,
  fee_due_date TEXT,
  exam_date TEXT,
  tuition_fee REAL DEFAULT 0,
  savings_goal REAL DEFAULT 0,
  scholarship_notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transfers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  item TEXT,
  city TEXT,
  rent_estimate REAL DEFAULT 0,
  category TEXT,
  completed INTEGER DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  destination TEXT,
  people INTEGER DEFAULT 1,
  start_date TEXT,
  end_date TEXT,
  hotel_budget REAL DEFAULT 0,
  food_budget REAL DEFAULT 0,
  transport_budget REAL DEFAULT 0,
  other_budget REAL DEFAULT 0,
  leave_balance REAL DEFAULT 0,
  packing_item TEXT,
  packed INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retirement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  retirement_date TEXT,
  pension_estimate REAL DEFAULT 0,
  pf_nps_savings REAL DEFAULT 0,
  gratuity_estimate REAL DEFAULT 0,
  corpus_goal REAL DEFAULT 0,
  post_retirement_expense REAL DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title TEXT,
  category TEXT,
  reminder_date TEXT,
  repeat_type TEXT,
  priority TEXT,
  status TEXT DEFAULT 'Pending',
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_chat_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  chat_id TEXT,
  role TEXT,
  message TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  leave_type TEXT,
  from_date TEXT,
  to_date TEXT,
  days REAL DEFAULT 0,
  reason TEXT,
  status TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_balance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  total_cl REAL DEFAULT 0,
  used_cl REAL DEFAULT 0,
  remaining_cl REAL DEFAULT 0,
  total_el REAL DEFAULT 0,
  used_el REAL DEFAULT 0,
  remaining_el REAL DEFAULT 0,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pf_tracker (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  pf_account_type TEXT,
  employee_contribution REAL DEFAULT 0,
  employer_contribution REAL DEFAULT 0,
  current_balance REAL DEFAULT 0,
  interest_rate REAL DEFAULT 0,
  joining_date TEXT,
  retirement_date TEXT,
  nominee_name TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS insurance_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  policy_name TEXT,
  company_name TEXT,
  policy_number TEXT,
  insurance_type TEXT,
  insured_person_name TEXT,
  sum_assured REAL DEFAULT 0,
  premium_amount REAL DEFAULT 0,
  premium_frequency TEXT,
  start_date TEXT,
  renewal_date TEXT,
  maturity_date TEXT,
  nominee_name TEXT,
  status TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  setting_key TEXT,
  setting_value TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  email_enabled INTEGER DEFAULT 0,
  smtp_host TEXT,
  smtp_port INTEGER DEFAULT 587,
  smtp_username TEXT,
  smtp_password TEXT,
  sender_email TEXT,
  receiver_email TEXT,
  whatsapp_number TEXT,
  sms_number TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  channel TEXT,
  title TEXT,
  message TEXT,
  status TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
