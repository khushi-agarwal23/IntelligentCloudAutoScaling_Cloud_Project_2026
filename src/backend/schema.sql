-- Amazon RDS MySQL bootstrap schema. The Flask/SQLAlchemy app can also create these tables automatically.
CREATE DATABASE IF NOT EXISTS cloud_autoscaling;
USE cloud_autoscaling;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  amount DOUBLE NOT NULL,
  product VARCHAR(255) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'completed',
  created_at DATETIME NOT NULL,
  INDEX idx_transactions_user (user_id),
  INDEX idx_transactions_created (created_at),
  CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cpu_percent DOUBLE NOT NULL,
  memory_percent DOUBLE NOT NULL,
  request_rate DOUBLE NOT NULL,
  response_time_ms DOUBLE NOT NULL,
  instance_count INT NOT NULL DEFAULT 1,
  recorded_at DATETIME NOT NULL,
  INDEX idx_metrics_recorded (recorded_at)
);

CREATE TABLE IF NOT EXISTS scaling_decisions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  action VARCHAR(20) NOT NULL,
  desired_instances INT NOT NULL,
  reason TEXT NOT NULL,
  confidence DOUBLE NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  INDEX idx_scaling_created (created_at)
);
