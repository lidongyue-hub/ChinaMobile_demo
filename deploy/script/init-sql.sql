-- 初始化数据库 schema（MySQL 8+）
-- 目标库：source_agent（若未存在则创建）

DROP DATABASE IF EXISTS source_agent;
CREATE DATABASE IF NOT EXISTS source_agent
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE source_agent;

CREATE TABLE IF NOT EXISTS conversations (
    -- 会话表：记录会话名称、首条用户问题
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    name VARCHAR(255) NOT NULL,
    first_user_message TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    pinned TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶（1 置顶，0 普通）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS messages (
    -- 消息表：会话内的历史消息
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    conversation_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    deep_thinking TEXT NULL,
    model VARCHAR(100) NULL,
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    INDEX idx_messages_conversation (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
