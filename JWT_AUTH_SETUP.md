# JWT Authentication Setup for Yeldify API

## Overview

This project now supports **JWT (JSON Web Token)** authentication. The API can be used with:
- **Production**: JWT token in `Authorization: Bearer <token>` header
- **Development**: `user_id` query parameter (for testing)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements/base.txt
```

### 2. Set up environment variables

```bash
# JWT Secret Key (REQUIRED for production)
export JWT_SECRET_KEY=your-very-secret-key-here

# Token expiration (optional, default: 30 minutes)
export ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Get a JWT token

```bash
# Login to get a token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "username": "john_doe"}'

# Response:
# {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

### 4. Use the token in API requests

```bash
# Use token in Authorization header
curl -X GET "http://localhost:8000/orcamentos/?user_id=user-123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Or use token in POST request
curl -X POST "http://localhost:8000/orcamentos/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{"nome":"Alimenta\u00e7\u00e3o","categoria":"Essencial","valor":1000,"validade_meses":1}'
```

## Endpoints

### Authentication

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/auth/token` | Get JWT access token | `{"user_id": "...", "username": "..."}` |
| POST | `/auth/refresh` | Refresh existing token | `Authorization: Bearer <token>` |

### Usage with Existing Endpoints

All existing endpoints now support both authentication methods:

#### Method 1: JWT Token (Production)
```bash
curl -X GET "http://localhost:8000/orcamentos/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Method 2: Query Parameter (Development)
```bash
curl -X GET "http://localhost:8000/orcamentos/?user_id=user-123"
```

**Note**: If both are provided, JWT token takes precedence.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | Secret key for signing JWT tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time in minutes |

### Example .env file

```env
# JWT Configuration
JWT_SECRET_KEY=your-very-secret-and-strong-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database (if using PostgreSQL)
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yeldify
```

## Token Generation Example

### Python

```python
from src.infrastructure.web.api.v1.auth.jwt_auth import create_access_token

# Generate token for user-123
token = create_access_token({
    "sub": "user-123",
    "username": "john_doe"
})
print(f"Token: {token}")
```

### cURL

```bash
# Get token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'

# Use token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}' | jq -r '.access_token')

curl -X GET "http://localhost:8000/orcamentos/" \
  -H "Authorization: Bearer $TOKEN"
```

## Mock Users

For development and testing, the following mock users are available:

| user_id | username | disabled |
|---------|----------|----------|
| `user-123` | `john_doe` | false |
| `user-456` | `jane_doe` | false |

You can login with any of these user_ids to get a valid token.

## Implementation Details

### Files Created

| File | Description |
|------|-------------|
| `src/infrastructure/web/api/v1/auth/__init__.py` | Auth package |
| `src/infrastructure/web/api/v1/auth/jwt_auth.py` | JWT authentication logic |
| `src/infrastructure/web/api/v1/schemas/auth_schema.py` | Auth schemas (Token, UserLogin) |
| `src/infrastructure/web/api/v1/routes/auth.py` | Auth endpoints |

### Files Modified

| File | Change |
|------|--------|
| `requirements/base.txt` | Added `python-jose[cryptography]` |
| `src/infrastructure/web/api/v1/api.py` | Added auth router |
| `src/infrastructure/web/api/v1/routes/orcamentos.py` | JWT auth support |
| `src/infrastructure/web/api/v1/routes/despesas.py` | JWT auth support |

### Authentication Flow

```
Request
  │
  ▼
[Authorization: Bearer <token>] ──┐
  │                              │
  ▼                              ▼
get_user_id_from_token_or_query()
  │
  ▼
[user_id from token] ──or── [user_id from query param]
  │
  ▼
Use Case Execution
  │
  ▼
Response
```

### Token Structure

```json
{
  "sub": "user-123",           // User ID (required)
  "username": "john_doe",      // Optional username
  "exp": 1735689600,          // Expiration timestamp
  "iat": 1735686000,          // Issued at timestamp
  "type": "access_token"       // Token type
}
```

## Security Best Practices

### Production

1. **Always use HTTPS**: Never transmit JWT tokens over plain HTTP
2. **Strong secret key**: Use a long, random string for `JWT_SECRET_KEY`
3. **Short expiration**: Keep `ACCESS_TOKEN_EXPIRE_MINUTES` low (30-60 minutes)
4. **Rotate secrets**: Periodically change the JWT secret key
5. **Store securely**: Store secrets in environment variables or secret manager

### Development

1. **Use query params**: For local testing, you can use `?user_id=user-123`
2. **Don't commit secrets**: Add `JWT_SECRET_KEY` to your `.gitignore`
3. **Mock users**: Use the provided mock users for testing

## Troubleshooting

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

**Causes:**
- Missing `Authorization` header
- Invalid token
- Expired token
- Wrong secret key

**Solution:**
- Verify token is in format `Bearer <token>`
- Check token hasn't expired
- Ensure `JWT_SECRET_KEY` matches the key used to create the token

### Token not working in API calls

**Causes:**
- Token is valid but user_id doesn't exist in system
- Token is for a different user

**Solution:**
- Verify the token contains the correct `sub` (user_id) claim
- Ensure the user exists in your system

### "user_id query param is required"

**Cause:** Neither JWT token nor query param was provided

**Solution:**
- Provide `Authorization: Bearer <token>` header, OR
- Provide `?user_id=...` query parameter

## Migration Guide

### From Query Param to JWT

If you're currently using query parameters for authentication:

**Before:**
```bash
curl "http://localhost:8000/orcamentos/?user_id=user-123"
```

**After:**
```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}' | jq -r '.access_token')

# Use token
curl "http://localhost:8000/orcamentos/" \
  -H "Authorization: Bearer $TOKEN"
```

### Backward Compatibility

The API maintains **full backward compatibility** with query parameter authentication.
This means:
- Existing code using `?user_id=...` continues to work
- New code can use JWT tokens
- Both can be used simultaneously (JWT takes precedence)

You can migrate gradually without breaking existing clients.
