-- Создание базы данных OpenTalk
CREATE DATABASE IF NOT EXISTS opentalk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE opentalk;

-- Таблица пользователей (расширенная модель Django)
CREATE TABLE users_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined DATETIME NOT NULL,
    full_name VARCHAR(255) NULL,
    avatar VARCHAR(100) NULL,
    bio TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'offline',
    location VARCHAR(100) NULL,
    created_at DATETIME NOT NULL,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    theme_preference VARCHAR(10) NOT NULL DEFAULT 'light'
);

-- Группы пользователей (стандартная модель Django)
CREATE TABLE auth_group (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

-- Права пользователей (стандартная модель Django)
CREATE TABLE auth_permission (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id BIGINT NOT NULL,
    codename VARCHAR(100) NOT NULL
);

-- Связь пользователей с группами (стандартная модель Django)
CREATE TABLE users_user_groups (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES auth_group (id) ON DELETE CASCADE,
    UNIQUE (user_id, group_id)
);

-- Связь пользователей с правами (стандартная модель Django)
CREATE TABLE users_user_user_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES auth_permission (id) ON DELETE CASCADE,
    UNIQUE (user_id, permission_id)
);

-- Подписки между пользователями
CREATE TABLE users_subscription (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    follower_id BIGINT NOT NULL,
    followed_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (follower_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users_user (id) ON DELETE CASCADE,
    UNIQUE (follower_id, followed_id)
);

-- Посты пользователей
CREATE TABLE posts_post (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    media_urls TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    likes_count INT UNSIGNED NOT NULL DEFAULT 0,
    reposts_count INT UNSIGNED NOT NULL DEFAULT 0,
    comments_count INT UNSIGNED NOT NULL DEFAULT 0,
    is_repost BOOLEAN NOT NULL DEFAULT FALSE,
    original_post_id BIGINT NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (original_post_id) REFERENCES posts_post (id) ON DELETE SET NULL
);

-- Комментарии к постам
CREATE TABLE posts_comment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    parent_id BIGINT NULL,
    likes_count INT UNSIGNED NOT NULL DEFAULT 0,
    FOREIGN KEY (post_id) REFERENCES posts_post (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES posts_comment (id) ON DELETE SET NULL
);

-- Лайки к постам и комментариям
CREATE TABLE posts_like (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content_type VARCHAR(10) NOT NULL,
    content_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    UNIQUE (user_id, content_type, content_id)
);

-- Хештеги
CREATE TABLE posts_hashtag (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    post_count INT UNSIGNED NOT NULL DEFAULT 0
);

-- Связь поста с хештегами
CREATE TABLE posts_posthashtag (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT NOT NULL,
    hashtag_id BIGINT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts_post (id) ON DELETE CASCADE,
    FOREIGN KEY (hashtag_id) REFERENCES posts_hashtag (id) ON DELETE CASCADE,
    UNIQUE (post_id, hashtag_id)
);

-- Тренды
CREATE TABLE posts_trend (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hashtag_id BIGINT NOT NULL,
    trend_score FLOAT NOT NULL,
    category VARCHAR(50) NULL,
    location VARCHAR(100) NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (hashtag_id) REFERENCES posts_hashtag (id) ON DELETE CASCADE
);

-- Чаты
CREATE TABLE messages_api_chat (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NULL,
    is_group BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    avatar VARCHAR(100) NULL
);

-- Участники чата
CREATE TABLE messages_api_chatmember (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'member',
    joined_at DATETIME NOT NULL,
    last_read_message_id BIGINT NULL,
    FOREIGN KEY (chat_id) REFERENCES messages_api_chat (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    UNIQUE (chat_id, user_id)
);

-- Сообщения в чате
CREATE TABLE messages_api_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    sender_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    media_urls TEXT NULL,
    created_at DATETIME NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (chat_id) REFERENCES messages_api_chat (id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Обновление внешнего ключа для последнего прочитанного сообщения
ALTER TABLE messages_api_chatmember
ADD FOREIGN KEY (last_read_message_id) REFERENCES messages_api_message (id) ON DELETE SET NULL;

-- Голосовые каналы
CREATE TABLE voice_voicechannel (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    creator_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_participants INT UNSIGNED NOT NULL DEFAULT 10,
    FOREIGN KEY (creator_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Участники голосовых каналов
CREATE TABLE voice_voicechannelmember (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    joined_at DATETIME NOT NULL,
    mic_status BOOLEAN NOT NULL DEFAULT TRUE,
    speaker_status BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (channel_id) REFERENCES voice_voicechannel (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE,
    UNIQUE (channel_id, user_id)
);

-- Звонки
CREATE TABLE voice_call (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    caller_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    started_at DATETIME NOT NULL,
    ended_at DATETIME NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'missed',
    call_type VARCHAR(10) NOT NULL DEFAULT 'audio',
    FOREIGN KEY (caller_id) REFERENCES users_user (id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Уведомления
CREATE TABLE notifications_notification (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    reference_id BIGINT UNSIGNED NULL,
    reference_type VARCHAR(50) NULL,
    created_at DATETIME NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Премиум-подписки
CREATE TABLE notifications_premiumsubscription (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    started_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    payment_id VARCHAR(255) NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Стандартные таблицы для Django-сессий и админки
CREATE TABLE django_session (
    session_key VARCHAR(40) NOT NULL PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date DATETIME NOT NULL
);

CREATE TABLE django_admin_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    action_time DATETIME NOT NULL,
    object_id TEXT NULL,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT UNSIGNED NOT NULL,
    change_message TEXT NOT NULL,
    content_type_id BIGINT NULL,
    user_id BIGINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users_user (id) ON DELETE CASCADE
);

-- Таблица контент-типов Django
CREATE TABLE django_content_type (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE (app_label, model)
);

-- Таблица миграций Django
CREATE TABLE django_migrations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied DATETIME NOT NULL
);

-- Добавим индексы для оптимизации запросов
CREATE INDEX idx_post_created_at ON posts_post (created_at);
CREATE INDEX idx_post_user_id ON posts_post (user_id);
CREATE INDEX idx_comment_post_id ON posts_comment (post_id);
CREATE INDEX idx_message_chat_id ON messages_api_message (chat_id);
CREATE INDEX idx_notification_user_id ON notifications_notification (user_id);
CREATE INDEX idx_notification_created_at ON notifications_notification (created_at);
CREATE INDEX idx_subscription_follower_id ON users_subscription (follower_id);
CREATE INDEX idx_subscription_followed_id ON users_subscription (followed_id);
CREATE INDEX idx_voicemember_channel_id ON voice_voicechannelmember (channel_id);
CREATE INDEX idx_call_caller_id ON voice_call (caller_id);
CREATE INDEX idx_call_receiver_id ON voice_call (receiver_id);
CREATE INDEX idx_trending_score ON posts_trend (trend_score);

-- Добавим ограничение на допустимые значения для статусов и типов
ALTER TABLE users_user ADD CONSTRAINT chk_user_status CHECK (status IN ('online', 'offline', 'dnd'));
ALTER TABLE users_user ADD CONSTRAINT chk_theme_preference CHECK (theme_preference IN ('light', 'dark'));
ALTER TABLE posts_like ADD CONSTRAINT chk_content_type CHECK (content_type IN ('post', 'comment'));
ALTER TABLE voice_call ADD CONSTRAINT chk_call_status CHECK (status IN ('missed', 'answered', 'declined'));
ALTER TABLE voice_call ADD CONSTRAINT chk_call_type CHECK (call_type IN ('audio', 'video'));
ALTER TABLE notifications_premiumsubscription ADD CONSTRAINT chk_plan_type CHECK (plan_type IN ('monthly', 'yearly'));
ALTER TABLE notifications_notification ADD CONSTRAINT chk_notification_type CHECK (
    type IN ('like', 'comment', 'follow', 'mention', 'message', 'repost', 'system')
); 