import { watchEffect, onBeforeUnmount } from 'vue'

export const DEFAULT_PAGE_TITLE = 'NetPatrol · 网络设备巡检系统'

/**
 * 根据巡检状态动态更新浏览器标签页标题
 */
export function usePageTitle({ running, progress, deviceCount, enableSchedule, runSummary }) {
  watchEffect(() => {
    let title = DEFAULT_PAGE_TITLE

    if (running.value && progress.value.total > 0) {
      const { completed, total } = progress.value
      const pct = Math.round((completed / total) * 100)
      title = `巡检中 ${completed}/${total} (${pct}%) · NetPatrol`
    } else if (runSummary?.value) {
      title = `${runSummary.value} · NetPatrol`
    } else if (deviceCount.value > 0) {
      const scheduleTag = enableSchedule?.value ? ' · 定时已开' : ''
      title = `NetPatrol · ${deviceCount.value} 台设备${scheduleTag}`
    }

    document.title = title
  })

  onBeforeUnmount(() => {
    document.title = DEFAULT_PAGE_TITLE
  })
}
