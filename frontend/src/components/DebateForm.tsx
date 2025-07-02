import { useState } from 'react'

interface DebateFormProps {
  onSubmit: (topic: string, options: string[]) => void
  isLoading: boolean
}

export function DebateForm({ onSubmit, isLoading }: DebateFormProps) {
  const [topic, setTopic] = useState('')
  const [optionsText, setOptionsText] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!topic.trim()) {
      alert('議題を入力してください')
      return
    }

    const options = optionsText
      .split(',')
      .map(opt => opt.trim())
      .filter(opt => opt.length > 0)

    if (options.length < 2) {
      alert('選択肢を2つ以上入力してください（カンマ区切り）')
      return
    }

    onSubmit(topic, options)
  }

  return (
    <div style={{
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '12px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
    }}>
      <h2 style={{ 
        marginTop: 0, 
        marginBottom: '20px',
        color: '#333',
        fontSize: '1.5rem'
      }}>
        議題設定
      </h2>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px',
            fontWeight: 'bold',
            color: '#555'
          }}>
            議題
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="例: 今日のランチはどこにする？"
            style={{
              width: '100%',
              padding: '12px',
              border: '2px solid #e1e5e9',
              borderRadius: '8px',
              fontSize: '16px',
              resize: 'vertical',
              minHeight: '80px',
              fontFamily: 'inherit'
            }}
            disabled={isLoading}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px',
            fontWeight: 'bold',
            color: '#555'
          }}>
            選択肢（カンマ区切り）
          </label>
          <input
            type="text"
            value={optionsText}
            onChange={(e) => setOptionsText(e.target.value)}
            placeholder="例: 寿司屋A, ラーメン店B, カフェC"
            style={{
              width: '100%',
              padding: '12px',
              border: '2px solid #e1e5e9',
              borderRadius: '8px',
              fontSize: '16px',
              fontFamily: 'inherit'
            }}
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '12px 24px',
            backgroundColor: isLoading ? '#6c757d' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s'
          }}
        >
          {isLoading ? '議論中...' : '議論開始'}
        </button>
      </form>
    </div>
  )
}