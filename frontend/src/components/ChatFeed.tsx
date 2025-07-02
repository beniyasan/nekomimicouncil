import { useEffect, useRef } from 'react'

interface AgentMessage {
  agent_id: string
  agent_name: string
  message: string
  timestamp: string
  choice?: string
  message_type: string
  target_agent?: string
  round_number: number
}

interface RoundStart {
  round_number: number
  description: string
}

interface ChatFeedProps {
  messages: AgentMessage[]
  rounds?: RoundStart[]
  currentRound?: number
}

export function ChatFeed({ messages, rounds, currentRound }: ChatFeedProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const getAvatarUrl = (agentId: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    return `${baseUrl}/api/avatar/${agentId}`
  }

  const getMessageTypeLabel = (messageType: string) => {
    switch (messageType) {
      case 'initial_opinion': return '💭 初期意見'
      case 'question': return '❓ 質問'
      case 'response': return '💬 回答'
      case 'final_opinion': return '🎯 最終意見'
      case 'officer_question': return '👑 議長質問'
      case 'decision': return '⚖️ 決定'
      default: return ''
    }
  }

  const getMessageColor = (messageType: string) => {
    switch (messageType) {
      case 'initial_opinion': return '#007bff'
      case 'question': return '#fd7e14'
      case 'response': return '#28a745'
      case 'final_opinion': return '#6f42c1'
      case 'officer_question': return '#dc3545'
      case 'decision': return '#20c997'
      default: return '#007bff'
    }
  }

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
        <div style={{ marginBottom: '15px' }}>
          議論を開始すると、ここにAIキャラクターたちの会話が表示されます
        </div>
        {currentRound && (
          <div style={{
            fontSize: '0.9rem',
            color: '#007bff',
            fontWeight: 'bold'
          }}>
            現在のラウンド: {currentRound}
          </div>
        )}
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
        color: '#333',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>💬 議論の様子</span>
        {currentRound && (
          <span style={{
            fontSize: '0.8rem',
            color: '#007bff',
            backgroundColor: '#f0f8ff',
            padding: '4px 8px',
            borderRadius: '12px'
          }}>
            ラウンド {currentRound}
          </span>
        )}
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
              borderLeft: `4px solid ${getMessageColor(message.message_type)}`
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <img
                  src={getAvatarUrl(message.agent_id)}
                  alt={message.agent_name}
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: `2px solid ${getMessageColor(message.message_type)}`,
                    backgroundColor: 'white'
                  }}
                  onError={(e) => {
                    // Fallback to default avatar if image fails to load
                    const target = e.target as HTMLImageElement
                    target.src = getAvatarUrl('ai')
                  }}
                />
                <div>
                  <strong style={{ color: '#333', display: 'block' }}>
                    {message.agent_name}
                  </strong>
                  <span style={{
                    fontSize: '0.7rem',
                    color: getMessageColor(message.message_type),
                    backgroundColor: `${getMessageColor(message.message_type)}20`,
                    padding: '2px 6px',
                    borderRadius: '10px'
                  }}>
                    {getMessageTypeLabel(message.message_type)}
                  </span>
                </div>
              </div>
              <span style={{ 
                fontSize: '0.8em', 
                color: '#666' 
              }}>
                {new Date(message.timestamp).toLocaleTimeString('ja-JP')}
              </span>
            </div>
            
            {message.target_agent && (
              <div style={{
                fontSize: '0.8rem',
                color: '#666',
                marginBottom: '8px',
                fontStyle: 'italic'
              }}>
                → {message.target_agent} へ
              </div>
            )}
            
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