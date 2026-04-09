# Lab 2 Phase 6 Redux DevTools Screenshot Guide

Use Redux DevTools to capture at least two state transitions for the Lab 2 report.

## Recommended Screenshots

### 1. Auth Slice
- Action: user login
- Page: `/login`
- Expected Redux actions:
  - `auth/setSession`
  - optionally `auth/refreshCurrentUser/fulfilled`
- What to show in DevTools:
  - `auth.token`
  - `auth.user`
  - `auth.isAuthReady`

### 2. Restaurant Slice
- Action: explore/search filters
- Page: `/`
- Expected Redux actions:
  - `restaurants/setRestaurantFilter`
  - `restaurants/fetchRestaurants/pending`
  - `restaurants/fetchRestaurants/fulfilled`
- What to show in DevTools:
  - `restaurants.filters`
  - `restaurants.results.items`
  - `restaurants.page`

### 3. Review Slice
- Action: open a restaurant details page and submit/edit/delete a review
- Page: `/restaurant/:id`
- Expected Redux actions:
  - `reviews/fetchRestaurantReviews/pending`
  - `reviews/fetchRestaurantReviews/fulfilled`
  - `reviews/setReviewFeedback`
- What to show in DevTools:
  - `reviews.items`
  - `reviews.total`
  - `reviews.mutationStatus`
  - `reviews.mutationMessage`

### 4. Favorites Slice
- Action: open dashboard favorites/history or click the favorite heart
- Pages:
  - `/dashboard`
  - any restaurant card/detail page
- Expected Redux actions:
  - `favorites/loadFavorites/fulfilled`
  - `favorites/fetchFavoritesPage/fulfilled`
  - `favorites/fetchHistory/fulfilled`
  - `favorites/optimisticToggleFavorite`
- What to show in DevTools:
  - `favorites.ids`
  - `favorites.paged`
  - `favorites.history`

### 5. Owner Auth Slice
- Action: owner login
- Page: `/owner/login`
- Expected Redux actions:
  - `ownerAuth/setOwnerSession`
  - optionally `ownerAuth/refreshCurrentOwner/fulfilled`
- What to show in DevTools:
  - `ownerAuth.ownerToken`
  - `ownerAuth.owner`
  - `ownerAuth.isOwnerAuthReady`

## Best Report Pairing

If you only want two screenshots for the report, use:

1. `auth` login state transition
2. `restaurants` search/filter state transition

If you want stronger evidence, add:

3. `reviews` mutation feedback on restaurant detail page
4. `favorites` dashboard/history state load

