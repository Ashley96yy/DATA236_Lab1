# Week 1 Implementation Checklist (Frontend vs Backend)

## Scope
This checklist follows `docs/api-contract-v1.md` and focuses on the first milestone:
- Auth
- Profile
- Preferences

Target milestone date: `2026-02-20` (Friday afternoon)

## Backend Checklist
- [ ] Set up FastAPI app structure with `/api/v1` prefix.
- [ ] Add environment config (`.env`) for DB/JWT settings.
- [ ] Connect MySQL and verify startup without errors.
- [ ] Implement `GET /api/v1/health`.
- [ ] Implement `POST /api/v1/auth/signup` with bcrypt password hashing.
- [ ] Implement `POST /api/v1/auth/login` and JWT token issue.
- [ ] Implement auth dependency/middleware for protected endpoints.
- [ ] Implement `GET /api/v1/users/me`.
- [ ] Implement `PUT /api/v1/users/me`.
- [ ] Implement `GET /api/v1/users/me/preferences`.
- [ ] Implement `PUT /api/v1/users/me/preferences`.
- [ ] Return consistent error format for 4xx/5xx.
- [ ] Verify all above endpoints in Swagger or Postman.

## Frontend Checklist
- [ ] Set up React app structure with routes and page skeletons.
- [ ] Create API client layer (base URL, auth header, error handling).
- [ ] Build Login page and call `POST /auth/login`.
- [ ] Build Signup page and call `POST /auth/signup`.
- [ ] Store JWT token and apply route guard for protected pages.
- [ ] Build Profile page and call `GET /users/me`.
- [ ] Implement Profile update form and call `PUT /users/me`.
- [ ] Build Preferences page and call `GET /users/me/preferences`.
- [ ] Implement Preferences update form and call `PUT /users/me/preferences`.
- [ ] Add loading and error states for all above pages.

## Tuesday Integration Sync (Noon)
- [ ] Auth flow works end-to-end: signup -> login -> token storage.
- [ ] Protected API calls include Bearer token.
- [ ] Profile read/update works from UI.
- [ ] Preferences read/update works from UI.

## Friday Milestone Review (Afternoon)
- [ ] Demo starts from clean login state.
- [ ] All Week 1 endpoints return expected schema from contract.
- [ ] No blocker-level bugs in auth/profile/preferences flow.
- [ ] Team confirms Week 2 can start (restaurant + reviews).
