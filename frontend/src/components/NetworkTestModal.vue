<template>
  <a-modal
    v-model:open="visible"
    title="网络测试"
    :width="780"
    :mask-closable="false"
    :footer="null"
    destroy-on-close
    @cancel="handleClose"
  >
    <a-tabs v-model:activeKey="activeTab" class="network-test-tabs">
      <!-- ── Ping ── -->
      <a-tab-pane key="ping" tab="Ping 测试">
        <div class="test-toolbar">
          <a-input
            v-model:value="pingTarget"
            placeholder="目标 IP 或域名，如 192.168.1.1"
            style="width:220px"
            :disabled="pingRunning"
            @press-enter="togglePing"
          />
          <a-select v-model:value="pingInterval" style="width:100px" :disabled="pingRunning">
            <a-select-option :value="1">1 秒/次</a-select-option>
            <a-select-option :value="2">2 秒/次</a-select-option>
            <a-select-option :value="3">3 秒/次</a-select-option>
          </a-select>
          <a-button
            type="primary"
            :loading="pingRunning && !pingSeries.length"
            @click="togglePing"
          >
            <template v-if="pingRunning">
              <PauseCircleOutlined /> 停止
            </template>
            <template v-else>
              <CaretRightOutlined /> 开始
            </template>
          </a-button>
          <a-button @click="clearPing" :disabled="!pingSeries.length">清空</a-button>
        </div>

        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-label">最新</span>
            <span class="stat-value" :class="latestLatencyClass">{{ latestLabel }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均</span>
            <span class="stat-value">{{ avgLabel }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最小</span>
            <span class="stat-value ok">{{ minLabel }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大</span>
            <span class="stat-value warn">{{ maxLabel }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">丢包</span>
            <span class="stat-value" :class="lossRate > 0 ? 'fail' : 'ok'">{{ lossLabel }}</span>
          </div>
          <div class="stat-item status-badge">
            <span class="ni-status-dot" :class="connectStatus" />
            {{ statusText }}
          </div>
        </div>

        <div class="chart-wrap">
          <canvas ref="chartCanvas" class="latency-chart" />
        </div>
      </a-tab-pane>

      <!-- ── Tracert ── -->
      <a-tab-pane key="tracert" tab="Tracert 路由追踪">
        <div class="test-toolbar">
          <a-input
            v-model:value="tracertTarget"
            placeholder="目标 IP 或域名"
            style="width:220px"
            :disabled="tracertRunning"
            @press-enter="startTracert"
          />
          <a-input-number
            v-model:value="maxHops"
            :min="1"
            :max="64"
            style="width:100px"
            addon-before="跳数"
            :disabled="tracertRunning"
          />
          <a-button type="primary" :loading="tracertRunning" @click="toggleTracert">
            <template v-if="tracertRunning">
              <PauseCircleOutlined /> 停止
            </template>
            <template v-else>
              <CaretRightOutlined /> 开始追踪
            </template>
          </a-button>
          <a-button @click="tracertLines = []" :disabled="tracertRunning || !tracertLines.length">清空</a-button>
        </div>

        <div class="tracert-log">
          <div v-for="(line, i) in tracertLines" :key="i" class="tracert-line">{{ line }}</div>
          <div v-if="tracertRunning" class="tracert-line running">追踪中...</div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { message } from 'ant-design-vue'
import { CaretRightOutlined, PauseCircleOutlined } from '@ant-design/icons-vue'
import { NetworkTestWebSocket } from '@/api/index.js'

const visible = defineModel('open', { type: Boolean, default: false })

const activeTab = ref('ping')
const pingTarget = ref('192.168.1.1')
const pingInterval = ref(1)
const pingRunning = ref(false)
const pingSeries = ref([])

const tracertTarget = ref('192.168.1.1')
const maxHops = ref(30)
const tracertRunning = ref(false)
const tracertLines = ref([])

const chartCanvas = ref(null)
let ws = null
let chartResizeObs = null

const okPoints = computed(() => pingSeries.value.filter(p => p.status === 'ok' && p.latency_ms != null))
const lossRate = computed(() => {
  if (!pingSeries.value.length) return 0
  const lost = pingSeries.value.filter(p => p.status !== 'ok').length
  return Math.round((lost / pingSeries.value.length) * 100)
})

const latestPoint = computed(() => pingSeries.value[pingSeries.value.length - 1])
const latestLabel = computed(() => {
  const p = latestPoint.value
  if (!p) return '—'
  if (p.status === 'ok' && p.latency_ms != null) return `${p.latency_ms} ms`
  return p.status === 'timeout' ? '超时' : '失败'
})
const latestLatencyClass = computed(() => {
  const p = latestPoint.value
  if (!p || p.status !== 'ok') return 'fail'
  return p.latency_ms > 100 ? 'warn' : 'ok'
})
const avgLabel = computed(() => {
  if (!okPoints.value.length) return '—'
  const avg = okPoints.value.reduce((s, p) => s + p.latency_ms, 0) / okPoints.value.length
  return `${avg.toFixed(1)} ms`
})
const minLabel = computed(() => {
  if (!okPoints.value.length) return '—'
  return `${Math.min(...okPoints.value.map(p => p.latency_ms))} ms`
})
const maxLabel = computed(() => {
  if (!okPoints.value.length) return '—'
  return `${Math.max(...okPoints.value.map(p => p.latency_ms))} ms`
})
const lossLabel = computed(() => `${lossRate.value}%`)

const connectStatus = computed(() => {
  if (!pingSeries.value.length) return 'idle'
  if (lossRate.value === 100) return 'fail'
  if (lossRate.value > 0) return 'warn'
  return 'ok'
})
const statusText = computed(() => {
  if (!pingRunning.value && !pingSeries.value.length) return '未测试'
  if (pingRunning.value && !pingSeries.value.length) return '探测中...'
  if (connectStatus.value === 'ok') return '连通正常'
  if (connectStatus.value === 'warn') return '部分丢包'
  if (connectStatus.value === 'fail') return '不可达'
  return '就绪'
})

function ensureWs(onReady) {
  if (ws?.ws?.readyState === WebSocket.OPEN) {
    onReady?.()
    return
  }
  ws?.close()
  ws = new NetworkTestWebSocket(handleWsMessage, onReady)
  ws.connect()
}

function sendAction(payload) {
  ensureWs(() => ws?.send(payload))
}

function handleWsMessage(data) {
  if (data.type === 'ping') {
    pingSeries.value.push(data)
    if (pingSeries.value.length > 120) pingSeries.value.shift()
    nextTick(drawChart)
  } else if (data.type === 'ping_started') {
    pingRunning.value = true
  } else if (data.type === 'ping_stopped' || data.type === 'stopped') {
    pingRunning.value = false
    tracertRunning.value = false
  } else if (data.type === 'tracert_start') {
    tracertRunning.value = true
    tracertLines.value = []
  } else if (data.type === 'tracert_line') {
    tracertLines.value.push(data.line)
  } else if (data.type === 'tracert_done') {
    tracertRunning.value = false
  } else if (data.type === 'error') {
    message.error(data.message)
    pingRunning.value = false
    tracertRunning.value = false
  }
}

function togglePing() {
  if (pingRunning.value) {
    ws?.send({ action: 'ping_stop' })
    pingRunning.value = false
    return
  }
  const target = pingTarget.value.trim()
  if (!target) {
    message.warning('请输入目标地址')
    return
  }
  ensureWs(() => {
    ws?.send({ action: 'ping_start', target, interval: pingInterval.value })
    pingRunning.value = true
  })
}

function clearPing() {
  pingSeries.value = []
  nextTick(drawChart)
}

function toggleTracert() {
  if (tracertRunning.value) {
    ws?.send({ action: 'stop' })
    tracertRunning.value = false
    return
  }
  startTracert()
}

function startTracert() {
  const target = tracertTarget.value.trim()
  if (!target) {
    message.warning('请输入目标地址')
    return
  }
  tracertLines.value = []
  sendAction({ action: 'tracert', target, max_hops: maxHops.value })
  tracertRunning.value = true
}

function drawChart() {
  const canvas = chartCanvas.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.parentElement.getBoundingClientRect()
  const w = rect.width
  const h = 240
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = `${w}px`
  canvas.style.height = `${h}px`

  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, w, h)

  // 背景
  ctx.fillStyle = '#fafafa'
  ctx.fillRect(0, 0, w, h)

  const pad = { top: 28, right: 16, bottom: 28, left: 44 }
  const chartW = w - pad.left - pad.right
  const chartH = h - pad.top - pad.bottom

  const points = pingSeries.value
  const latencies = points.filter(p => p.status === 'ok' && p.latency_ms != null).map(p => p.latency_ms)
  const yMax = Math.max(50, ...(latencies.length ? latencies : [50])) * 1.25

  // 网格
  ctx.strokeStyle = '#e5e6eb'
  ctx.lineWidth = 1
  ctx.fillStyle = '#86909c'
  ctx.font = '11px Inter, sans-serif'
  ctx.fillText('ms', 4, 11)
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (chartH / 4) * i
    const val = yMax - (yMax / 4) * i
    ctx.beginPath()
    ctx.moveTo(pad.left, y)
    ctx.lineTo(pad.left + chartW, y)
    ctx.stroke()
    ctx.fillText(`${Math.round(val)}`, 4, y + 4)
  }

  if (!points.length) return

  // 折线区域
  const stepX = points.length > 1 ? chartW / (points.length - 1) : chartW

  // 填充区域
  ctx.beginPath()
  points.forEach((p, i) => {
    const x = pad.left + i * stepX
    const yVal = p.status === 'ok' && p.latency_ms != null ? p.latency_ms : yMax
    const y = pad.top + chartH - (yVal / yMax) * chartH
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.lineTo(pad.left + (points.length - 1) * stepX, pad.top + chartH)
  ctx.lineTo(pad.left, pad.top + chartH)
  ctx.closePath()
  ctx.fillStyle = 'rgba(22, 119, 255, 0.08)'
  ctx.fill()

  // 折线
  ctx.beginPath()
  points.forEach((p, i) => {
    const x = pad.left + i * stepX
    const yVal = p.status === 'ok' && p.latency_ms != null ? p.latency_ms : yMax
    const y = pad.top + chartH - (yVal / yMax) * chartH
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.strokeStyle = '#1677ff'
  ctx.lineWidth = 2
  ctx.stroke()

  // 数据点
  points.forEach((p, i) => {
    const x = pad.left + i * stepX
    const isOk = p.status === 'ok' && p.latency_ms != null
    const yVal = isOk ? p.latency_ms : yMax
    const y = pad.top + chartH - (yVal / yMax) * chartH
    ctx.beginPath()
    ctx.arc(x, y, isOk ? 3 : 4, 0, Math.PI * 2)
    ctx.fillStyle = isOk ? '#1677ff' : '#ff4d4f'
    ctx.fill()
  })
}

function handleClose() {
  ws?.send({ action: 'stop' })
  pingRunning.value = false
  tracertRunning.value = false
}

watch(visible, (v) => {
  if (v) {
    nextTick(() => {
      drawChart()
      if (!chartResizeObs && chartCanvas.value?.parentElement) {
        chartResizeObs = new ResizeObserver(() => drawChart())
        chartResizeObs.observe(chartCanvas.value.parentElement)
      }
    })
  } else {
    handleClose()
  }
})

watch(pingSeries, () => nextTick(drawChart), { deep: true })

onBeforeUnmount(() => {
  ws?.send({ action: 'stop' })
  ws?.close()
  chartResizeObs?.disconnect()
})
</script>

<style scoped>
.network-test-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 12px;
}
.test-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.stat-item {
  flex: 1;
  min-width: 72px;
  padding: 8px 10px;
  background: #f7f8fa;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  text-align: center;
}
.stat-item.status-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #4e5969;
}
.stat-label {
  display: block;
  font-size: 11px;
  color: #86909c;
  margin-bottom: 2px;
}
.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}
.stat-value.ok { color: #52c41a; }
.stat-value.warn { color: #faad14; }
.stat-value.fail { color: #ff4d4f; }

.ni-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ni-status-dot.idle { background: #c9cdd4; }
.ni-status-dot.ok { background: #52c41a; box-shadow: 0 0 4px rgba(82,196,26,.5); }
.ni-status-dot.warn { background: #faad14; }
.ni-status-dot.fail { background: #ff4d4f; animation: blink 1s infinite; }

@keyframes blink {
  50% { opacity: 0.4; }
}

.chart-wrap {
  position: relative;
  height: 240px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}
.latency-chart {
  display: block;
  width: 100%;
  height: 240px;
}

.tracert-log {
  height: 320px;
  overflow-y: auto;
  background: #1d2129;
  border-radius: 8px;
  padding: 12px 14px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.7;
  color: #e5e6eb;
}
.tracert-line {
  white-space: pre-wrap;
  word-break: break-all;
}
.tracert-line.running {
  color: #1677ff;
}
</style>
