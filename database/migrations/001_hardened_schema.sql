CREATE TABLE IF NOT EXISTS "meta_schema_migrations" (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  checksum TEXT NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  applied_by TEXT NOT NULL DEFAULT 'karakuri'
);

CREATE TABLE IF NOT EXISTS "meta_schema_catalog" (
  table_name TEXT PRIMARY KEY,
  table_kind TEXT NOT NULL,
  purpose TEXT NOT NULL,
  created_by_migration INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS "idx_meta_schema_catalog_kind" ON "meta_schema_catalog" ("table_kind");

CREATE TABLE IF NOT EXISTS "security_principals" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  principal_key TEXT NOT NULL UNIQUE,
  principal_type TEXT NOT NULL CHECK (principal_type IN ('user','device','service')),
  display_name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_security_principals_type" ON "security_principals" ("principal_type");

CREATE TRIGGER IF NOT EXISTS "trg_security_principals_touch"
AFTER UPDATE ON "security_principals"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "security_principals" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "security_roles" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  role_key TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT ''
);

CREATE TRIGGER IF NOT EXISTS "trg_security_roles_touch"
AFTER UPDATE ON "security_roles"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "security_roles" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "security_role_assignments" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  principal_key TEXT NOT NULL,
  role_key TEXT NOT NULL,
  reason TEXT NOT NULL,
  expires_at TEXT,
  UNIQUE (principal_key, role_key)
);

CREATE INDEX IF NOT EXISTS "idx_security_role_assignments_principal" ON "security_role_assignments" ("principal_key");

CREATE TRIGGER IF NOT EXISTS "trg_security_role_assignments_touch"
AFTER UPDATE ON "security_role_assignments"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "security_role_assignments" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "security_capabilities" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  role_key TEXT NOT NULL,
  capability TEXT NOT NULL,
  allow INTEGER NOT NULL DEFAULT 0 CHECK (allow IN (0,1)),
  UNIQUE (role_key, capability)
);

CREATE TRIGGER IF NOT EXISTS "trg_security_capabilities_touch"
AFTER UPDATE ON "security_capabilities"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "security_capabilities" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "security_sessions" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  session_key TEXT NOT NULL UNIQUE,
  principal_key TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  client_ref TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS "idx_security_sessions_principal" ON "security_sessions" ("principal_key");

CREATE TRIGGER IF NOT EXISTS "trg_security_sessions_touch"
AFTER UPDATE ON "security_sessions"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "security_sessions" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "audit_event_log" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  event_name TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('debug','info','notice','warning','error','critical'))
);

CREATE INDEX IF NOT EXISTS "idx_audit_event_log_event" ON "audit_event_log" ("event_name");

CREATE INDEX IF NOT EXISTS "idx_audit_event_log_created" ON "audit_event_log" ("created_at");

CREATE TRIGGER IF NOT EXISTS "trg_audit_event_log_touch"
AFTER UPDATE ON "audit_event_log"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "audit_event_log" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "audit_event_chain" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  event_key TEXT NOT NULL UNIQUE,
  previous_hash TEXT NOT NULL DEFAULT '',
  record_hash TEXT NOT NULL UNIQUE,
  signature TEXT NOT NULL DEFAULT ''
);

CREATE TRIGGER IF NOT EXISTS "trg_audit_event_chain_touch"
AFTER UPDATE ON "audit_event_chain"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "audit_event_chain" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "robot_missions" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  mission_key TEXT NOT NULL UNIQUE,
  requested_by TEXT NOT NULL DEFAULT 'local',
  state TEXT NOT NULL CHECK (state IN ('queued','running','paused','done','failed','blocked')),
  priority INTEGER NOT NULL DEFAULT 5 CHECK (priority BETWEEN 0 AND 10)
);

CREATE INDEX IF NOT EXISTS "idx_robot_missions_state" ON "robot_missions" ("state");

CREATE TRIGGER IF NOT EXISTS "trg_robot_missions_touch"
AFTER UPDATE ON "robot_missions"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "robot_missions" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "robot_mission_steps" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  mission_key TEXT NOT NULL,
  step_index INTEGER NOT NULL CHECK (step_index >= 0),
  action TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('pending','running','done','failed','skipped')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  UNIQUE (mission_key, step_index)
);

CREATE INDEX IF NOT EXISTS "idx_robot_mission_steps_mission" ON "robot_mission_steps" ("mission_key");

CREATE TRIGGER IF NOT EXISTS "trg_robot_mission_steps_touch"
AFTER UPDATE ON "robot_mission_steps"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "robot_mission_steps" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "robot_safety_envelopes" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  envelope_key TEXT NOT NULL UNIQUE,
  max_joint_velocity_rad_s REAL NOT NULL CHECK (max_joint_velocity_rad_s > 0),
  max_linear_velocity_m_s REAL NOT NULL CHECK (max_linear_velocity_m_s > 0),
  active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_robot_safety_envelopes_touch"
AFTER UPDATE ON "robot_safety_envelopes"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "robot_safety_envelopes" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "robot_stop_events" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  stop_key TEXT NOT NULL UNIQUE,
  stop_kind TEXT NOT NULL CHECK (stop_kind IN ('software','physical','watchdog','remote')),
  reason TEXT NOT NULL,
  cleared_at TEXT,
  cleared_by TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS "idx_robot_stop_events_kind" ON "robot_stop_events" ("stop_kind");

CREATE TRIGGER IF NOT EXISTS "trg_robot_stop_events_touch"
AFTER UPDATE ON "robot_stop_events"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "robot_stop_events" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "hardware_components" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  component_key TEXT NOT NULL UNIQUE,
  component_type TEXT NOT NULL,
  sku TEXT NOT NULL DEFAULT '',
  serial_number TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','installed','retired','failed'))
);

CREATE INDEX IF NOT EXISTS "idx_hardware_components_type" ON "hardware_components" ("component_type");

CREATE TRIGGER IF NOT EXISTS "trg_hardware_components_touch"
AFTER UPDATE ON "hardware_components"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "hardware_components" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "hardware_sensor_samples" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  sensor_key TEXT NOT NULL,
  sample_time TEXT NOT NULL,
  unit TEXT NOT NULL,
  value REAL NOT NULL,
  quality TEXT NOT NULL DEFAULT 'ok' CHECK (quality IN ('ok','stale','estimated','fault'))
);

CREATE INDEX IF NOT EXISTS "idx_hardware_sensor_samples_sensor" ON "hardware_sensor_samples" ("sensor_key", "sample_time");

CREATE TRIGGER IF NOT EXISTS "trg_hardware_sensor_samples_touch"
AFTER UPDATE ON "hardware_sensor_samples"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "hardware_sensor_samples" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "hardware_motor_commands" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  motor_key TEXT NOT NULL,
  command_time TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('disabled','velocity','position','torque')),
  setpoint REAL NOT NULL,
  limited INTEGER NOT NULL DEFAULT 0 CHECK (limited IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_hardware_motor_commands_motor" ON "hardware_motor_commands" ("motor_key", "command_time");

CREATE TRIGGER IF NOT EXISTS "trg_hardware_motor_commands_touch"
AFTER UPDATE ON "hardware_motor_commands"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "hardware_motor_commands" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "battery_packs" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  pack_key TEXT NOT NULL UNIQUE,
  chemistry TEXT NOT NULL,
  series_cells INTEGER NOT NULL CHECK (series_cells > 0),
  capacity_mah INTEGER NOT NULL CHECK (capacity_mah > 0),
  health_pct REAL NOT NULL DEFAULT 100 CHECK (health_pct BETWEEN 0 AND 100)
);

CREATE TRIGGER IF NOT EXISTS "trg_battery_packs_touch"
AFTER UPDATE ON "battery_packs"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "battery_packs" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "battery_cell_samples" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  pack_key TEXT NOT NULL,
  cell_index INTEGER NOT NULL CHECK (cell_index >= 0),
  sample_time TEXT NOT NULL,
  voltage_v REAL NOT NULL CHECK (voltage_v >= 0),
  temperature_c REAL NOT NULL,
  balancing INTEGER NOT NULL DEFAULT 0 CHECK (balancing IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_battery_cell_samples_pack" ON "battery_cell_samples" ("pack_key", "sample_time");

CREATE TRIGGER IF NOT EXISTS "trg_battery_cell_samples_touch"
AFTER UPDATE ON "battery_cell_samples"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "battery_cell_samples" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "ros_node_registry" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  node_name TEXT NOT NULL UNIQUE,
  package_name TEXT NOT NULL,
  required INTEGER NOT NULL DEFAULT 1 CHECK (required IN (0,1)),
  heartbeat_timeout_ms INTEGER NOT NULL CHECK (heartbeat_timeout_ms > 0)
);

CREATE TRIGGER IF NOT EXISTS "trg_ros_node_registry_touch"
AFTER UPDATE ON "ros_node_registry"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "ros_node_registry" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "ros_topic_registry" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  topic_name TEXT NOT NULL UNIQUE,
  message_type TEXT NOT NULL,
  publisher_node TEXT NOT NULL DEFAULT '',
  subscriber_node TEXT NOT NULL DEFAULT '',
  qos_profile TEXT NOT NULL DEFAULT 'default'
);

CREATE TRIGGER IF NOT EXISTS "trg_ros_topic_registry_touch"
AFTER UPDATE ON "ros_topic_registry"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "ros_topic_registry" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "maintenance_work_orders" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  work_order_key TEXT NOT NULL UNIQUE,
  component_key TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','waiting','done','cancelled')),
  severity TEXT NOT NULL DEFAULT 'normal' CHECK (severity IN ('low','normal','high','urgent'))
);

CREATE INDEX IF NOT EXISTS "idx_maintenance_work_orders_state" ON "maintenance_work_orders" ("state");

CREATE TRIGGER IF NOT EXISTS "trg_maintenance_work_orders_touch"
AFTER UPDATE ON "maintenance_work_orders"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "maintenance_work_orders" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "inventory_parts" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  part_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  vendor TEXT NOT NULL DEFAULT '',
  sku TEXT NOT NULL DEFAULT '',
  on_hand INTEGER NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
  reorder_at INTEGER NOT NULL DEFAULT 0 CHECK (reorder_at >= 0)
);

CREATE TRIGGER IF NOT EXISTS "trg_inventory_parts_touch"
AFTER UPDATE ON "inventory_parts"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "inventory_parts" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "bom_line_items" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  bom_key TEXT NOT NULL,
  part_key TEXT NOT NULL,
  quantity REAL NOT NULL CHECK (quantity > 0),
  assembly_ref TEXT NOT NULL DEFAULT '',
  approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_bom_line_items_bom" ON "bom_line_items" ("bom_key");

CREATE TRIGGER IF NOT EXISTS "trg_bom_line_items_touch"
AFTER UPDATE ON "bom_line_items"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "bom_line_items" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "calibration_profiles" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  profile_key TEXT NOT NULL UNIQUE,
  profile_type TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  valid INTEGER NOT NULL DEFAULT 0 CHECK (valid IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_calibration_profiles_touch"
AFTER UPDATE ON "calibration_profiles"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "calibration_profiles" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "diagnostic_runs" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  run_key TEXT NOT NULL UNIQUE,
  suite_name TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','passed','failed','cancelled'))
);

CREATE INDEX IF NOT EXISTS "idx_diagnostic_runs_status" ON "diagnostic_runs" ("status");

CREATE TRIGGER IF NOT EXISTS "trg_diagnostic_runs_touch"
AFTER UPDATE ON "diagnostic_runs"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "diagnostic_runs" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "diagnostic_results" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  run_key TEXT NOT NULL,
  check_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('passed','failed','warning','skipped')),
  duration_ms INTEGER NOT NULL DEFAULT 0 CHECK (duration_ms >= 0),
  UNIQUE (run_key, check_name)
);

CREATE INDEX IF NOT EXISTS "idx_diagnostic_results_run" ON "diagnostic_results" ("run_key");

CREATE TRIGGER IF NOT EXISTS "trg_diagnostic_results_touch"
AFTER UPDATE ON "diagnostic_results"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "diagnostic_results" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "stl_assets" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  asset_key TEXT NOT NULL UNIQUE,
  stl_path TEXT NOT NULL,
  source_path TEXT NOT NULL DEFAULT '',
  print_profile TEXT NOT NULL DEFAULT '',
  approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_stl_assets_touch"
AFTER UPDATE ON "stl_assets"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "stl_assets" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "stl_validation_results" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  asset_key TEXT NOT NULL,
  checked_at TEXT NOT NULL,
  boundary_edges INTEGER NOT NULL CHECK (boundary_edges >= 0),
  nonmanifold_edges INTEGER NOT NULL CHECK (nonmanifold_edges >= 0),
  zero_area_facets INTEGER NOT NULL CHECK (zero_area_facets >= 0),
  fits_printer INTEGER NOT NULL CHECK (fits_printer IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_stl_validation_results_asset" ON "stl_validation_results" ("asset_key", "checked_at");

CREATE TRIGGER IF NOT EXISTS "trg_stl_validation_results_touch"
AFTER UPDATE ON "stl_validation_results"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "stl_validation_results" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "firmware_builds" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  build_key TEXT NOT NULL UNIQUE,
  target_board TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  artifact_path TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK (status IN ('planned','built','failed','flashed'))
);

CREATE TRIGGER IF NOT EXISTS "trg_firmware_builds_touch"
AFTER UPDATE ON "firmware_builds"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "firmware_builds" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "firmware_flash_events" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  flash_key TEXT NOT NULL UNIQUE,
  build_key TEXT NOT NULL,
  device_ref TEXT NOT NULL,
  flashed_at TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1))
);

CREATE INDEX IF NOT EXISTS "idx_firmware_flash_events_device" ON "firmware_flash_events" ("device_ref");

CREATE TRIGGER IF NOT EXISTS "trg_firmware_flash_events_touch"
AFTER UPDATE ON "firmware_flash_events"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "firmware_flash_events" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "research_sources" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  domain TEXT NOT NULL UNIQUE,
  trust_score REAL NOT NULL DEFAULT 0.5 CHECK (trust_score BETWEEN 0 AND 1),
  allowed INTEGER NOT NULL DEFAULT 0 CHECK (allowed IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_research_sources_touch"
AFTER UPDATE ON "research_sources"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "research_sources" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "research_fetch_events" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  url TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued','fetched','denied','failed','cached')),
  http_status INTEGER,
  cache_key TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS "idx_research_fetch_events_domain" ON "research_fetch_events" ("domain");

CREATE TRIGGER IF NOT EXISTS "trg_research_fetch_events_touch"
AFTER UPDATE ON "research_fetch_events"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "research_fetch_events" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "promotion_candidates" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  candidate_key TEXT NOT NULL UNIQUE,
  source_path TEXT NOT NULL,
  target_path TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('draft','testing','passed','failed','promoted'))
);

CREATE TRIGGER IF NOT EXISTS "trg_promotion_candidates_touch"
AFTER UPDATE ON "promotion_candidates"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "promotion_candidates" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "promotion_results" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  candidate_key TEXT NOT NULL,
  result_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('passed','failed','skipped')),
  test_count INTEGER NOT NULL DEFAULT 0 CHECK (test_count >= 0)
);

CREATE INDEX IF NOT EXISTS "idx_promotion_results_candidate" ON "promotion_results" ("candidate_key");

CREATE TRIGGER IF NOT EXISTS "trg_promotion_results_touch"
AFTER UPDATE ON "promotion_results"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "promotion_results" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "configuration_entries" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  config_key TEXT NOT NULL UNIQUE,
  config_value TEXT NOT NULL,
  value_type TEXT NOT NULL CHECK (value_type IN ('text','integer','real','boolean','json')),
  valid INTEGER NOT NULL DEFAULT 1 CHECK (valid IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_configuration_entries_touch"
AFTER UPDATE ON "configuration_entries"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "configuration_entries" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "backup_manifests" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  backup_key TEXT NOT NULL UNIQUE,
  root_path TEXT NOT NULL,
  file_count INTEGER NOT NULL CHECK (file_count >= 0),
  byte_count INTEGER NOT NULL CHECK (byte_count >= 0),
  restore_verified INTEGER NOT NULL DEFAULT 0 CHECK (restore_verified IN (0,1))
);

CREATE TRIGGER IF NOT EXISTS "trg_backup_manifests_touch"
AFTER UPDATE ON "backup_manifests"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "backup_manifests" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "incident_reports" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  incident_key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
  state TEXT NOT NULL CHECK (state IN ('open','triage','mitigated','closed'))
);

CREATE INDEX IF NOT EXISTS "idx_incident_reports_state" ON "incident_reports" ("state");

CREATE TRIGGER IF NOT EXISTS "trg_incident_reports_touch"
AFTER UPDATE ON "incident_reports"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "incident_reports" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "incident_actions" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  incident_key TEXT NOT NULL,
  action_key TEXT NOT NULL UNIQUE,
  owner TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL CHECK (state IN ('open','doing','done','cancelled'))
);

CREATE INDEX IF NOT EXISTS "idx_incident_actions_incident" ON "incident_actions" ("incident_key");

CREATE TRIGGER IF NOT EXISTS "trg_incident_actions_touch"
AFTER UPDATE ON "incident_actions"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "incident_actions" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "simulation_runs" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  simulation_key TEXT NOT NULL UNIQUE,
  world_name TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running','passed','failed','cancelled'))
);

CREATE TRIGGER IF NOT EXISTS "trg_simulation_runs_touch"
AFTER UPDATE ON "simulation_runs"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "simulation_runs" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "simulation_metrics" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT NOT NULL DEFAULT 'local',
  source_ref TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
  simulation_key TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  unit TEXT NOT NULL DEFAULT '',
  UNIQUE (simulation_key, metric_name)
);

CREATE INDEX IF NOT EXISTS "idx_simulation_metrics_run" ON "simulation_metrics" ("simulation_key");

CREATE TRIGGER IF NOT EXISTS "trg_simulation_metrics_touch"
AFTER UPDATE ON "simulation_metrics"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "simulation_metrics" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS "ledger_records" (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  domain TEXT NOT NULL CHECK (domain IN ('audit', 'safety', 'autonomy', 'battery', 'calibration', 'camera', 'cliff', 'controller', 'diagnostic', 'dock', 'drive', 'estop', 'firmware', 'gripper', 'imu', 'inventory', 'mapping', 'maintenance', 'motion', 'network', 'perception', 'planner', 'power', 'promotion', 'research', 'ros', 'simulation', 'stl', 'telemetry', 'vision')),
  stream TEXT NOT NULL CHECK (stream IN ('accepted', 'alerts', 'baselines', 'commands', 'events', 'failures', 'heartbeats', 'limits', 'metrics', 'observations', 'plans', 'proofs', 'samples', 'snapshots', 'states', 'transitions')),
  zone TEXT NOT NULL CHECK (zone IN ('ring0', 'ring1', 'ring2', 'robot', 'ros', 'firmware', 'field', 'lab')),
  producer TEXT NOT NULL,
  subject TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('debug','info','notice','warning','error','critical')),
  sequence_no INTEGER NOT NULL DEFAULT 0 CHECK (sequence_no >= 0),
  payload_json TEXT NOT NULL DEFAULT '{}',
  previous_hash TEXT NOT NULL DEFAULT '',
  record_hash TEXT NOT NULL CHECK (length(record_hash) BETWEEN 1 AND 128),
  retained_until TEXT,
  signature TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS "idx_ledger_records_partition_created" ON "ledger_records" ("domain", "stream", "zone", "created_at");

CREATE INDEX IF NOT EXISTS "idx_ledger_records_subject" ON "ledger_records" ("subject");

CREATE UNIQUE INDEX IF NOT EXISTS "idx_ledger_records_hash" ON "ledger_records" ("record_hash");

CREATE TRIGGER IF NOT EXISTS "trg_ledger_records_touch"
AFTER UPDATE ON "ledger_records"
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')
BEGIN
  UPDATE "ledger_records" SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE VIEW IF NOT EXISTS "v_ledger_records" AS
SELECT id, created_at, updated_at, domain, stream, zone, producer, subject, severity, sequence_no
FROM "ledger_records"
WHERE retained_until IS NULL OR retained_until >= strftime('%Y-%m-%dT%H:%M:%fZ','now');
