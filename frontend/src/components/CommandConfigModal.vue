<template>
  <a-modal
    v-model:open="visible"
    title="巡检命令配置"
    width="720px"
    :footer="null"
    @cancel="visible = false"
  >
    <div style="margin-bottom:8px;font-size:12px;color:#86909c">
      格式：<code style="background:#f2f3f5;padding:2px 6px;border-radius:4px">[设备类型]</code>
      后跟命令列表，支持华为/h3c/cisco/ruijie/zte/default
    </div>
    <a-textarea
      v-model:value="content"
      :rows="22"
      :style="{ fontFamily: 'Consolas, monospace', fontSize: '13px' }"
      placeholder="[huawei]&#10;display version&#10;display ip interface brief&#10;&#10;[default]&#10;show version"
    />
    <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px">
      <a-button @click="visible = false">取消</a-button>
      <a-button type="primary" :loading="saving" @click="handleSave">保存</a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { configApi } from '@/api/index.js'

const visible = defineModel('open', { type: Boolean, default: false })
const content = ref('')
const saving = ref(false)

watch(visible, async (v) => {
  if (v) {
    try {
      const res = await configApi.getCommands()
      content.value = res.content
    } catch (e) {
      message.error('加载配置失败: ' + e.message)
    }
  }
})

async function handleSave() {
  saving.value = true
  try {
    await configApi.saveCommands(content.value)
    message.success('命令配置已保存')
    visible.value = false
  } catch (e) {
    message.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>
