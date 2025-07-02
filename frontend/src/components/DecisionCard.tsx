import { useEffect } from 'react'
import confetti from 'canvas-confetti'

interface DebateResult {
  final_choice?: string
  summary?: string
  confidence?: number
}

interface DecisionCardProps {
  result: DebateResult
}

export function DecisionCard({ result }: DecisionCardProps) {
  useEffect(() => {
    if (result.final_choice) {
      // Celebration confetti
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      })
    }
  }, [result.final_choice])

  if (!result.final_choice) {
    return null
  }

  const confidencePercentage = result.confidence 
    ? Math.round(result.confidence * 100) 
    : 0

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '20px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      border: '2px solid #28a745'
    }}>
      <div style={{
        textAlign: 'center',
        marginBottom: '15px'
      }}>
        <h2 style={{
          margin: 0,
          color: '#28a745',
          fontSize: '1.8rem'
        }}>
          🎉 決定！
        </h2>
      </div>

      <div style={{
        textAlign: 'center',
        marginBottom: '20px'
      }}>
        <div style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          color: '#333',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '2px solid #28a745'
        }}>
          {result.final_choice}
        </div>
      </div>

      {result.summary && (
        <div style={{
          marginBottom: '15px'
        }}>
          <h4 style={{
            margin: '0 0 10px 0',
            color: '#555'
          }}>
            📝 決定理由
          </h4>
          <p style={{
            margin: 0,
            color: '#666',
            lineHeight: '1.6',
            backgroundColor: '#f8f9fa',
            padding: '12px',
            borderRadius: '6px'
          }}>
            {result.summary}
          </p>
        </div>
      )}

      {result.confidence !== undefined && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{
            fontWeight: 'bold',
            color: '#555'
          }}>
            信頼度:
          </span>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <div style={{
              width: '100px',
              height: '8px',
              backgroundColor: '#e9ecef',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${confidencePercentage}%`,
                height: '100%',
                backgroundColor: confidencePercentage > 70 ? '#28a745' : 
                                 confidencePercentage > 40 ? '#ffc107' : '#dc3545',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <span style={{
              fontWeight: 'bold',
              color: '#333'
            }}>
              {confidencePercentage}%
            </span>
          </div>
        </div>
      )}
    </div>
  )
}