<template>
  <div class="ni-card device-panel">
    <div class="section-header">
      <div class="section-icon">
        <DatabaseOutlined />
        <span>设备列表</span>
        <a-tag v-if="localDevices.length" color="blue" style="margin-left:4px">
          {{ localDevices.length }} 台
        </a-tag>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <a-button type="primary" size="small" @click="openAddDialog()">
          <PlusOutlined /> 添加设备
        </a-button>
        <a-button type="primary" size="small" danger class="ni-btn-clear" @click="handleClearAll" v-if="localDevices.length">
          <DeleteOutlined /> 清空
        </a-button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!localDevices.length" class="empty-state">
      <div class="empty-icon">
        <ApiOutlined />
      </div>
      <p class="empty-title">暂无设备</p>
      <p class="empty-hint">点击右上角「添加设备」填写设备信息</p>
    </div>

    <!-- 设备表格 -->
    <div v-else class="device-table-wrap">
      <a-table
        class="ni-table device-table"
        :data-source="localDevices"
        :columns="columns"
        :pagination="false"
        size="small"
        row-key="__id"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === '连接类型'">
            <span :class="['ni-badge', protocolBadgeClass(record['连接类型'])]">
              {{ record['连接类型']?.toUpperCase() }}
            </span>
          </template>
          <template v-else-if="column.key === '设备类型'">
            <span :class="['ni-badge', typeBadgeClass(record['设备类型'])]">
              {{ record['设备类型'] }}
            </span>
          </template>
          <template v-else-if="column.key === '密码'">
            <div class="password-cell">
              <span class="password-text">{{ displayPassword(record) }}</span>
              <button
                v-if="record['密码']"
                type="button"
                class="password-eye-btn"
                :title="isPasswordVisible(record.__id) ? '隐藏密码' : '显示密码'"
                @click.stop="togglePasswordVisible(record.__id)"
              >
                <EyeInvisibleOutlined v-if="isPasswordVisible(record.__id)" />
                <EyeOutlined v-else />
              </button>
            </div>
          </template>
          <template v-else-if="column.key === 'action'">
            <div style="display:flex;gap:6px">
              <a-button type="link" size="small" style="padding:0;color:#1677ff" @click="openAddDialog(record, index)">
                编辑
              </a-button>
              <a-button type="link" size="small" danger style="padding:0" @click="removeDevice(index)">
                删除
              </a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- ══ 添加/编辑设备弹窗 ═══════════════════════════════════════════════ -->
    <a-modal
      v-model:open="showEditModal"
      :title="editIndex === -1 ? '添加设备' : '编辑设备'"
      :width="540"
      :mask-closable="false"
      @cancel="resetForm"
    >
      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        layout="vertical"
        style="margin-top:8px"
      >
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px">
          <a-form-item label="设备名称" name="设备名称">
            <a-input v-model:value="form['设备名称']" placeholder="如：Core-SW-01" />
          </a-form-item>
          <a-form-item label="设备类型" name="设备类型">
            <a-select v-model:value="form['设备类型']" placeholder="选择厂商">
              <a-select-option value="huawei">华为 (Huawei)</a-select-option>
              <a-select-option value="h3c">华三 (H3C)</a-select-option>
              <a-select-option value="cisco">思科 (Cisco)</a-select-option>
              <a-select-option value="ruijie">锐捷 (Ruijie)</a-select-option>
              <a-select-option value="zte">中兴 (ZTE)</a-select-option>
              <a-select-option value="other">其他 (Other)</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item
            v-if="form['设备类型'] === 'other'"
            label="自定义类型/驱动"
            name="自定义类型"
            :rules="[{ required: true, message: '请输入自定义设备类型或 Netmiko 驱动名称' }]"
          >
            <a-input v-model:value="form['自定义类型']" placeholder="例如: generic, juniper_junos" />
          </a-form-item>
          <a-form-item label="IP 地址" name="IP地址">
            <a-input v-model:value="form['IP地址']" placeholder="192.168.1.1" />
          </a-form-item>
          <a-form-item label="端口" name="端口号">
            <a-input-number
              v-model:value="form['端口号']"
              :min="1" :max="65535"
              style="width:100%"
            />
          </a-form-item>
          <a-form-item label="连接协议" name="连接类型">
            <a-radio-group
              v-model:value="form['连接类型']"
              button-style="solid"
              class="ni-radio-segment"
              @change="onProtocolChange"
            >
              <a-radio-button value="ssh">SSH</a-radio-button>
              <a-radio-button value="telnet">Telnet</a-radio-button>
            </a-radio-group>
          </a-form-item>
          <a-form-item label="用户名" name="用户名">
            <a-input v-model:value="form['用户名']" placeholder="admin" />
          </a-form-item>
          <a-form-item label="登录密码" name="密码">
            <a-input-password v-model:value="form['密码']" placeholder="登录密码" />
          </a-form-item>
          <a-form-item label="提权密码" name="提权密码">
            <a-input-password
              v-model:value="form['提权密码']"
              placeholder="Enable 密码（可选）"
            />
          </a-form-item>
        </div>
      </a-form>

      <template #footer>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <a-button type="default" :loading="testing" @click="handleTestConnect">
            测试连接
          </a-button>
          <div style="display:flex;gap:8px">
            <a-button @click="resetForm">取消</a-button>
            <a-button type="primary" @click="handleSubmit">确认</a-button>
          </div>
        </div>
      </template>
    </a-modal>


  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  DatabaseOutlined, PlusOutlined, DeleteOutlined, ApiOutlined,
  EyeOutlined, EyeInvisibleOutlined,
} from '@ant-design/icons-vue'
import { deviceApi } from '@/api/index.js'

// ── props / emits ─────────────────────────────────────────────────────────────
const props = defineProps({
  devices: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:devices'])

// ── 本地设备列表（带内部 __id 唯一标识） ───────────────────────────────────────
let __idCounter = 0
const localDevices = computed({
  get: () => props.devices,
  set: (v) => emit('update:devices', v),
})

// ── 弹窗状态 ──────────────────────────────────────────────────────────────────
const showEditModal = ref(false)
const editIndex = ref(-1)
const formRef = ref(null)

// ── 表单数据 ──────────────────────────────────────────────────────────────────
const DEFAULT_FORM = () => ({
  '设备名称': '',
  '设备类型': 'huawei',
  'IP地址': '',
  '端口号': 22,
  '连接类型': 'ssh',
  '用户名': '',
  '密码': '',
  '提权密码': '',
  '自定义类型': '',
})
const form = reactive(DEFAULT_FORM())

const rules = {
  '设备名称': [{ required: true, message: '请输入设备名称' }],
  '设备类型': [{ required: true, message: '请选择设备类型' }],
  'IP地址': [
    { required: true, message: '请输入 IP 地址' },
    {
      pattern: /^(\d{1,3}\.){3}\d{1,3}$/,
      message: 'IP 格式不正确',
    },
  ],
  '用户名': [{ required: true, message: '请输入用户名' }],
}

// ── 表格列定义 ────────────────────────────────────────────────────────────────
const columns = [
  { title: '设备名称', dataIndex: '设备名称', key: '设备名称', width: 110, ellipsis: true },
  { title: '类型', dataIndex: '设备类型', key: '设备类型', width: 90, align: 'center' },
  { title: 'IP 地址', dataIndex: 'IP地址', key: 'IP地址', width: 130 },
  { title: '端口', dataIndex: '端口号', key: '端口号', width: 60, align: 'center' },
  { title: '协议', dataIndex: '连接类型', key: '连接类型', width: 80, align: 'center' },
  { title: '用户名', dataIndex: '用户名', key: '用户名', width: 90 },
  { title: '密码', dataIndex: '密码', key: '密码', width: 100 },
  { title: '操作', key: 'action', width: 90, align: 'center' },
]

// ── 辅助函数 ──────────────────────────────────────────────────────────────────
const TYPE_BADGE = {
  huawei: 'ni-badge-huawei',
  h3c: 'ni-badge-h3c',
  cisco: 'ni-badge-cisco',
  ruijie: 'ni-badge-ruijie',
  zte: 'ni-badge-zte',
}
function typeBadgeClass(t) {
  return TYPE_BADGE[t?.toLowerCase()] || 'ni-badge-default'
}
function protocolBadgeClass(p) {
  return p?.toLowerCase() === 'telnet' ? 'ni-badge-telnet' : 'ni-badge-ssh'
}
function maskStr(s) {
  if (!s) return '—'
  if (s.startsWith('*')) return s
  return '*'.repeat(Math.min(s.length, 8))
}

const visiblePasswordIds = ref(new Set())

function isPasswordVisible(id) {
  return visiblePasswordIds.value.has(id)
}

function togglePasswordVisible(id) {
  const next = new Set(visiblePasswordIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  visiblePasswordIds.value = next
}

function displayPassword(record) {
  const pwd = record['密码']
  if (!pwd) return '—'
  if (isPasswordVisible(record.__id)) return pwd
  return maskStr(pwd)
}

// ── 协议切换自动切默认端口 ────────────────────────────────────────────────────
function onProtocolChange() {
  form['端口号'] = form['连接类型'] === 'ssh' ? 22 : 23
}

// ── 打开添加/编辑弹窗 ─────────────────────────────────────────────────────────
function openAddDialog(record = null, idx = -1) {
  editIndex.value = idx
  if (record) {
    const knownTypes = ['huawei', 'h3c', 'cisco', 'ruijie', 'zte']
    const recType = record['设备类型']
    if (knownTypes.includes(recType?.toLowerCase())) {
      Object.assign(form, { ...DEFAULT_FORM(), ...record, '自定义类型': '' })
    } else {
      Object.assign(form, {
        ...DEFAULT_FORM(),
        ...record,
        '设备类型': 'other',
        '自定义类型': recType,
      })
    }
  } else {
    Object.assign(form, DEFAULT_FORM())
  }
  showEditModal.value = true
}

// ── 提交表单 ──────────────────────────────────────────────────────────────────
async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  const submitForm = { ...form }
  if (submitForm['设备类型'] === 'other') {
    submitForm['设备类型'] = (submitForm['自定义类型'] || 'generic').trim()
  }

  const entry = {
    ...submitForm,
    __id: editIndex.value >= 0 ? localDevices.value[editIndex.value].__id : (++__idCounter),
    _raw: { ...submitForm },
  }

  const list = [...localDevices.value]
  if (editIndex.value >= 0) {
    list[editIndex.value] = entry
    message.success('设备已更新')
  } else {
    list.push(entry)
    message.success('设备已添加')
  }
  emit('update:devices', list)
  resetForm()
}

function resetForm() {
  showEditModal.value = false
  editIndex.value = -1
  formRef.value?.resetFields()
  Object.assign(form, DEFAULT_FORM())
}

const testing = ref(false)

async function handleTestConnect() {
  try {
    const fieldsToValidate = ['IP地址', '用户名', '密码']
    if (form['设备类型'] === 'other') {
      fieldsToValidate.push('自定义类型')
    }
    await formRef.value.validateFields(fieldsToValidate)
  } catch (err) {
    message.warning('请填写完整的连接信息')
    return
  }

  testing.value = true
  try {
    const submitForm = { ...form }
    if (submitForm['设备类型'] === 'other') {
      submitForm['设备类型'] = (submitForm['自定义类型'] || 'generic').trim()
    }
    const res = await deviceApi.testConnect(submitForm)
    if (res.success) {
      message.success(res.message || '连接测试成功！')
    } else {
      message.error(res.message || '连接测试失败')
    }
  } catch (e) {
    message.error('测试出错: ' + e.message)
  } finally {
    testing.value = false
  }
}

// ── 删除单台 ──────────────────────────────────────────────────────────────────
function removeDevice(idx) {
  const list = [...localDevices.value]
  list.splice(idx, 1)
  emit('update:devices', list)
  message.success('已删除')
}

// ── 清空全部 ──────────────────────────────────────────────────────────────────
function handleClearAll() {
  Modal.confirm({
    title: '确认清空',
    content: `将删除全部 ${localDevices.value.length} 台设备，是否继续？`,
    okText: '清空',
    okButtonProps: { type: 'primary', class: 'ni-btn-confirm-danger' },
    cancelText: '取消',
    onOk() {
      emit('update:devices', [])
      message.success('已清空设备列表')
    },
  })
}


</script>

<style scoped>
.device-panel {
  height: 480px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.device-panel .section-header {
  padding: 8px 12px;
  flex-shrink: 0;
}
.device-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.device-table :deep(.ant-table) {
  margin: 0;
}
.device-table :deep(.ant-table-container),
.device-table :deep(.ant-table-content) {
  overflow: visible !important;
}
.device-table :deep(.ant-table-thead > tr > th) {
  padding: 6px 12px !important;
}
.device-table :deep(.ant-table-tbody > tr > td) {
  padding: 4px 12px !important;
}
.device-table :deep(.ant-table-measure-row) {
  display: none !important;
  height: 0 !important;
}
.device-table :deep(.ant-table-header),
.device-table :deep(.ant-table-body) {
  margin: 0 !important;
}

/* 类型 / 协议徽章 */
.ni-badge {
  display: inline-block;
  padding: 0 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  line-height: 22px;
  border: 1px solid transparent;
  white-space: nowrap;
}
.ni-badge-huawei { background: #fff1f0; color: #a8071a; border-color: #ffccc7; }
.ni-badge-h3c    { background: #fff7e6; color: #ad4e00; border-color: #ffd591; }
.ni-badge-cisco  { background: #e6f4ff; color: #0958d9; border-color: #91caff; }
.ni-badge-ruijie { background: #f6ffed; color: #237804; border-color: #b7eb8f; }
.ni-badge-zte    { background: #f9f0ff; color: #531dab; border-color: #d3adf7; }
.ni-badge-default { background: #f5f5f5; color: #434343; border-color: #d9d9d9; }
.ni-badge-ssh    { background: #1677ff; color: #fff; border-color: #1677ff; }
.ni-badge-telnet { background: #434343; color: #fff; border-color: #434343; }

.password-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
}
.password-text {
  color: #86909c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.password-eye-btn {
  border: none;
  background: transparent;
  color: #86909c;
  cursor: pointer;
  padding: 0 2px;
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  flex-shrink: 0;
  line-height: 1;
}
.password-eye-btn:hover {
  color: #1677ff;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 40px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%;
  background: #f2f3f5; display: flex; align-items: center;
  justify-content: center; margin-bottom: 12px;
  font-size: 24px; color: #c9cdd4;
}
.empty-title { font-size: 14px; font-weight: 600; color: #4e5969; margin: 0 0 4px; }
.empty-hint  { font-size: 12px; color: #86909c; margin: 0; }

.ni-btn-clear {
  background: #ff4d4f !important;
  border-color: #ff4d4f !important;
  color: #fff !important;
  box-shadow: 0 2px 6px rgba(255, 77, 79, 0.2);
}
.ni-btn-clear:hover {
  background: #ff7875 !important;
  border-color: #ff7875 !important;
  color: #fff !important;
}
</style>
