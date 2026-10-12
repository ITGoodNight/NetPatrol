<template>
  <div class="layout-root">

    <!-- ══ 顶部导航栏（黑灰风格）═══════════════════════════════════ -->
    <header class="ni-navbar">
      <!-- 左：品牌区 -->
      <div class="brand">
        <div class="brand-icon">
          <img src="/icons/icon.png" alt="NetPatrol" class="brand-logo" />
        </div>
        <span class="brand-name">NetPatrol</span>
      </div>

      <!-- 中：导航菜单 -->
      <nav class="nav-menu">
        <button
          class="nav-item"
          @click="showCmdConfig = true"
        >
          <FileTextOutlined />
          巡检命令
        </button>
        <button
          class="nav-item"
          @click="loadReports(); showReportPanel = true"
        >
          <FolderOpenOutlined />
          巡检报告
        </button>
        <button
          class="nav-item"
          @click="showNetworkTest = true"
        >
          <GlobalOutlined />
          网络测试
        </button>
      </nav>

      <!-- 右：设置 -->
      <div class="nav-right">
        <a
          v-if="GITHUB_URL"
          class="nav-icon-btn"
          :href="GITHUB_URL"
          target="_blank"
          rel="noopener noreferrer"
          title="GitHub 仓库"
        >
          <GithubOutlined />
        </a>
        <button v-else class="nav-icon-btn" disabled title="GitHub（链接待填）">
          <GithubOutlined />
        </button>

        <button class="nav-icon-btn" @click="showAbout = true" title="免责声明">
          <WarningOutlined />
        </button>
      </div>
    </header>

    <!-- ══ 页面主体 ════════════════════════════════════════════════════════════ -->
    <div class="page-body">

      <!-- ── 左侧配置面板 ────────────────────────────────────────────────── -->
      <aside class="ni-sidebar">

        <!-- 统计卡片组：2×2 网格，防止截断 -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-num" style="color:#1677ff">{{ progress.total }}</div>
            <div class="stat-label">总设备</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#52c41a">{{ progress.successful }}</div>
            <div class="stat-label">成功</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#ff4d4f">{{ progress.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <div class="stat-card">
            <div class="stat-num" style="color:#faad14">{{ progress.completed }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="ni-card" style="padding:12px 16px 12px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:12px;color:#4e5969;font-weight:600;display:flex;align-items:center;gap:6px">
              <span class="status-dot" :class="running ? 'running' : 'idle'" />
              {{ running ? '执行进度...' : '就绪' }}
            </span>
            <span style="font-size:12px;color:#86909c">
              {{ progress.completed }}/{{ progress.total }}
            </span>
          </div>
          <a-progress
            :percent="progressPercent"
            :status="running ? 'active' : 'normal'"
            :stroke-color="{ '0%': '#1677ff', '100%': '#52c41a' }"
            size="small"
          />
        </div>

        <!-- 执行配置 -->
        <div class="ni-card" style="padding:0;overflow:hidden">
          <div class="section-header">
            <div class="section-icon">
              <SlidersOutlined />
              <span>执行配置</span>
            </div>
          </div>
          <div style="padding:12px 16px;display:flex;flex-direction:column;gap:10px">

            <div class="config-row">
              <label>并发线程</label>
              <a-input-number
                v-model:value="maxWorkers"
                :min="1" :max="100"
                style="width:80px"
                :disabled="running"
                @change="handleExecConfigChange"
              />
              <a-tooltip title="同时连接的最大设备数量">
                <QuestionCircleOutlined style="color:#c9cdd4;cursor:help" />
              </a-tooltip>
            </div>

            <div class="config-row">
              <label>输出格式</label>
              <a-select v-model:value="outputFormat" style="width:100px" :disabled="running" @change="handleExecConfigChange">
                <a-select-option value="HTML">HTML</a-select-option>
                <a-select-option value="TXT">TXT</a-select-option>
              </a-select>
            </div>





          </div>
        </div>

        <!-- 操作按鈕：同行排列 -->
        <div style="display:flex;gap:8px">
          <a-button
            class="ni-btn-start"
            :class="{ 'is-running': running }"
            block
            :loading="running"
            @click="handleStart"
          >
            <PlayCircleOutlined v-if="!running" />
            {{ running ? '执行中...' : '开始执行' }}
          </a-button>
          <a-button
            class="ni-btn-stop"
            block
            :disabled="!running"
            @click="handleStop"
          >
            <PauseCircleOutlined /> 停止
          </a-button>
        </div>

        <!-- 定时巡检 -->
        <div class="ni-card schedule-card">
          <div class="section-header" style="flex-shrink:0">
            <div class="section-icon">
              <ClockCircleOutlined />
              <span>定时巡检</span>
            </div>
          </div>
          <div class="schedule-card-body">
            <div class="config-row">
              <label>启用定时</label>
              <a-switch
                v-model:checked="enableSchedule"
                checked-children="开启"
                un-checked-children="关闭"
                :disabled="running"
                @change="handleScheduleChange"
              />
            </div>

            <template v-if="enableSchedule">
              <div class="config-row" style="flex-direction:column;align-items:flex-start;gap:6px">
                <label style="min-width:auto">巡检模式</label>
                <a-radio-group
                  v-model:value="scheduleMode"
                  button-style="solid"
                  class="ni-radio-segment"
                  :disabled="running"
                  @change="handleScheduleChange"
                >
                  <a-radio-button value="daily">每日定时</a-radio-button>
                  <a-radio-button value="date">指定日期</a-radio-button>
                </a-radio-group>
              </div>

              <div class="config-row" style="display:flex;gap:8px;align-items:stretch">
                <div style="flex:1.3;display:flex;flex-direction:column;gap:6px;min-width:0">
                  <label style="min-width:auto">{{ scheduleMode === 'date' ? '巡检日期' : '巡检时间' }}</label>
                  <a-date-picker
                    v-if="scheduleMode === 'date'"
                    v-model:value="scheduleDateTime"
                    :show-time="{ showHour: true, showMinute: true, format: 'HH:mm' }"
                    format="YYYY-MM-DD"
                    size="small"
                    style="width:100%"
                    :disabled="running"
                    @change="handleScheduleChange"
                  />
                  <a-time-picker
                    v-else
                    v-model:value="scheduleTime"
                    format="HH:mm"
                    size="small"
                    style="width:100%"
                    :disabled="running"
                    @change="handleScheduleChange"
                  />
                </div>
                <div style="flex:1;display:flex;flex-direction:column;gap:6px;min-width:0">
                  <label style="min-width:auto">巡检次数</label>
                  <a-input-number
                    v-model:value="scheduleCount"
                    :min="1"
                    :max="24"
                    :precision="0"
                    size="small"
                    style="width:100%"
                    :disabled="running"
                    @change="handleScheduleChange"
                  />
                </div>
              </div>
            </template>

            <!-- 失败重试 + 声音提醒（仅定时开启时显示） -->
            <div v-if="enableSchedule" class="config-row config-row-dual">
              <div class="config-switch-item">
                <label>失败重试</label>
                <a-switch
                  v-model:checked="enableRetry"
                  checked-children="开启"
                  un-checked-children="关闭"
                  :disabled="running"
                  @change="handleRetryChange"
                />
              </div>
              <div class="config-switch-item">
                <label>声音提醒</label>
                <a-switch
                  v-model:checked="enableSoundAlert"
                  checked-children="开启"
                  un-checked-children="关闭"
                  :disabled="running"
                  @change="handleSoundAlertChange"
                />
              </div>
            </div>
          </div>
        </div>

      </aside>

      <!-- ── 右侧主内容区 ─────────────────────────────────────────────────── -->
      <main class="ni-main">

        <!-- 设备列表 -->
        <DeviceTable
          :devices="devices"
          @update:devices="onDevicesUpdated"
          style="flex-shrink:0"
        />

        <!-- 日志控制台 -->
        <div class="ni-card log-panel">
          <div class="section-header" style="flex-shrink:0">
            <div class="section-icon">
              <CodeOutlined />
              <span>执行日志</span>
            </div>
            <a-button type="text" size="small" @click="logs = []" title="清空日志">
              <DeleteOutlined />
            </a-button>
          </div>
          <div style="flex:1;padding:8px;min-height:0;overflow:hidden">
            <LogConsole :logs="logs" :auto-scroll="autoScroll" style="height:100%" />
          </div>
        </div>

      </main>
    </div>

    <!-- ══ 弹窗 & 抽屉 ════════════════════════════════════════════════════════ -->
    <AboutModal v-model:open="showAbout" />
    <CommandConfigModal v-model:open="showCmdConfig" />
    <ReportViewerModal v-model:open="showReport" :filename="reportFilename" />
    <NetworkTestModal v-model:open="showNetworkTest" />

    <!-- 巡检报告列表抽屉 -->
    <a-drawer
      title="历史巡检报告"
      placement="right"
      :width="380"
      v-model:open="showReportPanel"
    >
      <template #extra>
        <div style="display:flex;gap:8px">
          <a-button type="text" size="small" @click="loadReports" title="刷新">
            <ReloadOutlined />
          </a-button>
          <a-button type="text" size="small" danger @click="handleClearAllReports" title="清空所有报告" v-if="reports.length">
            <DeleteOutlined style="color:#ff4d4f" />
          </a-button>
        </div>
      </template>
      <div style="overflow-y:auto;height:100%;padding:4px">
        <div
          v-if="!reports.length"
          style="text-align:center;padding:48px 0;color:#c9cdd4;font-size:13px"
        >
          暂无历史报告
        </div>
        <div
          v-for="r in reports"
          :key="r.name"
          class="report-item"
          @click="openReport(r.name)"
        >
          <FileOutlined style="color:#1677ff;flex-shrink:0;margin-top:2px" />
          <div style="min-width:0;flex:1">
            <div class="report-name" style="font-weight:600;color:#1d2129">{{ r.name }}</div>
            <div class="report-size" style="font-size:11px;color:#86909c;margin-top:2px">{{ formatSize(r.size) }}</div>
          </div>
          <a-button
            type="text"
            size="small"
            danger
            class="report-delete-btn"
            @click.stop="handleDeleteReport(r.name)"
            title="删除报告"
          >
            <DeleteOutlined />
          </a-button>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  FolderOpenOutlined, FileTextOutlined, FileOutlined,
  PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined,
  CodeOutlined, SlidersOutlined, QuestionCircleOutlined,
  AppstoreOutlined, DeleteOutlined, LinkOutlined, WarningOutlined,
  ClockCircleOutlined, GlobalOutlined, GithubOutlined,
} from '@ant-design/icons-vue'

import DeviceTable from '@/components/DeviceTable.vue'
import LogConsole from '@/components/LogConsole.vue'
import CommandConfigModal from '@/components/CommandConfigModal.vue'
import ReportViewerModal from '@/components/ReportViewerModal.vue'
import AboutModal from '@/components/AboutModal.vue'
import NetworkTestModal from '@/components/NetworkTestModal.vue'

import { inspectionApi, settingsApi, LogWebSocket } from '@/api/index.js'
import { usePageTitle } from '@/composables/usePageTitle.js'
import { playCompletionSound, playPreviewSound } from '@/composables/useCompletionSound.js'
import dayjs from 'dayjs'

// 填上你的 GitHub 仓库地址：导航栏的 GitHub 图标点击即在【新标签页】打开该地址
const GITHUB_URL = 'https://github.com/ITGoodNight/NetPatrol'

// ── 状态 ─────────────────────────────────────────────────────────────────────
const devices = ref([])
const logs = ref([])
const running = ref(false)
const wsConnected = ref(false)
const autoScroll = ref(true)
const showCmdConfig = ref(false)
const showAbout = ref(false)
const showReport = ref(false)
const showReportPanel = ref(false)
const showNetworkTest = ref(false)
const reportFilename = ref('')
const reports = ref([])
const maxWorkers = ref(10)
const outputFormat = ref('HTML')
const activeTab = ref('console')

const enableSchedule = ref(false)
const scheduleMode = ref('daily')
const scheduleTime = ref(null)
const scheduleDate = ref(null)
const scheduleCount = ref(1)
const enableRetry = ref(false)
const enableSoundAlert = ref(false)
const rawSettings = ref({})

// 指定日期模式：把「日期」与「时间」合并为单个日期时间选择器，
// 读写时映射回 scheduleDate / scheduleTime，保存逻辑无需改动
const scheduleDateTime = computed({
  get() {
    if (!scheduleDate.value) return null
    const t = scheduleTime.value
    return scheduleDate.value
      .hour(t ? t.hour() : 9)
      .minute(t ? t.minute() : 0)
      .second(0)
  },
  set(val) {
    if (!val) {
      scheduleDate.value = null
      return
    }
    scheduleDate.value = val
    scheduleTime.value = val
  },
})

const progress = ref({ total: 0, completed: 0, successful: 0, failed: 0 })
const runSummary = ref('')
let runSummaryTimer = null

usePageTitle({
  running,
  progress,
  deviceCount: computed(() => devices.value.length),
  enableSchedule,
  runSummary,
})

const progressPercent = computed(() => {
  if (!progress.value.total) return 0
  return Math.round((progress.value.completed / progress.value.total) * 100)
})

// ── WebSocket ──────────────────────────────────────────────────────────────
let ws = null

function normalizeLogMessage(msg) {
  return String(msg)
    .replace(/^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*/, '')
    .replace(/^\[(INFO|ERROR|WARNING|DEBUG|SUCCESS)\]\s*/i, '')
}

function addLog(level, msg) {
  logs.value.push({
    time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
    level: level.toUpperCase(),
    message: normalizeLogMessage(msg),
  })
  if (logs.value.length > 2000) {
    logs.value.splice(0, 500)
  }
}

function initWS() {
  ws = new LogWebSocket(
    (data) => {
      if (data.type === 'log') {
        addLog(data.level, data.message)
      } else if (data.type === 'progress') {
        progress.value = {
          total: data.total,
          completed: data.completed,
          successful: data.successful,
          failed: data.failed,
        }
      } else if (data.type === 'finished') {
        running.value = false
        const { successful, failed } = progress.value
        runSummary.value = failed > 0
          ? `完成 ✓${successful} ✗${failed}`
          : `完成 ✓${successful} 台`
        clearTimeout(runSummaryTimer)
        runSummaryTimer = setTimeout(() => { runSummary.value = '' }, 8000)

        if (enableSoundAlert.value) {
          playCompletionSound({ failed: progress.value.failed })
        }
        loadReports()
      }
    },
    () => {
      wsConnected.value = true
      addLog('INFO', 'WebSocket 消息隧道建立成功，实时日志监听已就绪...')
    },
    () => { wsConnected.value = false }
  )
  ws.connect()
}

// ── 设备管理 ──────────────────────────────────────────────────────────────
function onDevicesUpdated(devs) {
  const prev = devices.value.length
  devices.value = devs
  try {
    localStorage.setItem('netpatrol_devices', JSON.stringify(devs))
  } catch (e) {
    console.error('保存设备列表到本地失败:', e)
  }
  if (devs.length > prev) {
    addLog('INFO', `设备列表更新：共 ${devs.length} 台设备`)
  }
  if (enableSchedule.value) {
    saveScheduleSettings({ reason: '设备列表变更，已同步至定时任务' })
  }
}

// ── 巡检控制 ──────────────────────────────────────────────────────────────
async function handleStart() {
  if (!devices.value.length) {
    message.warning('请先添加设备')
    return
  }
  try {
    progress.value = { total: 0, completed: 0, successful: 0, failed: 0 }

    await inspectionApi.start({
      devices: devices.value,
      max_workers: maxWorkers.value,
      output_format: outputFormat.value,
    })

    running.value = true
  } catch (e) {
    message.error('启动失败: ' + e.message)
    addLog('ERROR', '启动失败: ' + e.message)
  }
}

async function handleStop() {
  try {
    await inspectionApi.stop()
    addLog('WARNING', '已发送停止信号，等待当前设备任务完成...')
  } catch (e) {
    message.error('停止失败: ' + e.message)
  }
}

// ── 报告管理 ──────────────────────────────────────────────────────────────
async function loadReports() {
  try {
    const res = await inspectionApi.listResults()
    reports.value = res.files || []
  } catch { /* 静默失败 */ }
}

function openReport(name) {
  reportFilename.value = name
  showReport.value = true
}

async function handleDeleteReport(name) {
  Modal.confirm({
    title: '确认删除',
    content: `确认要永久删除报告文件「${name}」吗？`,
    okText: '删除',
    okButtonProps: { type: 'primary', class: 'ni-btn-confirm-danger' },
    cancelText: '取消',
    async onOk() {
      try {
        await inspectionApi.deleteResult(name)
        message.success('删除成功')
        loadReports()
      } catch (e) {
        message.error('删除失败: ' + e.message)
      }
    }
  })
}

async function handleClearAllReports() {
  Modal.confirm({
    title: '确认清空',
    content: '确认要永久删除所有巡检报告吗？此操作无法恢复。',
    okText: '清空全部',
    okButtonProps: { type: 'primary', class: 'ni-btn-confirm-danger' },
    cancelText: '取消',
    async onOk() {
      try {
        await inspectionApi.clearAllResults()
        message.success('清空成功')
        loadReports()
      } catch (e) {
        message.error('清空失败: ' + e.message)
      }
    }
  })
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

// ── 初始加载 ──────────────────────────────────────────────────────────────
function formatScheduleLog(cfg) {
  if (!cfg.enable_schedule) {
    return '定时巡检：已关闭'
  }
  const mode = cfg.schedule_mode === 'date' ? '指定日期' : '每日'
  const time = cfg.schedule_time || '09:00'
  const workers = cfg.max_workers ?? maxWorkers.value
  const fmt = cfg.output_format ?? outputFormat.value
  const count = devices.value.length
  const rounds = cfg.schedule_count ?? scheduleCount.value ?? 1
  if (cfg.schedule_mode === 'date') {
    const date = cfg.schedule_date || '未设置'
    return `定时巡检：已开启 | 模式=${mode} | 日期=${date} | 时间=${time} | 次数=${rounds} | 设备=${count} 台 | 并发=${workers} | 输出=${fmt}`
  }
  return `定时巡检：已开启 | 模式=${mode} | 时间=${time} | 次数=${rounds} | 设备=${count} 台 | 并发=${workers} | 输出=${fmt}`
}

async function loadInitialSettings() {
  try {
    const res = await settingsApi.getAI()
    rawSettings.value = res.config || {}
    outputFormat.value = res.config.output_format ?? 'HTML'
    if (res.config.max_workers) {
      maxWorkers.value = res.config.max_workers
    }

    enableSchedule.value = res.config.enable_schedule ?? false
    scheduleMode.value = res.config.schedule_mode ?? 'daily'
    if (res.config.schedule_time) {
      scheduleTime.value = dayjs(res.config.schedule_time, 'HH:mm')
    }
    if (res.config.schedule_date) {
      scheduleDate.value = dayjs(res.config.schedule_date, 'YYYY-MM-DD')
    }
    const rounds = Number(res.config.schedule_count)
    scheduleCount.value = Number.isFinite(rounds) ? Math.min(24, Math.max(1, Math.round(rounds))) : 1
    enableRetry.value = (res.config.retry_count ?? 0) > 0
    enableSoundAlert.value = res.config.enable_result_notify ?? false
  } catch { /* 默认值 */ }
}

async function saveScheduleSettings(options = {}) {
  try {
    const postData = {
      ...rawSettings.value,
      output_format: outputFormat.value,
      enable_schedule: enableSchedule.value,
      schedule_mode: scheduleMode.value,
      schedule_time: scheduleTime.value ? scheduleTime.value.format('HH:mm') : '09:00',
      schedule_date: scheduleDate.value ? scheduleDate.value.format('YYYY-MM-DD') : '',
      schedule_count: Math.min(24, Math.max(1, Math.round(Number(scheduleCount.value) || 1))),
      max_workers: maxWorkers.value,
      retry_count: enableRetry.value ? 1 : 0,
      enable_result_notify: enableSoundAlert.value,
      schedule_devices: devices.value,
    }
    await settingsApi.saveAI(postData)
    rawSettings.value = postData
    if (postData.enable_schedule && devices.value.length === 0) {
      addLog('WARNING', '定时巡检已开启，但设备列表为空，到点时将跳过执行')
    }
    if (options.reason) {
      addLog('INFO', options.reason)
    }
  } catch (e) {
    message.error('保存定时设置失败: ' + e.message)
    addLog('ERROR', '保存定时设置失败: ' + e.message)
  }
}

function handleScheduleChange() {
  saveScheduleSettings()
}

function handleRetryChange() {
  saveScheduleSettings({
    reason: enableRetry.value ? '失败重试已开启' : '失败重试已关闭',
  })
}

function handleSoundAlertChange() {
  saveScheduleSettings({
    reason: enableSoundAlert.value ? '声音提醒已开启' : '声音提醒已关闭',
  })
  if (enableSoundAlert.value) {
    playPreviewSound()
  }
}

function handleExecConfigChange() {
  if (enableSchedule.value) {
    saveScheduleSettings({ reason: '执行配置变更，已同步至定时任务' })
  }
}

onMounted(() => {
  initWS()
  loadReports()
  loadInitialSettings()
  try {
    const savedVersion = localStorage.getItem('netpatrol_devices_version')
    const saved = localStorage.getItem('netpatrol_devices')

    // 清除历史模拟设备缓存
    if (savedVersion?.startsWith('mock-')) {
      localStorage.removeItem('netpatrol_devices')
      localStorage.removeItem('netpatrol_devices_version')
      devices.value = []
    } else if (saved) {
      devices.value = JSON.parse(saved)
      if (devices.value.length) {
        addLog('INFO', `已载入本地保存的设备列表，共 ${devices.value.length} 台设备`)
      }
    }
  } catch (e) {
    console.error('载入本地设备列表失败:', e)
    devices.value = []
  }
})

onBeforeUnmount(() => {
  clearTimeout(runSummaryTimer)
  ws?.disconnect()
})
</script>

<style scoped>
/* ── 根布局 ───────────────────────────────────────────────── */
.layout-root {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f2f5;
}

/* ══ 顶部导航栏（黑灰风格）════════════════════════════════ */
.ni-navbar {
  height: 52px;
  background: #2d2d2d;
  display: flex;
  align-items: center;
  padding: 0 16px;
  flex-shrink: 0;
  border-bottom: 1px solid #3e3e3e;
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
  position: relative;
  z-index: 100;
}

/* 品牌区 */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 32px;
}
.brand-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.brand-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: .3px;
}
.brand-tag {
  font-size: 10px;
  color: rgba(255,255,255,.5);
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 4px;
  padding: 1px 6px;
  letter-spacing: .5px;
}

/* 中：导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
}
.nav-item {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 13px;
  border: none; background: transparent;
  color: rgba(255,255,255,.5);
  font-size: 13px; cursor: pointer;
  border-radius: 6px;
  transition: all .16s;
  font-family: inherit;
}
.nav-item:hover {
  background: rgba(255,255,255,.07);
  color: rgba(255,255,255,.85);
}
.nav-item.active {
  background: rgba(255,255,255,.1);
  color: #fff;
}

/* 右：状态 */
.nav-right {
  display: flex; align-items: center; gap: 12px;
}
.ws-icon-status {
  font-size: 16px;
  flex-shrink: 0;
}
.ws-icon-status.ok  { color: #52c41a; filter: drop-shadow(0 0 2px rgba(82,196,26,.6)); }
.ws-icon-status.err { color: #ff4d4f; animation: pulse 2s infinite; }

.nav-divider {
  width: 1px; height: 20px;
  background: rgba(255,255,255,.12);
}
.nav-icon-btn {
  width: 34px; height: 34px;
  border: none; background: transparent;
  color: rgba(255,255,255,.6);
  font-size: 16px; cursor: pointer;
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  transition: all .18s;
  text-decoration: none;
}
.nav-icon-btn:hover {
  background: rgba(255,255,255,.1);
  color: #fff;
}

/* ══ 页面主体 ════════════════════════════════════════════════ */
.page-body {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
  min-height: 0;
}

.ni-sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  min-height: 0;
  padding-right: 2px;
  padding-bottom: 0;
}

.ni-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.log-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* 定时巡检卡片：撑满侧栏剩余高度，与右侧日志框底对齐 */
.schedule-card {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.schedule-card-body {
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 统计卡片 - 2×2 网格 */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 8px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 4px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e6eb;
  transition: box-shadow .2s, transform .2s;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,.08);
  transform: translateY(-1px);
}
.stat-num { font-size: 22px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 11px; color: #86909c; margin-top: 3px; }

/* 状态点 */
.status-dot {
  display: inline-block; width: 7px; height: 7px;
  border-radius: 50%; flex-shrink: 0;
}
.status-dot.running { background: #1677ff; animation: pulse 1.4s infinite; }
.status-dot.idle    { background: #c9cdd4; }

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .5; transform: scale(.8); }
}

/* 配置行 */
.config-row {
  display: flex; align-items: center; gap: 8px;
}
.config-row label {
  font-size: 13px; color: #4e5969;
  white-space: nowrap; min-width: 72px;
}

/* 数字输入框：上下调节箭头默认常显（Ant 默认仅悬停/聚焦时出现） */
:deep(.ant-input-number-handler-wrap) {
  opacity: 1;
}

/* 报告列表项 */
.report-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 8px 10px; border-radius: 6px;
  border: 1px solid #e5e6eb; background: #fff;
  cursor: pointer; transition: all .18s; margin-bottom: 6px;
  position: relative;
}
.report-item:hover {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22,119,255,.1);
}
.report-name { font-size: 12px; word-break: break-all; color: #1d2129; }
.report-size { font-size: 11px; color: #86909c; margin-top: 2px; }

.report-delete-btn {
  opacity: 0;
  transition: opacity 0.15s ease-in-out;
  flex-shrink: 0;
  align-self: center;
}
.report-item:hover .report-delete-btn {
  opacity: 1;
}

/* ══ 按钮自定义醒目样式 ════════════════════════════════ */
.ni-btn-start {
  flex: 1; height: 40px; font-weight: 600; border: none;
  background: #1677ff !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.15);
  display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: all .2s ease-in-out;
}
.ni-btn-start:hover:not(:disabled) {
  background: #4096ff !important;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
  transform: translateY(-0.5px);
}
.ni-btn-start:active:not(:disabled) {
  transform: translateY(0);
}
.ni-btn-start.is-running,
.ni-btn-start.ant-btn-loading {
  background: #1677ff !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.15) !important;
  opacity: 1;
  cursor: default;
}
.ni-btn-start.is-running :deep(.ant-btn-loading-icon),
.ni-btn-start.ant-btn-loading :deep(.ant-btn-loading-icon) {
  color: #fff !important;
}
.ni-btn-start:disabled:not(.is-running) {
  background: #f5f5f5 !important;
  color: rgba(0, 0, 0, 0.25) !important;
  border: 1px solid #d9d9d9 !important;
  box-shadow: none;
}

.ni-btn-stop {
  flex: 1; height: 40px; font-weight: 600; border: none;
  background: #ff4d4f !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.15);
  display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: all .2s ease-in-out;
}
.ni-btn-stop:hover:not(:disabled) {
  background: #ff7875 !important;
  box-shadow: 0 4px 12px rgba(245, 34, 45, 0.3);
  transform: translateY(-0.5px);
}
.ni-btn-stop:active:not(:disabled) {
  transform: translateY(0);
}
.ni-btn-stop:disabled {
  background: #f5f5f5 !important;
  color: rgba(0, 0, 0, 0.25) !important;
  border: 1px solid #d9d9d9 !important;
  box-shadow: none;
}

/* 双开关同行 */
.config-row-dual {
  flex-shrink: 0;
  justify-content: space-between;
  gap: 8px;
}
.config-switch-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.config-switch-item label {
  font-size: 13px;
  color: #4e5969;
  white-space: nowrap;
  min-width: 56px;
}
</style>
