# Полная документация API OpenTalk

Ниже представлена полная коллекция всех возможных запросов к API OpenTalk. Для каждого запроса указаны URL, HTTP-метод, необходимые заголовки, тело запроса и пример ответа.

## Содержание

1. [Аутентификация](#аутентификация)
2. [Пользователи](#пользователи)
3. [Посты](#посты)
4. [Комментарии](#комментарии)
5. [Хештеги и тренды](#хештеги-и-тренды)
6. [Чаты и сообщения](#чаты-и-сообщения)
7. [Голосовые каналы](#голосовые-каналы)
8. [Уведомления](#уведомления)
9. [Премиум-подписки](#премиум-подписки)

## Аутентификация

### Регистрация нового пользователя

**URL**: `POST /api/auth/register/`

**Требуется авторизация**: Нет

**Минимальный набор данных**:
```json
{
  "username": "example_user",
  "email": "user@example.com",
  "password": "securepassword123",
  "password2": "securepassword123"
}
```

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "user": {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "full_name": "example_user",
    "avatar": null,
    "bio": "",
    "status": "offline",
    "location": "",
    "created_at": "2023-03-18T18:00:00Z",
    "last_login": null,
    "is_premium": false,
    "is_verified": false,
    "theme_preference": "light"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Примечание**: По умолчанию поле `full_name` будет заполнено значением `username`. Вы можете обновить это поле позже через API обновления профиля.

### Вход в систему

**URL**: `POST /api/auth/login/`

**Требуется авторизация**: Нет

```json
{
  "username": "example_user",
  "password": "securepassword123"
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Обновление токена

**URL**: `POST /api/auth/refresh/`

**Требуется авторизация**: Нет

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Проверка токена

**URL**: `POST /api/auth/verify/`

**Требуется авторизация**: Нет

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{}
```

### Изменение пароля

**URL**: `POST /api/auth/change-password/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

```json
{
  "old_password": "securepassword123",
  "new_password": "newsecurepassword456",
  "new_password2": "newsecurepassword456"
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "message": "Пароль успешно изменен"
}
```

## Пользователи

### Получение данных текущего пользователя

**URL**: `GET /api/users/me/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "id": 1,
  "username": "example_user",
  "email": "user@example.com",
  "full_name": "example_user",
  "avatar": null,
  "bio": "",
  "status": "offline",
  "location": "",
  "created_at": "2023-03-18T18:00:00Z",
  "last_login": "2023-03-18T19:00:00Z",
  "is_premium": false,
  "is_verified": false,
  "theme_preference": "light",
  "followers_count": 0,
  "following_count": 0,
  "posts_count": 0,
  "is_following": false
}
```

### Обновление профиля

**URL**: `PUT /api/users/update_me/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Тело запроса** (можно обновлять любые доступные поля):
```json
{
  "full_name": "Иван Иванов",
  "bio": "Разработчик из Москвы",
  "status": "online",
  "location": "Москва",
  "theme_preference": "dark"
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "id": 1,
  "username": "example_user",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "avatar": null,
  "bio": "Разработчик из Москвы",
  "status": "online",
  "location": "Москва",
  "created_at": "2023-03-18T18:00:00Z",
  "last_login": "2023-03-18T19:00:00Z",
  "is_premium": false,
  "is_verified": false,
  "theme_preference": "dark"
}
```

### Обновление статуса пользователя

**URL**: `PATCH /api/users/update_status/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Тело запроса**:
```json
{
  "status": "online"
}
```

**Допустимые значения статуса**:
- `online` - Онлайн
- `offline` - Офлайн
- `dnd` или `do_not_disturb` - Не беспокоить

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "status": "online",
  "message": "Статус успешно обновлен"
}
```

### Получение списка всех пользователей

**URL**: `GET /api/users/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Параметры запроса**:
- `search`: Поиск по имени пользователя или полному имени
- `page`: Номер страницы

**Пример**: `GET /api/users/?search=иван&page=1`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "ivan123",
      "email": "ivan@example.com",
      "full_name": "Иван Иванов",
      "avatar": null,
      "bio": "Программист",
      "status": "online",
      "location": "Москва",
      "created_at": "2023-03-18T18:00:00Z",
      "last_login": "2023-03-18T19:00:00Z",
      "is_premium": false,
      "is_verified": false,
      "theme_preference": "light"
    },
    {
      "id": 2,
      "username": "ivanova",
      "email": "ivanova@example.com",
      "full_name": "Анна Иванова",
      "avatar": null,
      "bio": "Дизайнер",
      "status": "offline",
      "location": "Санкт-Петербург",
      "created_at": "2023-03-18T18:00:00Z",
      "last_login": "2023-03-18T19:00:00Z",
      "is_premium": false,
      "is_verified": false,
      "theme_preference": "dark"
    }
  ]
}
```

### Получение данных конкретного пользователя

**URL**: `GET /api/users/{id}/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `GET /api/users/2/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "id": 2,
  "username": "ivanova",
  "email": "ivanova@example.com",
  "full_name": "Анна Иванова",
  "avatar": null,
  "bio": "Дизайнер",
  "status": "offline",
  "location": "Санкт-Петербург",
  "created_at": "2023-03-18T18:00:00Z",
  "last_login": "2023-03-18T19:00:00Z",
  "is_premium": false,
  "is_verified": false,
  "theme_preference": "dark",
  "followers_count": 5,
  "following_count": 10,
  "posts_count": 23,
  "is_following": true
}
```

### Подписка на пользователя

**URL**: `POST /api/users/{id}/follow/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `POST /api/users/2/follow/`

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "status": "Вы успешно подписались"
}
```

### Отписка от пользователя

**URL**: `DELETE /api/users/{id}/unfollow/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `DELETE /api/users/2/unfollow/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "status": "Вы успешно отписались"
}
```

### Получение списка подписчиков пользователя

**URL**: `GET /api/users/{id}/followers/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `GET /api/users/2/followers/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "follower": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "followed": {
        "id": 2,
        "username": "ivanova",
        "full_name": "Анна Иванова",
        "avatar": null,
        "is_verified": false
      },
      "created_at": "2023-03-19T12:00:00Z"
    },
    {
      "id": 3,
      "follower": {
        "id": 3,
        "username": "petrov",
        "full_name": "Петр Петров",
        "avatar": null,
        "is_verified": false
      },
      "followed": {
        "id": 2,
        "username": "ivanova",
        "full_name": "Анна Иванова",
        "avatar": null,
        "is_verified": false
      },
      "created_at": "2023-03-20T10:00:00Z"
    }
  ]
}
```

### Получение списка подписок пользователя

**URL**: `GET /api/users/{id}/following/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `GET /api/users/1/following/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "follower": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "followed": {
        "id": 2,
        "username": "ivanova",
        "full_name": "Анна Иванова",
        "avatar": null,
        "is_verified": false
      },
      "created_at": "2023-03-19T12:00:00Z"
    },
    {
      "id": 2,
      "follower": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "followed": {
        "id": 3,
        "username": "petrov",
        "full_name": "Петр Петров",
        "avatar": null,
        "is_verified": false
      },
      "created_at": "2023-03-19T12:30:00Z"
    }
  ]
}
```

### Получение постов пользователя

**URL**: `GET /api/users/{id}/posts/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `GET /api/users/1/posts/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "content": "Мой первый пост в OpenTalk!",
      "media": [],
      "created_at": "2023-03-19T10:00:00Z",
      "updated_at": "2023-03-19T10:00:00Z",
      "likes_count": 3,
      "reposts_count": 1,
      "comments_count": 2,
      "is_repost": false,
      "original_post": null,
      "original_post_details": null,
      "is_liked": true,
      "hashtags": []
    },
    {
      "id": 2,
      "user": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "content": "Вот мое новое фото #OpenTalk",
      "media": ["media/post_media/example.jpg"],
      "created_at": "2023-03-20T15:30:00Z",
      "updated_at": "2023-03-20T15:30:00Z",
      "likes_count": 5,
      "reposts_count": 0,
      "comments_count": 1,
      "is_repost": false,
      "original_post": null,
      "original_post_details": null,
      "is_liked": false,
      "hashtags": [
        {
          "id": 1,
          "name": "opentalk",
          "post_count": 10
        }
      ]
    }
  ]
}
```

### Получение рекомендуемых пользователей

**URL**: `GET /api/users/suggested/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
[
  {
    "id": 4,
    "username": "sidorov",
    "full_name": "Сидор Сидоров",
    "avatar": null,
    "is_verified": false
  },
  {
    "id": 5,
    "username": "kuznetsova",
    "full_name": "Мария Кузнецова",
    "avatar": "media/avatars/maria.jpg",
    "is_verified": true
  }
]
```

## Посты

### Получение списка всех постов

**URL**: `GET /api/posts/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Параметры запроса**:
- `search`: Поиск по содержимому
- `username`: Фильтрация по имени пользователя
- `hashtag`: Фильтрация по хештегу
- `page`: Номер страницы

**Пример**: `GET /api/posts/?hashtag=opentalk&page=1`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "user": {
        "id": 1,
        "username": "example_user",
        "full_name": "Иван Иванов",
        "avatar": null,
        "is_verified": false
      },
      "content": "Вот мое новое фото #OpenTalk",
      "media": ["media/post_media/example.jpg"],
      "created_at": "2023-03-20T15:30:00Z",
      "updated_at": "2023-03-20T15:30:00Z",
      "likes_count": 5,
      "reposts_count": 0,
      "comments_count": 1,
      "is_repost": false,
      "original_post": null,
      "original_post_details": null,
      "is_liked": false,
      "hashtags": [
        {
          "id": 1,
          "name": "opentalk",
          "post_count": 10
        }
      ]
    },
    {
      "id": 3,
      "user": {
        "id": 2,
        "username": "ivanova",
        "full_name": "Анна Иванова",
        "avatar": null,
        "is_verified": false
      },
      "content": "Люблю этот проект #OpenTalk",
      "media": [],
      "created_at": "2023-03-21T12:00:00Z",
      "updated_at": "2023-03-21T12:00:00Z",
      "likes_count": 8,
      "reposts_count": 2,
      "comments_count": 3,
      "is_repost": false,
      "original_post": null,
      "original_post_details": null,
      "is_liked": true,
      "hashtags": [
        {
          "id": 1,
          "name": "opentalk",
          "post_count": 10
        }
      ]
    }
  ]
}
```

### Создание нового поста

**URL**: `POST /api/posts/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Тело запроса**:
```json
{
  "content": "Новый пост с хештегом #OpenTalk и фото",
  "media": ["media/post_media/photo1.jpg", "media/post_media/photo2.jpg"]
}
```

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "id": 4,
  "user": {
    "id": 1,
    "username": "example_user",
    "full_name": "Иван Иванов",
    "avatar": null,
    "is_verified": false
  },
  "content": "Новый пост с хештегом #OpenTalk и фото",
  "media": ["media/post_media/photo1.jpg", "media/post_media/photo2.jpg"],
  "created_at": "2023-03-22T10:15:00Z",
  "updated_at": "2023-03-22T10:15:00Z",
  "likes_count": 0,
  "reposts_count": 0,
  "comments_count": 0,
  "is_repost": false,
  "original_post": null,
  "original_post_details": null,
  "is_liked": false,
  "hashtags": [
    {
      "id": 1,
      "name": "opentalk",
      "post_count": 11
    }
  ]
}
```

### Получение конкретного поста

**URL**: `GET /api/posts/{id}/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример**: `GET /api/posts/4/`

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "id": 4,
  "user": {
    "id": 1,
    "username": "example_user",
    "full_name": "Иван Иванов",
    "avatar": null,
    "is_verified": false
  },
  "content": "Новый пост с хештегом #OpenTalk и фото",
  "media": ["media/post_media/photo1.jpg", "media/post_media/photo2.jpg"],
  "created_at": "2023-03-22T10:15:00Z",
  "updated_at": "2023-03-22T10:15:00Z",
  "likes_count": 0,
  "reposts_count": 0,
  "comments_count": 0,
  "is_repost": false,
  "original_post": null,
  "original_post_details": null,
  "is_liked": false,
  "hashtags": [
    {
      "id": 1,
      "name": "opentalk",
      "post_count": 11
    }
  ]
}
```

### Обновление поста

**URL**: `PUT /api/posts/{id}/`

**Требуется авторизация**: Да (только владелец поста или администратор)

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Тело запроса**:
```json
{
  "content": "Обновленный пост с хештегом #OpenTalk и фото"
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "id": 4,
  "user": {
    "id": 1,
    "username": "example_user",
    "full_name": "Иван Иванов",
    "avatar": null,
    "is_verified": false
  },
  "content": "Обновленный пост с хештегом #OpenTalk и фото",
  "media": ["media/post_media/photo1.jpg", "media/post_media/photo2.jpg"],
  "created_at": "2023-03-22T10:15:00Z",
  "updated_at": "2023-03-22T10:15:00Z",
  "likes_count": 0,
  "reposts_count": 0,
  "comments_count": 0,
  "is_repost": false,
  "original_post": null,
  "original_post_details": null,
  "is_liked": false,
  "hashtags": [
    {
      "id": 1,
      "name": "opentalk",
      "post_count": 11
    }
  ]
}
```

## Чаты и сообщения

### Получение списка чатов

**URL**: `GET /api/chats/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "ivanova",
      "full_name": "Анна Иванова",
      "avatar": "media/avatars/anna.jpg",
      "is_verified": false
    },
    "last_message": {
      "content": "Привет, как дела?",
      "timestamp": "2023-03-20T14:15:22Z"
    },
    "unread_count": 0,
    "is_pinned": false,
    "created_at": "2023-03-15T10:00:00Z"
  },
  {
    "id": 2,
    "user": {
      "id": 3,
      "username": "petrov",
      "full_name": "Петр Петров",
      "avatar": null,
      "is_verified": true
    },
    "last_message": {
      "content": "Спасибо за информацию!",
      "timestamp": "2023-03-21T09:30:15Z"
    },
    "unread_count": 2,
    "is_pinned": true,
    "created_at": "2023-03-18T12:00:00Z"
  }
]
```

### Создание нового чата

**URL**: `POST /api/chats/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

**Тело запроса**:
```json
{
  "userId": 3
}
```

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "id": 3,
  "user": {
    "id": 3,
    "username": "petrov",
    "full_name": "Петр Петров",
    "avatar": null,
    "is_verified": true
  },
  "created_at": "2023-03-22T15:45:30Z",
  "is_pinned": false
}
```

### Получение сообщений чата

**URL**: `GET /api/chats/{id}/messages/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Параметры запроса**:
- `limit`: количество сообщений (по умолчанию 50)
- `offset`: смещение для пагинации
- `sortOrder`: порядок сортировки ('asc' или 'desc')

**Пример запроса**: `GET /api/chats/1/messages/?limit=10&offset=0&sortOrder=desc`

**Ответ в случае успеха** (HTTP 200 OK):
```json
[
  {
    "id": 15,
    "chat": 1,
    "sender": {
      "id": 2,
      "username": "ivanova",
      "full_name": "Анна Иванова",
      "avatar": "media/avatars/anna.jpg",
      "is_verified": false
    },
    "content": "Привет, как дела?",
    "timestamp": "2023-03-20T14:15:22Z",
    "is_read": true,
    "attachments": []
  },
  {
    "id": 14,
    "chat": 1,
    "sender": {
      "id": 1,
      "username": "example_user",
      "full_name": "Иван Иванов",
      "avatar": null,
      "is_verified": false
    },
    "content": "Здравствуй! У меня всё хорошо, спасибо!",
    "timestamp": "2023-03-20T14:20:10Z",
    "is_read": true,
    "attachments": []
  }
]
```

### Отправка сообщения

**URL**: `POST /api/chats/{id}/messages/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

**Тело запроса**:
```json
{
  "content": "Привет! Как твои дела?",
  "attachments": [1, 2]
}
```

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "id": 16,
  "chat": 1,
  "sender": {
    "id": 1,
    "username": "example_user",
    "full_name": "Иван Иванов",
    "avatar": null,
    "is_verified": false
  },
  "content": "Привет! Как твои дела?",
  "timestamp": "2023-03-22T16:10:45Z",
  "is_read": false,
  "attachments": [
    {
      "id": 1,
      "file": "chat_attachments/document.pdf",
      "file_url": "http://example.com/media/chat_attachments/document.pdf",
      "file_type": "document",
      "file_name": "document.pdf",
      "file_size": 1245678,
      "upload_date": "2023-03-22T16:09:30Z",
      "uploader": 1
    },
    {
      "id": 2,
      "file": "chat_attachments/image.jpg",
      "file_url": "http://example.com/media/chat_attachments/image.jpg",
      "file_type": "image",
      "file_name": "image.jpg",
      "file_size": 345678,
      "upload_date": "2023-03-22T16:10:00Z",
      "uploader": 1
    }
  ]
}
```

### Отметка сообщений как прочитанных

**URL**: `PUT /api/chats/{id}/messages/read/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

**Тело запроса**:
```json
{
  "message_ids": [14, 15]
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "status": "success",
  "updated_count": 2
}
```

### Загрузка вложения

**URL**: `POST /api/attachments/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: multipart/form-data
```

**Тело запроса**:
```
file: [файл]
```

**Ответ в случае успеха** (HTTP 201 Created):
```json
{
  "id": 3,
  "file": "chat_attachments/presentation.pptx",
  "file_url": "http://example.com/media/chat_attachments/presentation.pptx",
  "file_type": "document",
  "file_name": "presentation.pptx",
  "file_size": 2345678,
  "upload_date": "2023-03-22T16:30:20Z",
  "uploader": 1
}
```

### Поиск сообщений

**URL**: `GET /api/messages/search/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Параметры запроса**:
- `q`: поисковый запрос
- `chatId`: (опционально) ID чата для ограничения поиска
- `limit`: максимальное количество результатов

**Пример запроса**: `GET /api/messages/search/?q=привет&limit=5`

**Ответ в случае успеха** (HTTP 200 OK):
```json
[
  {
    "id": 15,
    "chat": 1,
    "sender": {
      "id": 2,
      "username": "ivanova",
      "full_name": "Анна Иванова",
      "avatar": "media/avatars/anna.jpg",
      "is_verified": false
    },
    "content": "Привет, как дела?",
    "timestamp": "2023-03-20T14:15:22Z",
    "is_read": true,
    "attachments": []
  },
  {
    "id": 16,
    "chat": 1,
    "sender": {
      "id": 1,
      "username": "example_user",
      "full_name": "Иван Иванов",
      "avatar": null,
      "is_verified": false
    },
    "content": "Привет! Как твои дела?",
    "timestamp": "2023-03-22T16:10:45Z",
    "is_read": false,
    "attachments": [
      {
        "id": 1,
        "file": "chat_attachments/document.pdf",
        "file_url": "http://example.com/media/chat_attachments/document.pdf",
        "file_type": "document",
        "file_name": "document.pdf",
        "file_size": 1245678,
        "upload_date": "2023-03-22T16:09:30Z",
        "uploader": 1
      },
      {
        "id": 2,
        "file": "chat_attachments/image.jpg",
        "file_url": "http://example.com/media/chat_attachments/image.jpg",
        "file_type": "image",
        "file_name": "image.jpg",
        "file_size": 345678,
        "upload_date": "2023-03-22T16:10:00Z",
        "uploader": 1
      }
    ]
  }
]
```

### Получение статусов онлайн

**URL**: `POST /api/users/online-status/`

**Требуется авторизация**: Да

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

**Тело запроса**:
```json
{
  "userIds": [2, 3, 4]
}
```

**Ответ в случае успеха** (HTTP 200 OK):
```json
{
  "2": {
    "status": "online",
    "is_online": true
  },
  "3": {
    "status": "offline",
    "is_online": false
  },
  "4": {
    "status": "dnd",
    "is_online": false
  }
}
```