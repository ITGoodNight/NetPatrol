let audioCtx = null

function getAudioContext() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext
    if (!Ctx) return null
    audioCtx = new Ctx()
  }
  return audioCtx
}

function playTone(ctx, frequency, start, duration, volume = 0.12) {
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = 'sine'
  osc.frequency.value = frequency
  gain.gain.setValueAtTime(0, start)
  gain.gain.linearRampToValueAtTime(volume, start + 0.015)
  gain.gain.exponentialRampToValueAtTime(0.001, start + duration)
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(start)
  osc.stop(start + duration + 0.05)
}

/**
 * 巡检完成提示音（全部成功 / 含失败两种旋律）
 */
export async function playCompletionSound({ failed = 0 } = {}) {
  try {
    const ctx = getAudioContext()
    if (!ctx) return
    if (ctx.state === 'suspended') {
      await ctx.resume()
    }

    const now = ctx.currentTime
    if (failed > 0) {
      playTone(ctx, 440, now, 0.22, 0.1)
      playTone(ctx, 349.23, now + 0.18, 0.28, 0.1)
    } else {
      playTone(ctx, 523.25, now, 0.14)
      playTone(ctx, 659.25, now + 0.11, 0.18)
      playTone(ctx, 783.99, now + 0.22, 0.26)
    }
  } catch (e) {
    console.warn('播放完成提示音失败:', e)
  }
}

/** 开关切换时试听 */
export function playPreviewSound() {
  return playCompletionSound({ failed: 0 })
}
