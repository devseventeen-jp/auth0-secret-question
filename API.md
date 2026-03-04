# API Reference

このドキュメントは、本プロジェクトの API と関連環境変数を 1 つにまとめた一覧です。

## Base URL

- API Base Path: `/api`
- フロントエンドからの実URLは `NUXT_PUBLIC_API_BASE_URL` を先頭に付与
  - 例: `http://localhost:8000/api/auth/me`
- 内部 JWT API Base Path: `/jwt`

## Authentication

- Auth0 トークン必須エンドポイントは `Authorization: Bearer <token>` を使用
- 内部 JWT は `/jwt/token` で発行し、`Authorization: Bearer <internal_token>` で利用可能

## Endpoints

### `/api/*` (画面向け API)

#### 1. POST `/api/auth/authorize`
- 説明: Auth0 ID Token を検証し、ユーザー状態を返す
- 認証: 実装上 `AllowAny`（ただし `id_token` が必須）
- Request Body:
  - `id_token` (string, required)
- Response (`200`):
  - `{"status":"needs_secret"}`
  - `{"status":"needs_approval"}`
  - `{"status":"ok"}`

#### 2. GET `/api/auth/me`
- 説明: 認証ユーザー情報を返す
- 認証: Auth0 Bearer Token 必須
- Response (`200`):
  - UserSerializer のユーザー情報（`username`, `is_approved` など）

#### 3. GET `/api/auth/secret-question`
- 説明: 秘密の質問と回答状態を取得
- 認証: 必須
- Response (`200`):
  - `question`
  - `has_answered`
  - `secret_answer`
  - `is_approved`
  - `rejection_reason`

#### 4. POST `/api/auth/secret-question`
- 説明: 秘密の質問の回答を登録/更新
- 認証: 必須
- Request Body:
  - `answer` (string, required)
- 主な Response:
  - `200`: `{"status":"submitted"}`
  - `400`: `{"detail":"answer is required"}`
  - `400`: `{"detail":"Already approved"}`

#### 5. GET `/api/auth/status`
- 説明: 承認状態のみ取得
- 認証: 必須
- Response (`200`):
  - `is_approved`
  - `has_answered`

#### 6. POST `/api/auth/approve/<user_id>`
- 説明: 管理者がユーザーを承認
- 認証: 管理者のみ (`IsAdminUser`)
- Response (`200`):
  - `{"status":"approved"}`

### `/jwt/*` (内部 JWT / セッション API)

#### 1. POST `/jwt/session/callback`
- 説明: Auth0 callback 用。ID Token を検証し、成功時に内部JWTを HttpOnly Cookie で発行
- 認証: 実装上 `AllowAny`（`id_token` が必須）
- Request Body:
  - `id_token` (string, required)
  - `return_to` (string, optional, allowlist 必須)
- Response (`200`):
  - `{"status":"needs_secret"}`
  - `{"status":"needs_approval"}`
  - `{"status":"ok","return_to":"..."}`
- Cookie:
  - `INTERNAL_JWT_COOKIE_NAME` で指定したキー名の HttpOnly Cookie を `status=ok` のときに付与

#### 2. GET `/jwt/session/validate`
- 説明: callback で発行した HttpOnly Cookie 内の内部JWTを検証
- 認証: 不要（Cookie必須）
- Request:
  - `INTERNAL_JWT_COOKIE_NAME` の Cookie を送信
- 主な Response:
  - `200`: `{"valid": true, "user_id": ..., "username": "...", ...}`
  - `401`: `{"valid": false, "detail": "..."}`

#### 3. POST `/jwt/session/refresh`
- 説明: 既存の内部JWT Cookie（期限切れを含む）を検証し、内部JWT Cookieを再発行
- 認証: 不要（Cookie必須）
- Request:
  - Body なし
  - `INTERNAL_JWT_COOKIE_NAME` の Cookie を送信
- Response (`200`):
  - `{"status":"needs_secret"}`
  - `{"status":"needs_approval"}`
  - `{"status":"ok"}`
- 主な Error:
  - `401`: `{"message":"Cookie '<name>' is missing"}`
  - `401`: `{"message":"Invalid token"}`
  - `401`: `{"message":"Invalid token payload"}`
  - `401`: `{"message":"User not found"}`
- Cookie:
  - `status=ok` のときに `INTERNAL_JWT_COOKIE_NAME` の HttpOnly Cookie を再発行

#### 4. POST `/jwt/session/logout`
- 説明: 内部JWT Cookie を削除してログアウト状態にする
- 認証: 不要（Cookieがあれば削除）
- Request:
  - Body なし
- Response (`200`):
  - `{"status":"ok"}`

#### 5. GET `/jwt/claims`
- 説明: 内部JWT Cookie からクレーム (`sub`, `email`) を返す
- 認証: 不要（Cookie必須）
- Request:
  - `INTERNAL_JWT_COOKIE_NAME` の Cookie を送信
- Response (`200`):
  - `{"sub":"...", "email":"..."}`
- 主な Error:
  - `401`: `{"message":"Cookie '<name>' is missing"}`
  - `401`: `{"message":"..."}`

#### 6. POST `/jwt/token`
- 説明: コンテナ間連携用の内部 JWT を発行
- 認証: 必須
- Request Body (optional):
  - `expires_in_hours` (number, default: 24)
- Response (`200`):
  - `token`
  - `user_id`
  - `username`
  - `expires_in`

#### 7. POST `/jwt/token/validate`
- 説明: 内部 JWT を検証
- 認証: 不要 (`AllowAny`)
- Request Body:
  - `token` (string, required)
- 主な Response:
  - `200`: `{"valid": true, ...}`
  - `401`: `{"valid": false, "detail": "..."}`

## API 関連 Environment Variables

### Backend (Django)
- `AUTH0_DOMAIN`
  - Auth0 ドメイン。トークン検証時の JWKS 取得/issuer 照合で使用
- `AUTH0_CLIENT_ID`
  - `/api/auth/authorize` の ID Token audience 検証に使用
- `AUTH0_AUDIENCE`
  - Auth0 トークン検証ロジックで参照
- `DJANGO_SECRET_KEY`
  - Django `SECRET_KEY`。内部 JWT (`/jwt/token`) の署名鍵としても使用
- `RETURN_TO_ALLOWLIST`
  - `/jwt/session/callback` で許可する `return_to` の origin 一覧（カンマ区切り）
- `INTERNAL_JWT_COOKIE_NAME`
  - callback 成功時に発行する HttpOnly Cookie のキー名
- `INTERNAL_JWT_COOKIE_MAX_AGE`
  - callback 成功時に発行する Cookie の有効秒数
- `INTERNAL_JWT_COOKIE_PATH`
  - callback 成功時に発行する Cookie の Path
- `INTERNAL_JWT_COOKIE_DOMAIN`
  - callback 成功時に発行する Cookie の Domain（未指定なら省略）
- `INTERNAL_JWT_COOKIE_SAMESITE`
  - callback 成功時に発行する Cookie の SameSite
- `INTERNAL_JWT_COOKIE_SECURE`
  - callback 成功時に発行する Cookie の Secure フラグ
- `DATABASE_URL`
  - DB 接続文字列
- `SECRET_QUESTION_TEXT`
  - `/api/auth/secret-question` GET の `question` として返却
- `CORS_ALLOW_ALL_ORIGINS`
  - CORS 全許可フラグ
- `CORS_ALLOWED_ORIGINS`
  - CORS 許可 Origin のカンマ区切り一覧（上記が False の場合に使用）

### Frontend (Nuxt public runtimeConfig)
- `NUXT_PUBLIC_API_BASE_URL`
  - API 呼び出し時のベース URL
- `NUXT_PUBLIC_AUTH0_DOMAIN`
  - Auth0 SDK 設定
- `NUXT_PUBLIC_AUTH0_CLIENT_ID`
  - Auth0 SDK 設定
- `NUXT_PUBLIC_AUTH0_AUDIENCE`
  - Auth0 SDK 設定
- `NUXT_PUBLIC_APPROVAL_REDIRECT_URL`
  - 承認後の遷移先 URL（`/api/auth/secret-question` の結果に応じた画面遷移で利用）

## Notes

- `.env.example` にある `AUTH0_CLIENT_SECRET` は、現状のアプリコードでは API 実行時に直接参照されていません。
- SMTP 系 (`EMAIL_*`, `DEFAULT_FROM_EMAIL`) は API 機能拡張向け設定で、現行の `/api/auth/*` 処理では未使用です。
- ログイン画面 (`/`) に `?select_account=true`（または `1`）を付けると、Auth0 ログイン時に `prompt=select_account` を付与します。
- ただし Auth0 の既存セッション状態や tenant 側設定により、常にアカウント選択画面が表示されることは保証されません（有効化ヒントの位置づけ）。
