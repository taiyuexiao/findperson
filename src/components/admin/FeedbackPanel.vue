<template>
  <div class="feedback-panel">
    <div class="admin-grid">
      <MetricCard label="反馈总数" :value="summary.total" primary />
      <MetricCard label="有帮助率" :value="`${summary.helpfulRate}%`" />
      <MetricCard label="有帮助" :value="summary.up" />
      <MetricCard label="没帮助" :value="summary.down" />
    </div>

    <div class="admin-layout">
      <div>
        <div class="module-title"><div><h2>近 7 天反馈趋势</h2></div></div>
        <ActivityTrend :items="trendItems" :total="trendTotal" />
      </div>
      <div>
        <div class="module-title"><div><h2>没帮助原因分布</h2></div></div>
        <div class="activity-panel reason-panel">
          <div v-if="summary.reasons?.length" class="reason-list">
            <div v-for="item in summary.reasons" :key="item.reason" class="reason-row">
              <span class="reason-label">{{ item.reason }}</span>
              <div class="reason-bar-wrap">
                <div class="reason-bar" :style="{ width: reasonPercent(item.count) + '%' }"></div>
              </div>
              <span class="reason-count">{{ item.count }}</span>
            </div>
          </div>
          <div v-else class="empty-state compact">暂无没帮助反馈</div>
        </div>
      </div>
    </div>

    <div class="module-title"><div><h2>反馈明细</h2></div></div>
    <div class="admin-table-wrap">
      <el-table :data="recent" stripe>
        <el-table-column prop="createdAt" label="时间" width="170" />
        <el-table-column prop="user" label="用户" width="100" />
        <el-table-column prop="question" label="用户问题" min-width="200" show-overflow-tooltip />
        <el-table-column label="推荐人选" min-width="180">
          <template #default="{ row }">{{ candidateText(row.candidates) }}</template>
        </el-table-column>
        <el-table-column label="反馈" width="90">
          <template #default="{ row }">
            <span class="status-chip" :class="row.value === 'up' ? 'status-published' : 'status-rejected'">
              {{ row.value === 'up' ? '有帮助' : '没帮助' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="140" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { fetchFeedbackRecent, fetchFeedbackSummary } from "../../services/api/admin.js";
import { useDirectoryStore } from "../../stores/directory.js";
import ActivityTrend from "./ActivityTrend.vue";
import MetricCard from "./MetricCard.vue";

const directory = useDirectoryStore();
const summary = ref({ total: 0, up: 0, down: 0, helpfulRate: 0, trend: [], reasons: [] });
const recent = ref([]);

const trendItems = computed(() => {
  const items = summary.value.trend.map((d) => ({ day: d.day, value: d.up + d.down, percent: 0 }));
  const max = Math.max(...items.map((i) => i.value), 1);
  items.forEach((i) => { i.percent = Math.round(i.value / max * 100); });
  return items;
});
const trendTotal = computed(() => trendItems.value.reduce((total, item) => total + item.value, 0));

function reasonPercent(count) {
  const max = Math.max(...(summary.value.reasons || []).map((r) => r.count), 1);
  return Math.round(count / max * 100);
}

function candidateText(candidates) {
  if (!candidates?.length) return "-";
  return candidates.map((c) => directory.getPerson(c)?.name || c).join("、");
}

onMounted(async () => {
  const [s, r] = await Promise.all([fetchFeedbackSummary(), fetchFeedbackRecent({ limit: 100 })]);
  summary.value = s;
  recent.value = r;
});
</script>

<style scoped>
/* 没帮助原因分布与近 7 天反馈趋势保持一致的外框，蓝色条形 */
.reason-panel {
  min-height: 340px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.reason-list { display: grid; gap: 12px; }
.reason-row { display: flex; align-items: center; gap: 10px; }
.reason-label { flex: 0 0 180px; font-size: 13px; color: #334155; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reason-bar-wrap { flex: 1; height: 10px; background: #eef2f7; border-radius: 6px; overflow: hidden; }
.reason-bar { height: 100%; background: linear-gradient(90deg, #cfe0fb 0%, #1e63d6 100%); border-radius: 6px; }
.reason-count { flex: 0 0 32px; text-align: right; font-weight: 700; font-size: 13px; }

/* 反馈明细与上一个板块留出与其他板块一致的间隙 */
.feedback-panel > .module-title { margin-top: var(--frame-gap); }
</style>
