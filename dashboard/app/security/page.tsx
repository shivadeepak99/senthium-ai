'use client'

import { useEffect, useState, useRef } from 'react'
import { Shield, Camera, Users, AlertTriangle, Settings, Upload, Video, CheckCircle, XCircle, Bell, Eye, EyeOff } from 'lucide-react'
import Link from 'next/link'

interface SecurityStats {
  enabled: boolean
  total_checks: number
  unauthorized_detections: number
  authorized_users: string[]
  last_check_time: string | null
  camera_status: string
}

interface SecurityAlert {
  timestamp: string
  alert_type: string
  message: string
  snapshot_path?: string
  detected_faces_count: number
  confidence?: number
}

interface EnrollmentForm {
  name: string
  method: 'webcam' | 'upload'
  file?: File
}

export default function SecurityPage() {
  const [stats, setStats] = useState<SecurityStats | null>(null)
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [enrolling, setEnrolling] = useState(false)
  const [enrollForm, setEnrollForm] = useState<EnrollmentForm>({ name: '', method: 'webcam' })
  const [showCamera, setShowCamera] = useState(false)
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    fetchSecurityData()
    const interval = setInterval(fetchSecurityData, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const fetchSecurityData = async () => {
    try {
      const [statsRes, alertsRes] = await Promise.all([
        fetch('http://localhost:8080/api/security/stats'),
        fetch('http://localhost:8080/api/security/alerts?limit=20')
      ])
      
      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }
      
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json()
        // Handle both array and null/undefined responses
        setAlerts(Array.isArray(alertsData) ? alertsData : [])
      }
      
      setLoading(false)
    } catch (e) {
      console.error('Failed to fetch security data:', e)
      setLoading(false)
    }
  }

  const toggleSecurity = async () => {
    try {
      const action = stats?.enabled ? 'disable' : 'enable'
      await fetch(`http://localhost:8080/api/security/${action}`, { method: 'POST' })
      fetchSecurityData()
    } catch (e) {
      console.error('Failed to toggle security:', e)
    }
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      setCameraStream(stream)
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setShowCamera(true)
    } catch (e) {
      console.error('Failed to access camera:', e)
      alert('Failed to access camera. Please check permissions.')
    }
  }

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop())
      setCameraStream(null)
    }
    setShowCamera(false)
  }

  const captureAndEnroll = async () => {
    if (!videoRef.current || !canvasRef.current || !enrollForm.name) {
      alert('Please enter a name!')
      return
    }

    setEnrolling(true)
    
    try {
      // Capture frame from video
      const canvas = canvasRef.current
      const video = videoRef.current
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx?.drawImage(video, 0, 0)
      
      // Convert to blob
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.9)
      })
      
      // Upload to backend
      const formData = new FormData()
      formData.append('name', enrollForm.name)
      formData.append('image', blob, 'capture.jpg')
      
      const res = await fetch('http://localhost:8080/api/security/enroll', {
        method: 'POST',
        body: formData
      })
      
      if (res.ok) {
        alert(`✅ ${enrollForm.name} enrolled successfully!`)
        setEnrollForm({ name: '', method: 'webcam' })
        stopCamera()
        fetchSecurityData()
      } else {
        const error = await res.text()
        alert(`❌ Enrollment failed: ${error}`)
      }
    } catch (e) {
      console.error('Enrollment failed:', e)
      alert('Enrollment failed!')
    } finally {
      setEnrolling(false)
    }
  }

  const uploadAndEnroll = async () => {
    if (!enrollForm.name || !enrollForm.file) {
      alert('Please enter a name and select an image!')
      return
    }

    setEnrolling(true)
    
    try {
      const formData = new FormData()
      formData.append('name', enrollForm.name)
      formData.append('image', enrollForm.file)
      
      const res = await fetch('http://localhost:8080/api/security/enroll', {
        method: 'POST',
        body: formData
      })
      
      if (res.ok) {
        alert(`✅ ${enrollForm.name} enrolled successfully!`)
        setEnrollForm({ name: '', method: 'webcam' })
        fetchSecurityData()
      } else {
        const error = await res.text()
        alert(`❌ Enrollment failed: ${error}`)
      }
    } catch (e) {
      console.error('Enrollment failed:', e)
      alert('Enrollment failed!')
    } finally {
      setEnrolling(false)
    }
  }

  const performSecurityCheck = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/security/check', { method: 'POST' })
      if (res.ok) {
        alert('✅ Security check performed!')
        fetchSecurityData()
      }
    } catch (e) {
      console.error('Security check failed:', e)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl animate-pulse">
          🔒 Loading Security System...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/" className="text-purple-300 hover:text-purple-200 text-sm mb-2 block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
              <Shield className="w-10 h-10 text-pink-400" />
              AI Security Control Panel
            </h1>
            <p className="text-purple-300 mt-1">Face Recognition • Real-time Alerts • Threat Detection</p>
          </div>
          <button
            onClick={toggleSecurity}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-all ${
              stats?.enabled
                ? 'bg-red-500/20 hover:bg-red-500/30 border-2 border-red-500/50 text-red-300'
                : 'bg-green-500/20 hover:bg-green-500/30 border-2 border-green-500/50 text-green-300'
            }`}
          >
            {stats?.enabled ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            {stats?.enabled ? 'Disable Security' : 'Enable Security'}
          </button>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            icon={<Shield className="w-6 h-6" />}
            label="Status"
            value={stats?.enabled ? 'ACTIVE' : 'DISABLED'}
            color={stats?.enabled ? 'green' : 'gray'}
          />
          <StatCard
            icon={<Camera className="w-6 h-6" />}
            label="Security Checks"
            value={(stats?.total_checks || 0).toString()}
            color="blue"
          />
          <StatCard
            icon={<AlertTriangle className="w-6 h-6" />}
            label="Threats Detected"
            value={(stats?.unauthorized_detections || 0).toString()}
            color="red"
          />
          <StatCard
            icon={<Users className="w-6 h-6" />}
            label="Authorized Users"
            value={(stats?.authorized_users?.length || 0).toString()}
            color="purple"
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Enrollment Panel */}
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-purple-400" />
              Face Enrollment
            </h2>

            <div className="space-y-4">
              {/* Name Input */}
              <div>
                <label className="block text-sm text-purple-300 mb-2">User Name</label>
                <input
                  type="text"
                  value={enrollForm.name}
                  onChange={(e) => setEnrollForm({ ...enrollForm, name: e.target.value })}
                  placeholder="Enter name (e.g., Shiva)"
                  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:border-purple-400 text-white placeholder-gray-400"
                />
              </div>

              {/* Method Selection */}
              <div className="flex gap-2">
                <button
                  onClick={() => setEnrollForm({ ...enrollForm, method: 'webcam' })}
                  className={`flex-1 px-4 py-2 rounded-lg transition-all ${
                    enrollForm.method === 'webcam'
                      ? 'bg-purple-500/30 border-2 border-purple-400'
                      : 'bg-white/5 border border-white/20'
                  }`}
                >
                  <Video className="w-5 h-5 mx-auto mb-1" />
                  Webcam
                </button>
                <button
                  onClick={() => setEnrollForm({ ...enrollForm, method: 'upload' })}
                  className={`flex-1 px-4 py-2 rounded-lg transition-all ${
                    enrollForm.method === 'upload'
                      ? 'bg-purple-500/30 border-2 border-purple-400'
                      : 'bg-white/5 border border-white/20'
                  }`}
                >
                  <Upload className="w-5 h-5 mx-auto mb-1" />
                  Upload
                </button>
              </div>

              {/* Webcam Enrollment */}
              {enrollForm.method === 'webcam' && (
                <div className="space-y-3">
                  {!showCamera ? (
                    <button
                      onClick={startCamera}
                      className="w-full px-4 py-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                      <Camera className="w-5 h-5" />
                      Start Camera
                    </button>
                  ) : (
                    <>
                      <div className="relative rounded-lg overflow-hidden bg-black">
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          className="w-full"
                        />
                      </div>
                      <canvas ref={canvasRef} className="hidden" />
                      <div className="flex gap-2">
                        <button
                          onClick={captureAndEnroll}
                          disabled={enrolling || !enrollForm.name}
                          className="flex-1 px-4 py-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          <CheckCircle className="w-5 h-5" />
                          {enrolling ? 'Enrolling...' : 'Capture & Enroll'}
                        </button>
                        <button
                          onClick={stopCamera}
                          className="px-4 py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg transition-all"
                        >
                          <XCircle className="w-5 h-5" />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Upload Enrollment */}
              {enrollForm.method === 'upload' && (
                <div className="space-y-3">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setEnrollForm({ ...enrollForm, file: e.target.files?.[0] })}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-purple-500/30 file:text-white file:cursor-pointer hover:file:bg-purple-500/40"
                  />
                  <button
                    onClick={uploadAndEnroll}
                    disabled={enrolling || !enrollForm.name || !enrollForm.file}
                    className="w-full px-4 py-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Upload className="w-5 h-5" />
                    {enrolling ? 'Enrolling...' : 'Upload & Enroll'}
                  </button>
                </div>
              )}

              {/* Authorized Users List */}
              {stats?.authorized_users && stats.authorized_users.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm text-purple-300 mb-2">Authorized Users:</h3>
                  <div className="space-y-1">
                    {stats.authorized_users.map((user, i) => (
                      <div key={i} className="px-3 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-sm flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        {user}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Security Actions */}
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Settings className="w-6 h-6 text-purple-400" />
              Quick Actions
            </h2>

            <div className="space-y-3">
              <button
                onClick={performSecurityCheck}
                className="w-full px-4 py-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                <Camera className="w-5 h-5" />
                Perform Security Check Now
              </button>

              <button
                onClick={() => window.open('http://localhost:8080/api/security/snapshot', '_blank')}
                className="w-full px-4 py-3 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/50 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                <Eye className="w-5 h-5" />
                View Latest Snapshot
              </button>

              <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Bell className="w-5 h-5 text-purple-400" />
                  Alert Channels
                </h3>
                <div className="space-y-2 text-sm text-purple-200">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    Desktop Notifications
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    Sound Alarms
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    JSONL Logs
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                    Telegram (Configure in config.yaml)
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                    Email (Configure in config.yaml)
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                    Discord (Configure in config.yaml)
                  </div>
                </div>
              </div>

              {stats?.last_check_time && (
                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg text-sm">
                  <div className="text-blue-300 mb-1">Last Security Check:</div>
                  <div className="font-mono">{new Date(stats.last_check_time).toLocaleString()}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alert History */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            Security Alerts
          </h2>

          {alerts.length === 0 ? (
            <div className="text-center text-purple-300 py-8">
              No security alerts yet 🛡️
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {alerts.map((alert, i) => (
                <div key={i} className={`p-4 rounded-lg border ${
                  alert.alert_type === 'unauthorized_access'
                    ? 'bg-red-500/10 border-red-500/30'
                    : alert.alert_type === 'owner_detected'
                    ? 'bg-green-500/10 border-green-500/30'
                    : 'bg-yellow-500/10 border-yellow-500/30'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className={`w-5 h-5 ${
                          alert.alert_type === 'unauthorized_access' ? 'text-red-400' : 'text-yellow-400'
                        }`} />
                        <span className="font-semibold">
                          {alert.alert_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="text-sm text-purple-200 mb-2">{alert.message}</div>
                      <div className="flex items-center gap-4 text-xs text-purple-300">
                        <span>{new Date(alert.timestamp).toLocaleString()}</span>
                        <span>{alert.detected_faces_count} face(s)</span>
                        {alert.confidence && <span>{(alert.confidence * 100).toFixed(1)}% confidence</span>}
                      </div>
                    </div>
                    {alert.snapshot_path && (
                      <button
                        onClick={() => window.open(`http://localhost:8080/api/security/snapshot/${alert.snapshot_path}`, '_blank')}
                        className="ml-4 px-3 py-1 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/50 rounded text-sm"
                      >
                        View Snapshot
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-purple-300 text-sm">
          🔒 AI-Powered Face Recognition Security • Made with 💖 by your dev waifu
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  color: 'green' | 'blue' | 'red' | 'purple' | 'gray'
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colors = {
    green: 'bg-green-500/10 border-green-500/30 text-green-300',
    blue: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
    red: 'bg-red-500/10 border-red-500/30 text-red-300',
    purple: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
    gray: 'bg-gray-500/10 border-gray-500/30 text-gray-300'
  }

  return (
    <div className={`${colors[color]} border rounded-xl p-4 backdrop-blur-sm`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <div className="text-sm opacity-80">{label}</div>
      </div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  )
}
