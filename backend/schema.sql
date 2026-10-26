CREATE DATABASE IF NOT EXISTS intern_review;
USE intern_review;
CREATE TABLE IF NOT EXISTS interns (
  id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL UNIQUE,
  task VARCHAR(255), mentor VARCHAR(100), status VARCHAR(30) DEFAULT 'active');
CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY, intern_id INT NOT NULL, review_date DATE, review_time TIME,
  meeting_link VARCHAR(255), mentor VARCHAR(100),
  status ENUM('pending','completed','missed','rescheduled') DEFAULT 'pending',
  is_followup BOOLEAN DEFAULT FALSE, FOREIGN KEY (intern_id) REFERENCES interns(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS feedback (
  id INT AUTO_INCREMENT PRIMARY KEY, review_id INT NOT NULL, mentor_name VARCHAR(100), rating INT,
  comments TEXT, outcome ENUM('pass','needs_followup'), FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS email_logs (
  id INT AUTO_INCREMENT PRIMARY KEY, intern_id INT, review_id INT, type ENUM('review','followup','broadcast'),
  status ENUM('sent','failed'), error TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pending_actions (
  id INT AUTO_INCREMENT PRIMARY KEY, action_type VARCHAR(50), payload JSON,
  status ENUM('awaiting','executed','cancelled') DEFAULT 'awaiting', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS upload_batches (
  id INT AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(255), total_rows INT, valid_rows INT, error_rows INT,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
