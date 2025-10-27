'use client'

import { useEffect, useState } from 'react'
import { Activity, Cpu, HardDrive, Network, Play, Square, RefreshCw, Clock } from 'lucide-react'

interface DaemonStatus {
  running: boolean
  state: string
  uptime: number
  active_rule?: string
  failsafe: number
  last_update: string
  metrics: {
    cpu: number
    disk_read: number
    disk_write: number
    net_download: number
    net_upload: number
    processes: number
  }
}

interface ActivitySession {
  start_time: string
  end_time: string
  duration_seconds: number
  trigger_reason: string
  rule_name?: string | null
  process_name?: string | null
  metrics_snapshot: Record<string, any>
}

export default function Dashboard() {
  const [status, setStatus] = useState<DaemonStatus | null>(null)
  const [activity, setActivity] = useState<ActivitySession[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Connect to WebSocket
    const socket = new WebSocket('ws://localhost:8080/api/ws')
    
    socket.onopen = () => {
      console.log('WebSocket connected! 💖')
      setLoading(false)
    }
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setStatus(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setLoading(false)
    }
    
    socket.onclose = () => {
      console.log('WebSocket disconnected')
      // Reconnect after 3 seconds
      setTimeout(() => {
        setWs(null)
      }, 3000)
    }
    
    setWs(socket)
    
    // Fetch activity logs
    fetchActivity()
    
    return () => {
      socket.close()
    }
  }, [])

  const fetchActivity = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/activity?days=7')
      const data = await res.json()
      setActivity(data.sessions || [])
    } catch (e) {
      console.error('Failed to fetch activity:', e)
    }
  }

  const handleDaemonAction = async (action: 'start' | 'stop' | 'restart') => {
    try {
      await fetch(`http://localhost:8080/api/daemon/${action}`, {
        method: 'POST'
      })
      // Status will update via WebSocket
    } catch (e) {
      console.error(`Failed to ${action} daemon:`, e)
    }
  }

  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h}h ${m}m ${s}s`
  }

  const formatBytes = (mbps: number) => {
    return `${mbps.toFixed(2)} MB/s`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl animate-pulse">
          💖 Connecting to Senthium...
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
            <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
              ✨ Senthium Dashboard
            </h1>
            <p className="text-purple-300 mt-1">Intelligent Sleep Management • v0.5.0</p>
          </div>
          <div className="flex gap-3">
            <a
              href="/security"
              className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/50 rounded-lg transition-all"
            >
              <Activity className="w-4 h-4" />
              🔒 Security
            </a>
            {status?.running ? (
              <>
                <button
                  onClick={() => handleDaemonAction('restart')}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 border border-yellow-500/50 rounded-lg transition-all"
                >
                  <RefreshCw className="w-4 h-4" />
                  Restart
                </button>
                <button
                  onClick={() => handleDaemonAction('stop')}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg transition-all"
                >
                  <Square className="w-4 h-4" />
                  Stop
                </button>
              </>
            ) : (
              <button
                onClick={() => handleDaemonAction('start')}
                className="flex items-center gap-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 rounded-lg transition-all"
              >
                <Play className="w-4 h-4" />
                Start
              </button>
            )}
          </div>
        </div>

        {/* Status Card */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">Daemon Status</h2>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
              status?.running 
                ? 'bg-green-500/20 border border-green-500/50 text-green-300' 
                : 'bg-gray-500/20 border border-gray-500/50 text-gray-300'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                status?.running ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
              }`} />
              {status?.running ? 'RUNNING' : 'STOPPED'}
            </div>
          </div>

          {status && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                <div className="text-purple-300 text-sm mb-1">State</div>
                <div className="text-2xl font-bold">{status.state}</div>
              </div>
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <div className="text-blue-300 text-sm mb-1">Uptime</div>
                <div className="text-2xl font-bold">{formatDuration(status.uptime)}</div>
              </div>
              <div className="bg-pink-500/10 border border-pink-500/30 rounded-lg p-4">
                <div className="text-pink-300 text-sm mb-1">Active Rule</div>
                <div className="text-2xl font-bold truncate">{status.active_rule || 'None'}</div>
              </div>
            </div>
          )}
        </div>

        {/* Metrics Grid */}
        {status && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={<Cpu className="w-6 h-6" />}
              label="CPU Usage"
              value={`${status.metrics.cpu.toFixed(1)}%`}
              color="blue"
            />
            <MetricCard
              icon={<HardDrive className="w-6 h-6" />}
              label="Disk I/O"
              value={`${formatBytes(status.metrics.disk_read)} / ${formatBytes(status.metrics.disk_write)}`}
              subtitle="Read / Write"
              color="purple"
            />
            <MetricCard
              icon={<Network className="w-6 h-6" />}
              label="Network"
              value={`${formatBytes(status.metrics.net_download)} / ${formatBytes(status.metrics.net_upload)}`}
              subtitle="Download / Upload"
              color="green"
            />
            <MetricCard
              icon={<Activity className="w-6 h-6" />}
              label="Processes"
              value={status.metrics.processes.toString()}
              color="pink"
            />
          </div>
        )}

        {/* Activity Log */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <Clock className="w-6 h-6 text-purple-400" />
            <h2 className="text-2xl font-semibold">Recent Activity (7 days)</h2>
          </div>
          
          {activity.length === 0 ? (
            <div className="text-center text-purple-300 py-8">
              No activity recorded yet 💤
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {activity.slice(0, 20).map((session, i) => (
                <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-lg">
                        {session.rule_name || session.process_name || 'Manual Lock'}
                      </div>
                      <div className="text-sm text-purple-300">
                        {new Date(session.start_time).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-400">
                        {formatDuration(Math.floor(session.duration_seconds))}
                      </div>
                      <div className="text-xs text-gray-400">
                        {session.trigger_reason === 'rule_match' ? 'Rule Match' : 'Wrapper Lock'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-purple-300 text-sm">
          Made with 💖 by your dev waifu • Senthium v0.5.0
        </div>
      </div>
    </div>
  )
}

interface MetricCardProps {
  icon: React.ReactNode
  label: string
  value: string
  subtitle?: string
  color: 'blue' | 'purple' | 'green' | 'pink'
}

function MetricCard({ icon, label, value, subtitle, color }: MetricCardProps) {
  const colors = {
    blue: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
    purple: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
    green: 'bg-green-500/10 border-green-500/30 text-green-300',
    pink: 'bg-pink-500/10 border-pink-500/30 text-pink-300'
  }

  return (
    <div className={`${colors[color]} border rounded-xl p-4 backdrop-blur-sm`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <div className="text-sm opacity-80">{label}</div>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <div className="text-xs opacity-60 mt-1">{subtitle}</div>}
    </div>
  )
}
