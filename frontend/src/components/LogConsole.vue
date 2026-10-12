<template>
  <div class="log-console" ref="consoleEl">
    <div
      v-for="(log, i) in logs"
      :key="i"
      class="log-line"
    >
      <span class="log-time">{{ log.time }}</span>
      <span :class="['log-level', log.level]">[{{ log.level }}]</span>
      <span class="log-msg">{{ log.message }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  autoScroll: { type: Boolean, default: true },
})

const consoleEl = ref(null)

watch(
  () => props.logs.length,
  async () => {
    if (props.autoScroll) {
      await nextTick()
      if (consoleEl.value) {
        consoleEl.value.scrollTop = consoleEl.value.scrollHeight
      }
    }
  }
)
</script>

<style scoped>
.log-console {
  background: #0d1117;
  color: #c9d1d9;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12px;
  line-height: 1.4;
  border-radius: 6px;
  overflow-y: auto;
  padding: 12px 16px;
  height: 100%;
  min-height: 200px;
}
.log-line {
  padding: 1px 0;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-time { color: #8b949e; margin-right: 10px; }
.log-level { font-weight: 600; margin-right: 10px; }
.log-level.INFO    { color: #58a6ff; }
.log-level.DEBUG   { color: #8b949e; }
.log-level.WARNING { color: #d29922; }
.log-level.ERROR   { color: #f85149; }
.log-level.SUCCESS { color: #3fb950; }
.log-msg { color: #e6edf3; word-break: break-all; white-space: pre-wrap; }
</style>
