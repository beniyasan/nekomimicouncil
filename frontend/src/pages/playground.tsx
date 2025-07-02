import { useState, useCallback } from 'react'
import Head from 'next/head'
import { DebateForm } from '../components/DebateForm'
import { ChatFeed } from '../components/ChatFeed'
import { DecisionCard } from '../components/DecisionCard'
import { useDebate } from '../hooks/useDebate'

export default function Playground() {
  const {
    isConnected,
    isDebating,
    messages,
    result,
    startDebate,
    error
  } = useDebate()

  const handleDebateSubmit = useCallback((topic: string, options: string[]) => {
    startDebate(topic, options)
  }, [startDebate])

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <Head>
        <title>NekoMimi Council - Playground</title>
        <meta name="description" content="AI議論システム" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        padding: '20px' 
      }}>
        <header style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ 
            fontSize: '2.5rem', 
            color: '#333',
            marginBottom: '10px'
          }}>
            🐱 NekoMimi Council
          </h1>
          <p style={{ 
            fontSize: '1.1rem', 
            color: '#666' 
          }}>
            AI キャラクターたちが議論して決めてくれるシステム
          </p>
          <div style={{ 
            marginTop: '10px',
            fontSize: '0.9rem',
            color: isConnected ? '#28a745' : '#dc3545'
          }}>
            {isConnected ? '🟢 接続中' : '🔴 未接続'}
          </div>
        </header>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 2fr', 
          gap: '20px',
          minHeight: '600px'
        }}>
          <div>
            <DebateForm 
              onSubmit={handleDebateSubmit} 
              isLoading={isDebating}
            />
            {error && (
              <div style={{ 
                marginTop: '20px',
                padding: '15px',
                backgroundColor: '#f8d7da',
                color: '#721c24',
                borderRadius: '8px',
                border: '1px solid #f5c6cb'
              }}>
                エラー: {error}
              </div>
            )}
          </div>

          <div>
            {result && (
              <DecisionCard result={result} />
            )}
            <ChatFeed messages={messages} />
          </div>
        </div>
      </main>
    </div>
  )
}