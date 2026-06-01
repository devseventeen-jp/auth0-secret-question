# FEATURE: 認証/JWT と アプリ間遷移の整理

このドキュメントは「コンテナ内で起きる認証と JWT の状態」と「コンテナ外アプリとの遷移」を整理したものです。
コードと設定の実態に合わせて記載しています。

**対象リポジトリ**
- Backend: Django (`backend/`)
- Frontend: Nuxt SPA (`frontend/`)
- DB: Postgres
- 外部アプリ: `NUXT_PUBLIC_APPROVAL_REDIRECT_URL` で指定される外部 URL

---

## 1. コンポーネントと役割

**コンテナ内**
1. `auth-backend` (Django API)。Auth0 ID Token の検証、Secret Question の状態管理、内部 JWT の発行/検証（Cookie と Bearer）。
2. `auth-frontend` (Nuxt SPA)。Auth0 ログイン UI、Secret Question 画面、callback 画面。
3. `db` (Postgres)。`User` と回答/承認ステータスを保持。

**コンテナ外**
1. Auth0 (SaaS)。ID Token を発行。
2. 外部アプリ（別オリジン）。`NUXT_PUBLIC_APPROVAL_REDIRECT_URL` で指定される URL。例: 現在 `.env` では `http://localhost:8080/meeting/`。

---

## 2. 使用するトークン/セッション

**Auth0 ID Token (RS256)**
- 発行元: Auth0
- 発行条件: Auth0 ログイン成功時にブラウザへ返却
- 利用: `/api/auth/authorize`, `/api/auth/me`, `/api/auth/secret-question`, `/jwt/session/callback`
- 用途: Auth0 → フロント → backend の API 呼び出しで Bearer として使わる。backend が検証してユーザーを解決し、内部 JWT 発行やユーザー状態判定に利用

**内部 JWT (HS256, SECRET_KEY で署名)**
- 発行元: backend (`generate_internal_jwt_token`)
- 発行条件: `/jwt/session/callback` の `status=ok`、または `/jwt/token` 実行時
- 利用: backend が `verify_internal_jwt_token` で検証し、ユーザー情報と承認状態に利用
- 用途: コンテナ内で発行され、コンテナ外/別サービス連携で Bearer として利用。Cookie セッションの中身としても利用

**Cookie セッション**
- 発行元: backend（内部 JWT を Cookie に格納）
- 発行条件: `/jwt/session/callback` の `status=ok`、または `/jwt/session/refresh` の `status=ok`
- 利用: `/jwt/session/validate` や `/jwt/session/refresh` で検証し、セッション継続に利用
- 用途: ブラウザ ↔ backend の間で自動送信され、JS からは直接参照しない

---

## 3. ユーザー状態（遷移に関係する状態）

ユーザーの状態は以下の 2 つのフラグで決まります。
1. `has_answered` (秘密の質問に回答済みか)
2. `is_approved` (管理者承認済みか)

**状態遷移**
1. `has_answered=false` → `needs_secret`
2. `has_answered=true && is_approved=false` → `needs_approval`
3. `has_answered=true && is_approved=true` → `ok`

---

## 4. 画面遷移（フロント中心）

### 4.1 ログイン開始 → Auth0
- 画面: `/` (`frontend/app/pages/index.vue`)
- 動作: `loginWithRedirect` で Auth0 へ遷移。`return_to` が外部 URL の場合はリダイレクトまで保持する。

### 4.2 Auth0 → `/callback`
- 画面: `/callback` (`frontend/app/pages/callback.vue`)
- 動作: ID Token を取得して backend に送信。
- API: `POST /jwt/session/callback`
- 分岐: `needs_secret` → `/secret-question`、`needs_approval` → `/pending-approval`、`ok` → Cookie セッションを付与した後にリダイレクト

### 4.3 `ok` 後のリダイレクト先
- `response.return_to` が外部 URL ならそこへ遷移。
- そうでない場合は `NUXT_PUBLIC_APPROVAL_REDIRECT_URL` を優先。
- 両方なければ `/dashboard`。

### 4.4 Secret Question 画面
- 画面: `/secret-question` (`frontend/app/pages/secret-question.vue`)
- API: `/api/auth/secret-question`
- 認証: Auth0 ID Token (Authorization: Bearer `<id_token>`)
- 注意: ここでは **内部 JWT Cookie は使われない**。

## 5. Backend の認証経路（重要）

**主な API と認証**
1. `/api/auth/me`。Auth0 ID Token 必須。Internal JWT は無関係。
2. `/api/auth/secret-question`。`IsAuthenticated`。`Auth0Authentication` または `InternalJWTAuthentication` で認証。Frontend は Auth0 Bearer を送る。
3. `/jwt/session/callback`。AllowAny。Auth0 ID Token を検証し、内部 JWT Cookie を発行。
4. `/jwt/session/validate`。Cookie の内部 JWT を検証。
5. `/jwt/token`。`IsAuthenticated` 必須。internal JWT を返す（Bearer 用）。

---

## 6. Cookie と外部アプリの関係

**Cookie は backend ドメインに紐付く**
- `INTERNAL_JWT_COOKIE_DOMAIN` / `SameSite` / `Secure` が外部遷移に影響。
- 現在の `.env` では `INTERNAL_JWT_COOKIE_SAMESITE=Lax`、`INTERNAL_JWT_COOKIE_SECURE=False`。

**影響ポイント**
- 外部アプリが別オリジン (`http://localhost:8080`) の場合、Cookie が送信されない可能性がある。
- Cookie が送信されないと、外部アプリ側でセッション状態を確認できない。
- 外部アプリが backend に `/jwt/session/validate` を叩く場合も、Cookie が付かないと `401` になる。

### 6.1 セッション期限切れ時の復帰（運用）
- 前提: `利用アプリ backend -> 本backend` の経路では、本backendは `401` を返すだけで画面遷移を実行できない。
- `POST /jwt/session/refresh` が `401` の場合、利用アプリ backend 側で再認証導線へ切り替える。
- 推奨: 利用アプリ backend が本frontendのログインURLへ `302` リダイレクトし、`return_to` に期限切れ前の画面URLを付ける。
- 再認証成功後は `/callback` で `return_to` が利用され、元画面に戻す。

---

## 7. 画面遷移が想定通りにならない典型パターン

1. `return_to` が allowlist に入っておらず `Invalid return_to` で `400`。
2. Auth0 ID Token が取得できず `/callback` で `No ID Token found`。
3. `needs_approval` と `needs_secret` の分岐が想定外。`has_answered` / `is_approved` の値で挙動が決まる。
4. 外部アプリで Cookie が送れず、内部 JWT セッションが認識されない。`SameSite` / `Secure` の影響。
5. Authorization ヘッダが付かず `IsAuthenticated` で `403`。Auth0 ID Token 未取得や外部アプリの API 呼び出しで Bearer を付けていないケース。
6. `session/refresh` が `401` でも、利用アプリ backend で frontend への再認証リダイレクトを行わないため復帰導線が途切れる。

---

## 8. 関連ファイル

- Backend 認証ロジック: `backend/app/auth0_utils.py`
- Backend API: `backend/app/views.py`
- Frontend callback: `frontend/app/pages/callback.vue`
- Frontend secret question: `frontend/app/pages/secret-question.vue`
- 環境変数: `.env`
- API 仕様: `API.md`
