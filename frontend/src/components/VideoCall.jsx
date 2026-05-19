import React, { useEffect, useRef } from 'react'

const FRAME_INTERVAL_MS = 100  // ~10 fps sent to backend

export default function VideoCall({ isCameraOn, isMuted, onFrame, onStart }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const canvasRef = useRef(document.createElement('canvas'))
  const intervalRef = useRef(null)

  useEffect(() => {
    startCamera()
    onStart()
    return () => {
      clearInterval(intervalRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [])

  useEffect(() => {
    streamRef.current?.getVideoTracks().forEach(t => { t.enabled = isCameraOn })
    streamRef.current?.getAudioTracks().forEach(t => { t.enabled = !isMuted })
  }, [isCameraOn, isMuted])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      startFrameCapture()
    } catch (err) {
      console.error('Camera access denied:', err)
    }
  }

  const startFrameCapture = () => {
    intervalRef.current = setInterval(() => {
      const video = videoRef.current
      if (!video || !isCameraOn || video.readyState < 2) return
      const canvas = canvasRef.current
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      canvas.getContext('2d').drawImage(video, 0, 0)
      const base64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]
      onFrame(base64)
    }, FRAME_INTERVAL_MS)
  }

  return (
    <video
      ref={videoRef}
      autoPlay
      muted
      playsInline
      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
    />
  )
}
