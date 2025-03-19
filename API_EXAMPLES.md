# Примеры запросов к API OpenTalk

## Аутентификация

### Регистрация нового пользователя

**Endpoint**: `POST /api/auth/register/`

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

**Endpoint**: `POST /api/auth/login/`

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

**Endpoint**: `POST /api/auth/refresh/`

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

## Профиль пользователя

### Получение данных текущего пользователя

**Endpoint**: `GET /api/users/me/`

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Обновление профиля

**Endpoint**: `PUT /api/users/update_me/`

**Заголовки**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Пример данных для обновления полного имени**:
```json
{
  "full_name": "Иван Иванов"
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
  "bio": "",
  "status": "offline",
  "location": "",
  "created_at": "2023-03-18T18:00:00Z",
  "last_login": "2023-03-18T19:00:00Z",
  "is_premium": false,
  "is_verified": false,
  "theme_preference": "light"
}
``` 