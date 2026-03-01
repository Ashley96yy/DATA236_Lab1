import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { aiAssistantApi, extractApiError } from "../services/api";

const QUICK_PROMPTS = [
  "Find dinner tonight near downtown under $$",
  "Suggest a romantic place for anniversary",
  "Show casual vegan-friendly options",
];

const MOBILE_BREAKPOINT = 480;
const PANEL_MIN_WIDTH = 340;
const PANEL_MIN_HEIGHT = 420;
const PANEL_MARGIN = 24;
const DEFAULT_PANEL_WIDTH = 430;
const DEFAULT_PANEL_HEIGHT = 620;
const PANEL_SIZE_KEY = "ai_widget_panel_size_v1";
const RESIZE_HOTZONE_PX = 32;

function buildId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function loadSavedPanelSize() {
  if (typeof window === "undefined") {
    return { width: DEFAULT_PANEL_WIDTH, height: DEFAULT_PANEL_HEIGHT };
  }
  try {
    const raw = window.localStorage.getItem(PANEL_SIZE_KEY);
    if (!raw) {
      return { width: DEFAULT_PANEL_WIDTH, height: DEFAULT_PANEL_HEIGHT };
    }
    const parsed = JSON.parse(raw);
    const width = Number(parsed?.width);
    const height = Number(parsed?.height);
    if (!Number.isFinite(width) || !Number.isFinite(height)) {
      return { width: DEFAULT_PANEL_WIDTH, height: DEFAULT_PANEL_HEIGHT };
    }
    return { width, height };
  } catch {
    return { width: DEFAULT_PANEL_WIDTH, height: DEFAULT_PANEL_HEIGHT };
  }
}

export default function AIChatWidget() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth <= MOBILE_BREAKPOINT : false
  );
  const [panelSize, setPanelSize] = useState(loadSavedPanelSize);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const panelSizeRef = useRef(panelSize);
  const panelRef = useRef(null);
  const [messages, setMessages] = useState(() => [
    {
      id: buildId("assistant"),
      role: "assistant",
      content: "Hi! Tell me what food, budget, or vibe you want and I will recommend places.",
      suggestions: [],
    },
  ]);

  const conversationHistory = useMemo(
    () =>
      messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({ role: m.role, content: m.content })),
    [messages]
  );

  useEffect(() => {
    panelSizeRef.current = panelSize;
  }, [panelSize]);

  useEffect(() => {
    function syncLayout() {
      const mobileNow = window.innerWidth <= MOBILE_BREAKPOINT;
      setIsMobile(mobileNow);
      if (!mobileNow) {
        setPanelSize((prev) => ({
          width: clamp(prev.width, PANEL_MIN_WIDTH, window.innerWidth - PANEL_MARGIN),
          height: clamp(prev.height, PANEL_MIN_HEIGHT, window.innerHeight - PANEL_MARGIN),
        }));
      }
    }

    syncLayout();
    window.addEventListener("resize", syncLayout);
    return () => {
      window.removeEventListener("resize", syncLayout);
    };
  }, []);

  useEffect(() => {
    if (isMobile || typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(PANEL_SIZE_KEY, JSON.stringify(panelSize));
  }, [panelSize, isMobile]);

  function beginResize(startX, startY) {
    const startWidth = panelSizeRef.current.width;
    const startHeight = panelSizeRef.current.height;

    const previousUserSelect = document.body.style.userSelect;
    document.body.style.userSelect = "none";

    function applyResize(clientX, clientY) {
      const maxWidth = window.innerWidth - PANEL_MARGIN;
      const maxHeight = window.innerHeight - PANEL_MARGIN;
      const width = clamp(startWidth + (clientX - startX), PANEL_MIN_WIDTH, maxWidth);
      const height = clamp(startHeight + (clientY - startY), PANEL_MIN_HEIGHT, maxHeight);
      setPanelSize({ width, height });
    }

    function onMouseMove(moveEvent) {
      applyResize(moveEvent.clientX, moveEvent.clientY);
    }

    function onTouchMove(moveEvent) {
      const touch = moveEvent.touches?.[0];
      if (!touch) return;
      moveEvent.preventDefault();
      applyResize(touch.clientX, touch.clientY);
    }

    function cleanup() {
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", cleanup);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("touchend", cleanup);
      window.removeEventListener("touchcancel", cleanup);
    }

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", cleanup);
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("touchend", cleanup);
    window.addEventListener("touchcancel", cleanup);
  }

  function startPanelResize(event) {
    if (isMobile) {
      return;
    }

    event.preventDefault();
    beginResize(event.clientX, event.clientY);
  }

  function startPanelResizeTouch(event) {
    if (isMobile) {
      return;
    }
    const touch = event.touches?.[0];
    if (!touch) {
      return;
    }
    event.preventDefault();
    beginResize(touch.clientX, touch.clientY);
  }

  function tryStartResizeFromPanel(event) {
    if (isMobile || !panelRef.current) {
      return;
    }
    const rect = panelRef.current.getBoundingClientRect();
    const nearRight = rect.right - event.clientX <= RESIZE_HOTZONE_PX;
    const nearBottom = rect.bottom - event.clientY <= RESIZE_HOTZONE_PX;
    if (!nearRight || !nearBottom) {
      return;
    }
    event.preventDefault();
    beginResize(event.clientX, event.clientY);
  }

  const panelStyle = isMobile
    ? undefined
    : {
        width: `${panelSize.width}px`,
        height: `${panelSize.height}px`,
      };

  async function sendMessage(rawMessage) {
    if (!isAuthenticated) {
      setError("Please log in to use the AI assistant.");
      return;
    }

    const message = (rawMessage ?? input).trim();
    if (!message || isSending) {
      return;
    }

    setError("");
    setIsSending(true);
    if (rawMessage == null) {
      setInput("");
    }

    const userMsg = {
      id: buildId("user"),
      role: "user",
      content: message,
      suggestions: [],
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await aiAssistantApi.chat({
        message,
        conversation_history: conversationHistory,
      });
      const assistantMsg = {
        id: buildId("assistant"),
        role: "assistant",
        content: response.data.reply,
        suggestions: response.data.suggested_restaurants || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (requestError) {
      setError(extractApiError(requestError, "AI assistant request failed."));
    } finally {
      setIsSending(false);
    }
  }

  function clearConversation() {
    setMessages([
      {
        id: buildId("assistant"),
        role: "assistant",
        content: "New chat started. What are you in the mood for?",
        suggestions: [],
      },
    ]);
    setError("");
    setInput("");
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        className="ai-widget-launcher"
        onClick={() => setIsOpen(true)}
        aria-label="Open AI assistant chat"
      >
        Ask Assistant
      </button>
    );
  }

  return (
    <section
      ref={panelRef}
      className="ai-widget-panel"
      aria-label="AI assistant chat panel"
      style={panelStyle}
      onMouseDown={tryStartResizeFromPanel}
    >
      <header className="ai-widget-header">
        <div>
          <h2 className="ai-widget-title">AI Assistant</h2>
          <p className="ai-widget-subtitle">Personalized restaurant recommendations</p>
        </div>
        <div className="ai-widget-header-actions">
          <button type="button" className="ai-widget-btn" onClick={clearConversation}>
            New
          </button>
          <button type="button" className="ai-widget-btn" onClick={() => setIsOpen(false)}>
            Close
          </button>
        </div>
      </header>

      {!isAuthenticated ? (
        <div className="ai-widget-login-block">
          <p>Log in to use personalized AI recommendations from your saved preferences.</p>
          <button type="button" className="btn-primary" onClick={() => navigate("/login")}>
            Go to Login
          </button>
        </div>
      ) : (
        <>
          <div className="ai-widget-messages">
            {messages.map((message) => (
              <article
                key={message.id}
                className={`ai-msg ai-msg--${message.role}`}
                aria-live={message.role === "assistant" ? "polite" : undefined}
              >
                <p className="ai-msg-content">{message.content}</p>
                {message.suggestions?.length > 0 && (
                  <div className="ai-suggestion-list">
                    {message.suggestions.map((restaurant) => (
                      <button
                        key={`${message.id}-${restaurant.id}`}
                        type="button"
                        className="ai-suggestion-card"
                        onClick={() => navigate(`/restaurant/${restaurant.id}`)}
                      >
                        <span className="ai-suggestion-name">{restaurant.name}</span>
                        <span className="ai-suggestion-meta">
                          {[restaurant.cuisine_type, restaurant.pricing_tier, restaurant.average_rating ? `${restaurant.average_rating.toFixed(1)}★` : null]
                            .filter(Boolean)
                            .join(" • ")}
                        </span>
                        <span className="ai-suggestion-reason">{restaurant.reason}</span>
                      </button>
                    ))}
                  </div>
                )}
              </article>
            ))}

            {isSending && (
              <div className="ai-msg ai-msg--assistant">
                <p className="ai-msg-content">Thinking...</p>
              </div>
            )}
          </div>

          <div className="ai-widget-quick-prompts">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="ai-quick-btn"
                onClick={() => sendMessage(prompt)}
                disabled={isSending}
              >
                {prompt}
              </button>
            ))}
          </div>

          {error ? <p className="error-text ai-widget-error">{error}</p> : null}

          <form
            className="ai-widget-input-row"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <input
              type="text"
              placeholder="Ask for recommendations..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={isSending}
            />
            <button type="submit" className="btn-primary" disabled={isSending || !input.trim()}>
              Send
            </button>
          </form>
        </>
      )}

      {!isMobile ? (
        <button
          type="button"
          className="ai-widget-resizer"
          onMouseDown={startPanelResize}
          onTouchStart={startPanelResizeTouch}
          aria-label="Resize AI assistant panel"
          title="Drag to resize"
        />
      ) : null}
    </section>
  );
}
