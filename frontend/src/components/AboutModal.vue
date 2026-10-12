<template>
  <a-modal
    v-model:open="visible"
    title="免责声明"
    width="500px"
    :footer="null"
    @cancel="visible = false"
  >
    <div class="disclaimer">
      <p>本项目仅供网络运维人员在<b>已获授权</b>的网络环境中使用。</p>
      <ul>
        <li>
          本工具会用你提供的凭据登录网络设备并执行命令（含读取运行配置）。
          请仅在你有权管理的设备上使用，并自行确认符合所属组织的安全与合规要求。
        </li>
        <li>
          设备密码默认以<b>明文</b>保存在浏览器 localStorage 与 config/config.json 中。
          请勿在共享或不受信任的环境中使用，也不要将含真实设备的配置文件或巡检报告提交到公开仓库。
        </li>
        <li>
          本软件按「现状」提供，不提供任何明示或暗示的担保。作者不对因使用本软件造成的
          网络中断、配置变更、数据丢失或其它任何损失承担责任。<b>在生产环境使用前请务必充分测试。</b>
        </li>
      </ul>
      <p class="license-note">本软件以 <b>MIT</b> 协议发布，完整条款见仓库中的 LICENSE 文件。</p>
    </div>
  </a-modal>
</template>

<script setup>
const visible = defineModel('open', { type: Boolean, default: false })
</script>

<style scoped>
.disclaimer {
  font-size: 12.5px;
  color: #4e5969;
  line-height: 1.75;
}
.disclaimer p {
  margin: 0 0 10px;
}
.disclaimer ul {
  margin: 0 0 12px;
  padding-left: 18px;
}
.disclaimer li {
  margin-bottom: 9px;
}
.disclaimer b {
  color: #1d2129;
}
.license-note {
  margin: 0;
  padding-top: 10px;
  border-top: 1px solid #e5e6eb;
  font-size: 12px;
  color: #86909c;
}
</style>
