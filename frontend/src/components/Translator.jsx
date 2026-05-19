import React from 'react'

export default function Translator({ translation, isConnected }) {
  return (
    <div style={{
      position: 'absolute',
      bottom: 100,
      left: 0,
      right: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
      pointerEvents: 'none',
    }}>
      {translation.sign && (
        <div style={{
          background: 'rgba(0,0,0,0.75)',
          color: '#fff',
          padding: '8px 24px',
          borderRadius: 8,
          fontSize: 32,
          fontWeight: 'bold',
          letterSpacing: 2,
        }}>
          {translation.sign}
          <span style={{ fontSize: 14, marginLeft: 12, opacity: 0.6 }}>
            {Math.round(translation.confidence * 100)}%
          </span>
        </div>
      )}

      {translation.sentence && (
        <div style={{
          background: 'rgba(0,0,0,0.55)',
          color: '#ddd',
          padding: '6px 18px',
          borderRadius: 6,
          fontSize: 18,
        }}>
          {translation.sentence}
        </div>
      )}

      <div style={{
        position: 'absolute',
        top: -36,
        right: 16,
        fontSize: 12,
        color: isConnected ? '#4ade80' : '#f87171',
      }}>
        {isConnected ? '● Connected' : '○ Disconnected'}
      </div>
    </div>
  )
}
