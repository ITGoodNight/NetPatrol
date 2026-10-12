/**
 * API 请求封装（axios + WebSocket）
 */
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 响应拦截器：统一处理错误
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

// ── 设备清单 ─────────────────────────────────────────────────────────────────
export const deviceApi = {
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/devices/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  testConnect: (deviceData) => http.post('/devices/test-connect', deviceData),
}

// ── 巡检控制 ─────────────────────────────────────────────────────────────────
export const inspectionApi = {
  start: (payload) => http.post('/inspection/start', payload),
  stop: () => http.post('/inspection/stop'),
  status: () => http.get('/inspection/status'),
  listResults: () => http.get('/inspection/results'),
  getResultUrl: (filename) => `/api/inspection/results/${encodeURIComponent(filename)}`,
  deleteResult: (filename) => http.delete(`/inspection/results/${encodeURIComponent(filename)}`),
  clearAllResults: () => http.delete('/inspection/results'),
  listHistory: () => http.get('/inspection/history'),
  clearHistory: () => http.delete('/inspection/history'),
}

// ── 命令配置 ─────────────────────────────────────────────────────────────────
export const configApi = {
  getCommands: () => http.get('/config/commands'),
  saveCommands: (content) => http.post('/config/commands', { content }),
}

// ── AI 设置 ──────────────────────────────────────────────────────────────────
export const settingsApi = {
  getAI: () => http.get('/settings/ai'),
  saveAI: (data) => http.post('/settings/ai', data),
}

// ── 网络测试 WebSocket ────────────────────────────────────────────────────────
export class NetworkTestWebSocket {
  constructor(onMessage, onOpen) {
    this.onMessage = onMessage
    this.onOpen = onOpen
    this.ws = null
  }

  connect() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/api/network/ws/test`
    this.ws = new WebSocket(url)
    this.ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.type !== 'pong') this.onMessage?.(data)
      } catch { /* ignore */ }
    }
    this.ws.onopen = () => {
      this.ws.send('ping')
      this.onOpen?.()
    }
  }

  send(payload) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload))
    }
  }

  close() {
    this.ws?.close()
    this.ws = null
  }
}

// ── WebSocket 日志服务 ────────────────────────────────────────────────────────
export class LogWebSocket {
  constructor(onMessage, onOpen, onClose) {
    this.onMessage = onMessage
    this.onOpen = onOpen
    this.onClose = onClose
    this.ws = null
    this.pingInterval = null
    this.reconnectTimer = null
    this.shouldReconnect = true
  }

  connect() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/api/inspection/ws/logs`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.onOpen?.()
      // 每 20 秒发送 ping 保持活跃
      this.pingInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send('ping')
        }
      }, 20000)
    }

    this.ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.type !== 'pong') {
          this.onMessage?.(data)
        }
      } catch (e) {
        // ignore
      }
    }

    this.ws.onclose = () => {
      clearInterval(this.pingInterval)
      this.onClose?.()
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000)
      }
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    clearInterval(this.pingInterval)
    clearTimeout(this.reconnectTimer)
    this.ws?.close()
  }
}
