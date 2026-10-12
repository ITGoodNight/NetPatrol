<template>
  <a-modal
    v-model:open="visible"
    title="巡检报告"
    width="90vw"
    :style="{ top: '20px' }"
    :footer="null"
    destroy-on-close
  >
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-size:13px;color:#4e5969">{{ filename }}</span>
      <a :href="downloadUrl" :download="filename">
        <a-button size="small" type="primary">
          <DownloadOutlined /> 下载
        </a-button>
      </a>
    </div>
    <iframe
      v-if="isHtml"
      :src="previewUrl"
      style="width:100%;height:72vh;border:1px solid #e5e6eb;border-radius:6px"
    />
    <a-textarea
      v-else
      :value="txtContent"
      :rows="30"
      readonly
      :style="{ fontFamily: 'Consolas, monospace', fontSize: '12px' }"
    />
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { inspectionApi } from '@/api/index.js'

const props = defineProps({
  filename: { type: String, default: '' },
})
const visible = defineModel('open', { type: Boolean, default: false })

const txtContent = ref('')
const isHtml = computed(() => props.filename.endsWith('.html'))
const previewUrl = computed(() =>
  props.filename ? inspectionApi.getResultUrl(props.filename) : ''
)
const downloadUrl = computed(() =>
  props.filename ? `${inspectionApi.getResultUrl(props.filename)}?download=1` : ''
)

watch([visible, () => props.filename], async ([v, fn]) => {
  if (v && fn && !isHtml.value) {
    try {
      const res = await fetch(inspectionApi.getResultUrl(fn))
      txtContent.value = await res.text()
    } catch {
      txtContent.value = '加载失败'
    }
  }
})
</script>
