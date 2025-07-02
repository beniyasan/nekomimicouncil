import { useEffect, useRef } from 'react'

interface AgentMessage {
  agent_id: string
  agent_name: string
  message: string
  timestamp: string
  choice?: string
}

interface ChatFeedProps {
  messages: AgentMessage[]
}

export function ChatFeed({ messages }: ChatFeedProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  if (messages.length === 0) {
    return (
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        textAlign: 'center',
        color: '#666'
      }}>
        議論を開始すると、ここにAIキャラクターたちの会話が表示されます
      </div>
    )
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
      height: '500px',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{
        padding: '15px 20px',
        borderBottom: '1px solid #e1e5e9',
        fontWeight: 'bold',
        color: '#333'
      }}>
        💬 議論の様子
      </div>
      
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '10px'
      }}>
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              marginBottom: '15px',
              padding: '12px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              borderLeft: '4px solid #007bff'
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <strong style={{ color: '#333' }}>
                {message.agent_name}
              </strong>
              <span style={{ 
                fontSize: '0.8em', 
                color: '#666' 
              }}>
                {new Date(message.timestamp).toLocaleTimeString('ja-JP')}
              </span>
            </div>
            
            <div style={{ 
              color: '#555',
              lineHeight: '1.5'
            }}>
              {message.message}
            </div>
            
            {message.choice && (
              <div style={{
                marginTop: '8px',
                padding: '6px 12px',
                backgroundColor: '#e7f3ff',
                borderRadius: '20px',
                fontSize: '0.9em',
                color: '#0066cc',
                display: 'inline-block'
              }}>
                選択: {message.choice}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}