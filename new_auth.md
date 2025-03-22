# Запросы в бэкенд для системы авторизации

## 1. Аутентификация по номеру телефона

### 1.1. Отправка кода верификации

**Функция**: `sendVerificationCode`

**Запрос**:
```javascript
async function sendVerificationCode(phone) {
  try {
    const response = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ phone })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при отправке кода');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при отправке кода верификации:', error);
    throw error;
  }
}
```

**Параметры**:
- `phone`: строка с номером телефона (например, "79991234567")

**Ответ от сервера**:
```json
{
  "success": true,
  "message": "Код подтверждения отправлен",
  "expiresIn": 120 // время действия кода в секундах
}
```

### 1.2. Проверка кода верификации

**Функция**: `verifyCode`

**Запрос**:
```javascript
async function verifyCode(phone, code) {
  try {
    const response = await fetch('/api/auth/verify-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ phone, code })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Неверный код подтверждения');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при проверке кода верификации:', error);
    throw error;
  }
}
```

**Параметры**:
- `phone`: строка с номером телефона
- `code`: строка с 6-значным кодом подтверждения

**Ответ от сервера (существующий пользователь)**:
```json
{
  "success": true,
  "isNewUser": false,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123456",
    "username": "user123",
    "phone": "79991234567",
    "avatar": "https://example.com/avatars/default.png",
    "createdAt": "2023-01-15T12:00:00Z"
  }
}
```

**Ответ от сервера (новый пользователь)**:
```json
{
  "success": true,
  "isNewUser": true,
  "tempToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // временный токен для завершения регистрации
  "phone": "79991234567"
}
```

## 2. Регистрация нового пользователя

### 2.1. Проверка доступности имени пользователя

**Функция**: `checkUsername`

**Запрос**:
```javascript
async function checkUsername(username) {
  try {
    const response = await fetch(`/api/auth/check-username?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при проверке имени пользователя');
    }
    
    const data = await response.json();
    return data.available;
  } catch (error) {
    console.error('Ошибка при проверке имени пользователя:', error);
    throw error;
  }
}
```

**Параметры**:
- `username`: строка с проверяемым именем пользователя

**Ответ от сервера**:
```json
{
  "available": true, // или false
  "message": "Имя пользователя доступно" // опционально, сообщение о статусе
}
```

### 2.2. Завершение регистрации пользователя

**Функция**: `registerUser`

**Запрос**:
```javascript
async function registerUser(phone, username, tempToken) {
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tempToken}` // используем временный токен из шага верификации
      },
      body: JSON.stringify({ phone, username })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при создании аккаунта');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при регистрации пользователя:', error);
    throw error;
  }
}
```

**Параметры**:
- `phone`: строка с номером телефона
- `username`: строка с выбранным именем пользователя
- `tempToken`: строка с временным токеном из ответа на верификацию кода

**Ответ от сервера**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123456",
    "username": "user123",
    "phone": "79991234567",
    "avatar": "https://example.com/avatars/default.png",
    "createdAt": "2023-08-25T14:30:00Z"
  }
}
```

## 3. Аутентификация по QR-коду

### 3.1. Получение QR-кода для входа

**Функция**: `getQrCode`

**Запрос**:
```javascript
async function getQrCode() {
  try {
    const response = await fetch('/api/auth/qr-code', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при получении QR-кода');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при получении QR-кода:', error);
    throw error;
  }
}
```

**Ответ от сервера**:
```json
{
  "qrCodeUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "qrCodeId": "qr-12345-abcde"
}
```

### 3.2. Проверка статуса QR-кода

**Функция**: `checkQrStatus`

**Запрос**:
```javascript
async function checkQrStatus(qrCodeId) {
  try {
    const response = await fetch(`/api/auth/qr-status/${qrCodeId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при проверке статуса QR-кода');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при проверке статуса QR-кода:', error);
    throw error;
  }
}
```

**Параметры**:
- `qrCodeId`: идентификатор QR-кода, полученный при запросе QR-кода

**Ответ от сервера (QR-код ещё не отсканирован)**:
```json
{
  "status": "pending"
}
```

**Ответ от сервера (QR-код отсканирован и пользователь авторизован)**:
```json
{
  "status": "authenticated",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123456",
    "username": "user123",
    "phone": "79991234567",
    "avatar": "https://example.com/avatars/default.png",
    "createdAt": "2023-01-15T12:00:00Z"
  }
}
```

**Ответ от сервера (QR-код устарел или недействителен)**:
```json
{
  "status": "expired",
  "message": "QR-код истек, пожалуйста, получите новый"
}
```

## 4. Управление токенами

### 4.1. Обновление токена доступа

**Функция**: `refreshToken`

**Запрос**:
```javascript
async function refreshToken(refreshToken) {
  try {
    const response = await fetch('/api/auth/refresh-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refreshToken })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при обновлении токена');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при обновлении токена доступа:', error);
    throw error;
  }
}
```

**Параметры**:
- `refreshToken`: строка с refresh токеном

**Ответ от сервера**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // новый refresh токен (опционально)
}
```

### 4.2. Выход из системы

**Функция**: `logout`

**Запрос**:
```javascript
async function logout(refreshToken) {
  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ refreshToken })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      console.warn('Ошибка при выходе из системы:', errorData.message);
    }
    
    // Удаляем токены из localStorage независимо от ответа сервера
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    
    return true;
  } catch (error) {
    console.error('Ошибка при выходе из системы:', error);
    // Удаляем токены из localStorage даже при ошибке
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    return true;
  }
}
```

**Параметры**:
- `refreshToken`: строка с refresh токеном для инвалидации на сервере

**Ответ от сервера**:
```json
{
  "success": true,
  "message": "Выход выполнен успешно"
}
```

## 5. Получение информации о пользователе

### 5.1. Получение данных текущего пользователя

**Функция**: `getCurrentUser`

**Запрос**:
```javascript
async function getCurrentUser() {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('Токен авторизации отсутствует');
    }
    
    const response = await fetch('/api/users/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Токен недействителен, пробуем обновить
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const newTokens = await refreshToken(refreshToken);
          localStorage.setItem('token', newTokens.token);
          if (newTokens.refreshToken) {
            localStorage.setItem('refreshToken', newTokens.refreshToken);
          }
          // Повторяем запрос с новым токеном
          return await getCurrentUser();
        } else {
          throw new Error('Требуется повторная авторизация');
        }
      }
      
      const errorData = await response.json();
      throw new Error(errorData.message || 'Ошибка при получении данных пользователя');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ошибка при получении данных пользователя:', error);
    throw error;
  }
}
```

**Ответ от сервера**:
```json
{
  "id": "123456",
  "username": "user123",
  "phone": "79991234567",
  "avatar": "https://example.com/avatars/user123.png",
  "email": "user@example.com",
  "name": "Иван Иванов",
  "bio": "О себе",
  "lastSeen": "2023-08-25T16:45:00Z",
  "online": true,
  "settings": {
    "notifications": true,
    "theme": "dark",
    "language": "ru"
  },
  "createdAt": "2023-01-15T12:00:00Z"
}
```

## 6. Обработка ошибок и структура ответов

### 6.1. Общая структура ответа с ошибкой

```json
{
  "success": false,
  "error": {
    "code": "AUTH_ERROR",
    "message": "Детальное сообщение об ошибке",
    "details": { 
      // Дополнительная информация об ошибке (опционально)
    }
  }
}
```

### 6.2. Коды и типы ошибок

- `AUTH_INVALID_PHONE` - Недействительный номер телефона
- `AUTH_CODE_EXPIRED` - Код подтверждения устарел
- `AUTH_CODE_INVALID` - Неверный код подтверждения
- `AUTH_RATE_LIMITED` - Превышен лимит запросов (много попыток отправки кода)
- `AUTH_USERNAME_TAKEN` - Имя пользователя уже занято
- `AUTH_USERNAME_INVALID` - Недопустимое имя пользователя
- `AUTH_TOKEN_INVALID` - Недействительный токен
- `AUTH_TOKEN_EXPIRED` - Истекший токен
- `AUTH_QR_EXPIRED` - QR-код истек
- `AUTH_PERMISSION_DENIED` - Доступ запрещен
- `SERVER_ERROR` - Внутренняя ошибка сервера

## 7. Полная реализация в контексте приложения

Для эффективного использования API в React приложении, эти запросы обычно инкапсулируются в сервисном слое:

```javascript
// src/api/authApi.js
export async function sendVerificationCode(phone) {
  // Реализация...
}

export async function verifyCode(phone, code) {
  // Реализация...
}

export async function checkUsername(username) {
  // Реализация...
}

export async function registerUser(phone, username, tempToken) {
  // Реализация...
}

export async function getQrCode() {
  // Реализация...
}

export async function checkQrStatus(qrCodeId) {
  // Реализация...
}

export async function refreshToken(refreshToken) {
  // Реализация...
}

export async function logout(refreshToken) {
  // Реализация...
}

export async function getCurrentUser() {
  // Реализация...
}
```

И могут использоваться в контексте аутентификации:

```javascript
// src/context/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import * as authApi from '../api/authApi';

const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      authApi.getCurrentUser()
        .then(userData => {
          setCurrentUser(userData);
        })
        .catch(err => {
          console.error('Ошибка при автологине:', err);
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);
  
  const login = async (authData) => {
    if (authData.token) {
      localStorage.setItem('token', authData.token);
      if (authData.refreshToken) {
        localStorage.setItem('refreshToken', authData.refreshToken);
      }
      setCurrentUser(authData.user);
      return authData.user;
    }
    throw new Error('Недействительные данные авторизации');
  };
  
  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      await authApi.logout(refreshToken);
    } catch (error) {
      console.error('Ошибка при выходе из системы:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      setCurrentUser(null);
    }
  };
  
  const value = {
    currentUser,
    loading,
    error,
    login,
    logout,
    // Другие функции для работы с аутентификацией...
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
```

## 8. Меры безопасности и рекомендации

1. **Транспортная безопасность**:
   - Все запросы должны использовать HTTPS
   - Используйте HTTP Strict Transport Security (HSTS)

2. **Токены**:
   - Токены JWT должны быть подписаны с использованием безопасного алгоритма (например, HS256)
   - Access token должен иметь короткий срок жизни (15-30 минут)
   - Refresh token должен иметь более длительный срок жизни (напр., 7-30 дней)
   - Refresh token должен быть одноразовым и обновляться при использовании

3. **Хранение токенов**:
   - Access token в localStorage или memory (в зависимости от требований безопасности)
   - Refresh token в httpOnly cookie для большей безопасности

4. **Защита от атак**:
   - Ограничение частоты запросов (rate limiting) для предотвращения брутфорс атак
   - CSRF-токены для защиты от CSRF атак
   - Валидация и санитизация всех входных данных

5. **Аудит**:
   - Логирование попыток входа и выхода из системы
   - Уведомления пользователей о подозрительной активности
   - Журналирование всех действий аутентификации для анализа безопасности
