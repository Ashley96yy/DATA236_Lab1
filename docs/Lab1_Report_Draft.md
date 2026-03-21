# DATA236 Lab 1 Report Draft

## Introduction

Dine Finder is a Yelp-style restaurant discovery and review platform built with React, FastAPI, and MySQL. The system supports two user roles: regular users/reviewers and restaurant owners. Users can create accounts, manage dining preferences, search for restaurants, write reviews, save favorites, and view their activity history. Owners can register separately, claim or create restaurant listings, edit restaurant information, view customer reviews, and access a dashboard with summary analytics.

The main goal of the project is to combine a traditional full-stack web application with an AI-powered restaurant recommendation assistant. In addition to standard CRUD and search features, the system includes a conversational AI Assistant that uses user preferences, restaurant data stored in MySQL, semantic retrieval over restaurant embeddings, and optional live web context enrichment. This makes the application more aligned with modern intelligent search and recommendation systems rather than a static listing website.

## System Design

The application follows a client-server architecture composed of four main layers: a React frontend, a FastAPI backend, a MySQL database, and an AI Assistant service. The React frontend is responsible for rendering pages, managing route navigation, handling forms, and maintaining authentication state for both users and restaurant owners. The frontend communicates with the backend through REST APIs using Axios, and the AI Assistant is exposed in the interface as a chat widget so it remains available during the main browsing flow.

The FastAPI backend acts as the central application layer. It organizes the system into endpoint, schema, model, and service modules. The backend provides APIs for authentication, profile management, user preferences, restaurant search, restaurant creation, photo upload, review CRUD, favorites, user activity history, owner management, and AI chat. This separation allows request validation to stay in the API layer, database models to stay in the ORM layer, and business logic such as authorization, ranking, claiming restaurants, and review ownership checks to stay in service modules. FastAPI also provides Swagger UI, which helps verify endpoint coverage and API behavior during testing.

MySQL is used as the primary source of truth for structured application data. The database stores users, owners, user preferences, restaurants, reviews, favorites, and restaurant photo metadata. Uploaded avatar files and restaurant photo files are served by the backend from a static uploads directory, while their URLs and ownership metadata are stored in the database. The current user activity history shown in the dashboard is generated from stored reviews and restaurants added by the user, which keeps the history view consistent with the underlying platform data. This relational design supports both normal platform features and AI-driven recommendations because the same restaurant records, review data, and saved preferences can be reused across search, dashboard, and chatbot workflows. SQLAlchemy is used as the ORM for querying and updating MySQL data, while bcrypt is used for password hashing and JWT is used for secure user and owner authentication.

The frontend is divided into public routes and protected routes. Public routes include restaurant exploration and restaurant detail pages. User-protected routes include dashboard, profile, preferences, and restaurant submission pages. Owner-protected routes include owner dashboard, owner profile, owner restaurant management, restaurant creation, claim, edit, and review monitoring pages. This role-based route design keeps the user and owner experiences separate while allowing both roles to operate on the same restaurant ecosystem.

The AI Assistant service is integrated into the overall system rather than being a standalone tool. It is exposed as an authenticated backend API and used by the frontend chat widget for logged-in users. The service loads preference and restaurant data from the backend, performs semantic retrieval and reranking, and then returns a natural-language reply together with structured restaurant suggestions back to the user interface. This architecture allows the chatbot to reuse the same restaurant database, review signals, and preference data as the rest of the application, making the AI assistant a natural extension of the main platform instead of an isolated feature.

## AI Implementation

The AI assistant is implemented as an authenticated backend service behind `POST /api/v1/ai-assistant/chat`. Its purpose is to recommend restaurants in natural language while incorporating both user preferences and current restaurant data. The AI pipeline begins by loading the current user's saved preferences, such as cuisine, budget, dietary needs, ambiance, and preferred locations. Before running a new search, the assistant also checks whether the user is asking a follow-up question about a previously recommended restaurant, such as its hours, location, contact details, price, or amenities.

If the request is a new recommendation query, the assistant extracts intent from the user message. In the current implementation, this is primarily done through heuristic parsing of cuisine terms, price range, location hints, dietary needs, ambiance keywords, and occasion words. The code also supports optional LLM-based intent extraction, but the default low-cost configuration relies on heuristics first and uses the language model only when enabled. This design keeps the assistant usable even when paid API usage is limited.

To align the system with vector database, embeddings, semantic retrieval, and RAG concepts, the project includes a vector retrieval layer built with Chroma. Restaurant data from MySQL is transformed into text documents that include restaurant name, cuisine, description, amenities, city, state, price tier, hours, contact fields, and short review highlights. These documents are embedded and stored in a Chroma collection. The embedding layer can use OpenAI embeddings when configured, and it also supports a local fallback embedding method for development or low-cost testing. When the user asks for recommendations, the assistant generates an embedding-aware retrieval query, performs semantic search against the vector store, and retrieves the top matching restaurant candidates.

After semantic retrieval, the system performs structured reranking using MySQL-backed restaurant attributes. The reranking logic considers cuisine match, budget match, location match, dietary or ambiance signals, average rating, review count, and vector similarity. This hybrid design combines semantic similarity from embeddings with deterministic business signals from relational data. The assistant then returns structured restaurant suggestions containing restaurant ID, name, reason, rating, cuisine type, city, and price tier.

The final response is generated in one of two ways. If an LLM provider is configured, the assistant uses LangChain-based chat generation to produce a concise conversational reply grounded in the ranked restaurant results, user preferences, and recent chat history. If no LLM is available, the system falls back to a template-based response so the chatbot still works. If live web search is enabled, the assistant can further enrich responses with current context such as restaurant hours, events, or recent restaurant-related information.

This design can be described as a lightweight RAG workflow: MySQL remains the source of truth for application data, Chroma provides vector retrieval for semantic search, and the response layer uses either an LLM or a fallback generator to present grounded restaurant recommendations to the user.

## Results

The final system demonstrates the main workflows required by the lab through both frontend pages and backend APIs. On the user side, the application supports signup/login, profile editing, dining preference management, restaurant search and sorting, restaurant detail browsing, restaurant submission, review creation/edit/delete, favorites, history, and AI-assisted restaurant recommendations. On the owner side, the application supports owner signup/login, owner profile management, owner dashboard analytics, creating restaurant listings, claiming existing restaurants, editing claimed restaurants, and viewing reviews for managed restaurants.

The key frontend results are shown through screenshots of the explore page, restaurant detail page, profile and preferences pages, review workflow, owner workflow pages, and the AI Assistant conversation interface. These screens demonstrate that the application is not only implemented at the API level, but is also integrated into a usable end-to-end web experience with separate user and owner flows.

The backend results are demonstrated through FastAPI Swagger UI, available at `http://127.0.0.1:8000/docs`, where the main endpoints can be tested directly. Representative API tests should include authentication, restaurant search, review operations, favorites/history, owner management, and `POST /api/v1/ai-assistant/chat`. Together, the UI screenshots and API test results show that the system supports both standard restaurant platform functionality and an AI-enhanced recommendation workflow built on MySQL, vector retrieval, and structured reranking.

Add screenshots and API evidence in this section before submission:

1. Explore/Search page
2. Restaurant detail page
3. User profile or preferences page
4. Add restaurant page
5. Review create/edit/delete flow
6. Favorites/history view
7. Owner dashboard
8. Owner create restaurant page
9. Owner claim restaurant flow
10. AI assistant conversation with recommendation cards
11. Swagger UI endpoint screenshots
12. Example API test results for auth, restaurant search, reviews, owner management, and AI assistant

Suggested closing sentence for the report:

Overall, the project demonstrates a complete full-stack restaurant discovery platform that integrates structured database operations, role-based workflows, and an AI assistant enhanced by embeddings, vector retrieval, and retrieval-augmented recommendation logic.
