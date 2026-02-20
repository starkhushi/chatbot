import React, { useState, useRef, useEffect } from 'react'
import './App.css'
import logoImage from '../image/1.png'

// API URL - use environment variable or default to localhost:8000
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef(null)

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined })
  }

  // Load all sessions
  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions`)
      const data = await response.json()
      if (data.sessions) {
        setSessions(data.sessions)
      }
    } catch (error) {
      console.error('Error loading sessions:', error)
    }
  }

  // Load messages for a session
  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/messages`)
      const data = await response.json()
      if (data.messages && Array.isArray(data.messages)) {
        setMessages(data.messages)
        setCurrentSessionId(sessionId)
      } else {
        // If no messages, set empty array
        setMessages([])
        setCurrentSessionId(sessionId)
      }
    } catch (error) {
      console.error('Error loading session messages:', error)
      setMessages([])
      setCurrentSessionId(sessionId)
    }
  }

  // Create new session
  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      })
      const data = await response.json()
      if (data.session_id) {
        setCurrentSessionId(data.session_id)
        setMessages([])
        await loadSessions()
      }
    } catch (error) {
      console.error('Error creating session:', error)
    }
  }

  // Delete session
  const deleteSession = async (sessionId, e) => {
    e.stopPropagation()
    try {
      await fetch(`${API_URL}/sessions/${sessionId}`, {
        method: 'DELETE'
      })
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }
      await loadSessions()
    } catch (error) {
      console.error('Error deleting session:', error)
    }
  }

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Don't auto-select first session - let user choose
  useEffect(() => {
    // Only auto-select if no current session and sessions exist
    if (!currentSessionId && sessions.length > 0) {
      // Don't auto-load - let user click
    }
  }, [sessions, currentSessionId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Create session if none exists
    if (!currentSessionId) {
      await createNewSession()
      // Wait a bit for session to be created
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    // Add user message to UI
    const newUserMessage = { role: 'user', content: userMessage }
    setMessages(prev => [...prev, newUserMessage])

    // Add placeholder for assistant response
    const assistantMessageIndex = messages.length + 1
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const response = await fetch(`${API_URL}/chat-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_text: userMessage,
          session_id: currentSessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantResponse = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        assistantResponse += chunk

        // Update the assistant message in real-time
        setMessages(prev => {
          const updated = [...prev]
          updated[assistantMessageIndex] = {
            role: 'assistant',
            content: assistantResponse
          }
          return updated
        })
      }

      // Reload sessions to update titles/timestamps
      await loadSessions()
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => {
        const updated = [...prev]
        updated[assistantMessageIndex] = {
          role: 'assistant',
          content: `Error: ${error.message}`
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Filter sessions based on search query
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="app">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <img src={logoImage} alt="Logo" className="sidebar-logo" />
            <h2 className="sidebar-title">AI PLATFORM</h2>
          </div>
          <button className="back-button" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ←
          </button>
        </div>

        <button className="new-chat-button" onClick={createNewSession}>
          <span className="plus-icon">+</span>
          New Chat
        </button>

        <div className="search-container">
          <input
            type="text"
            placeholder="Q Search chat..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="sessions-list">
          {filteredSessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${currentSessionId === session.session_id ? 'active' : ''}`}
              onClick={() => loadSessionMessages(session.session_id)}
            >
              <div className="session-content">
                <div className="session-title">{session.title}</div>
                <div className="session-time">{formatDate(session.updated_at)}</div>
              </div>
              <button
                className="delete-session-btn"
                onClick={(e) => deleteSession(session.session_id, e)}
                title="Delete session"
              >
                ×
              </button>
            </div>
          ))}
          {filteredSessions.length === 0 && sessions.length > 0 && (
            <div className="no-results">No chats found</div>
          )}
          {sessions.length === 0 && (
            <div className="no-sessions">No chats yet. Start a new conversation!</div>
          )}
        </div>

        <div className="sidebar-footer">
          <button className="settings-button">
            <span>⚙️</span> Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-content">
        <div className="chat-container">
          <div className="chat-header">
            <button className="menu-button" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <h1>Welcome to Bot</h1>
            <p className="subtitle">Get all your accounting and support queries answered in an instant!</p>
          </div>

          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>Welcome! Start a conversation with the chatbot.</p>
              </div>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content || (msg.role === 'assistant' && isLoading ? '...' : '')}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Reply..."
              rows={1}
              disabled={isLoading}
              className="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="send-button"
            >
              {isLoading ? 'Sending...' : '↑'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
