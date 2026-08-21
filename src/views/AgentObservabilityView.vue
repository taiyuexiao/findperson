<template>
  <section class="view active">
    <div class="page-heading admin-heading">
      <div><h1>Agent 可观测</h1></div>
      <div class="history-actions">
        <el-input v-model="keyword" placeholder="搜索问题 / 用户" clearable class="obs-search" @keyup.enter="!$event.isComposing && $event.keyCode !== 229 && load()" @clear="load" />
        <el-button class="secondary-button small-button" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="admin-table-wrap">
      <el-table :data="items" stripe v-loading="loading" @row-click="openDetail">
        <el-table-column prop="createdAt" label="时间" width="160" />
        <el-table-column prop="user" label="用户" width="100" />
        <el-table-column prop="query" label="用户问题" min-width="220" show-overflow-tooltip />
        <el-table-column label="意图" width="150">
          <template #default="{ row }">
            <span class="tag">{{ row.intent || '-' }}</span>
            <span v-if="row.queryType" class="tag">{{ row.queryType }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="90">
          <template #default="{ row }">{{ (row.latencyMs / 1000).toFixed(1) }}s</template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <span class="status-chip" :class="row.degraded ? 'status-pending' : 'status-published'">{{ row.degraded ? '降级' : '正常' }}</span>
            <span v-if="row.gateDecision" class="tag">{{ row.gateDecision }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page" :total="total" :page-size="20"
        layout="total, prev, pager, next" class="obs-pagination" @current-change="load" />
    </div>

    <el-drawer v-model="showDetail" size="720px" :title="detail?.trace?.query || '链路详情'">
      <div v-if="detail" class="obs-detail">
        <section class="obs-section">
          <h3>概览</h3>
          <p class="person-meta">
            {{ detail.trace.createdAt }} · {{ detail.trace.user }} · 耗时 {{ (detail.trace.latencyMs / 1000).toFixed(2) }}s
            · <span :class="detail.trace.degraded ? 'status-chip status-pending' : 'status-chip status-published'">{{ detail.trace.degraded ? '降级' : '正常' }}</span>
            <template v-if="detail.recommendation"> · 门禁 {{ detail.recommendation.gateDecision }} · 策略 {{ detail.recommendation.rankPolicy }}</template>
          </p>
          <p class="person-meta">trace: {{ detail.trace.traceId }}</p>
        </section>

        <section class="obs-section">
          <h3>节点链路({{ detail.spans.length }})</h3>
          <div v-for="s in detail.spans" :key="s.node" class="obs-node">
            <div class="obs-node-head">
              <strong>{{ s.node }}</strong>
              <span class="person-meta">{{ s.latencyMs }}ms</span>
              <span v-if="s.degraded" class="status-chip status-pending">降级</span>
              <span v-if="s.errorCode" class="status-chip status-rejected">{{ s.errorCode }}</span>
            </div>
            <div class="obs-node-bar"><div class="obs-node-bar-fill" :style="{ width: latencyPercent(s.latencyMs) + '%' }"></div></div>
            <p v-if="s.output" class="obs-node-io">输出:{{ s.output }}</p>
          </div>
        </section>

        <section v-if="detail.conceptLink" class="obs-section">
          <h3>概念链接</h3>
          <div v-for="t in detail.conceptLink.linkTrace" :key="t.term" class="obs-node">
            <p><strong>词条「{{ t.term }}」</strong></p>
            <p v-for="c in t.candidates.slice(0, 5)" :key="c.concept_id + c.candidate_source" class="person-meta">
              → {{ c.canonical_name }}({{ c.candidate_source }} {{ c.candidate_score }})
            </p>
            <p v-if="!t.candidates.length" class="person-meta">→ 无候选</p>
          </div>
          <p v-if="detail.conceptLink.resolvedConcepts?.length" class="person-meta">
            已确认概念:{{ detail.conceptLink.resolvedConcepts.map((c) => c.canonical_name).join('、') }}
          </p>
        </section>

        <section v-if="detail.mcpCalls.length" class="obs-section">
          <h3>MCP 调用({{ detail.mcpCalls.length }})</h3>
          <p v-for="(m, i) in detail.mcpCalls" :key="i" class="person-meta">
            {{ m.tool }} · {{ m.ok ? '成功' : '失败' }} · {{ m.latencyMs }}ms
          </p>
        </section>

        <section v-if="detail.recommendation?.candidates?.length" class="obs-section">
          <h3>推荐候选({{ detail.recommendation.candidates.length }})</h3>
          <div v-for="c in detail.recommendation.candidates" :key="c.person_id" class="obs-node">
            <strong>{{ c.person_id }}</strong>
            <span class="person-meta"> score={{ c.score }}</span>
            <span v-if="c.has_formal" class="tag">正式责任</span>
            <p class="person-meta">{{ (c.evidences || []).map((e) => `${e.evidence_type}@${e.concept_id || e.source_id || ''}`).join(' / ') }}</p>
          </div>
        </section>

        <section class="obs-section">
          <h3>对话内容</h3>
          <div v-for="(m, i) in detail.messages" :key="i" class="obs-message" :class="`obs-${m.role}`">
            <strong>{{ m.role === 'user' ? '用户' : '助手' }}</strong>
            <p>{{ m.text }}</p>
            <p v-if="m.cards?.length" class="person-meta">卡片 {{ m.cards.length }} 张</p>
          </div>
        </section>

        <section v-if="detail.feedbacks.length" class="obs-section">
          <h3>反馈({{ detail.feedbacks.length }})</h3>
          <p v-for="(f, i) in detail.feedbacks" :key="i" class="person-meta">
            {{ f.value }} {{ f.reason ? `· ${f.reason}` : '' }}
          </p>
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchAgentTraceDetail, fetchAgentTraces } from "../services/api/admin.js";

const items = ref([]);
const total = ref(0);
const page = ref(1);
const keyword = ref("");
const loading = ref(false);
const showDetail = ref(false);
const detail = ref(null);
const maxLatency = ref(1);

async function load() {
  loading.value = true;
  try {
    const data = await fetchAgentTraces({ page: page.value, page_size: 20, keyword: keyword.value || undefined });
    items.value = data.items || [];
    total.value = data.total || 0;
  } finally {
    loading.value = false;
  }
}

async function openDetail(row) {
  detail.value = await fetchAgentTraceDetail(row.traceId);
  maxLatency.value = Math.max(...detail.value.spans.map((s) => s.latencyMs), 1);
  showDetail.value = true;
}

function latencyPercent(ms) {
  return Math.max(2, Math.round((ms / maxLatency.value) * 100));
}

onMounted(load);
</script>

<style scoped>
.obs-search { width: 240px; }
.obs-pagination { margin-top: 12px; justify-content: flex-end; }
.obs-section { margin-bottom: 18px; }
.obs-section h3 { font-size: 14px; margin: 0 0 8px; }
.obs-node { padding: 6px 0; border-bottom: 1px dashed #eef2f7; }
.obs-node-head { display: flex; align-items: center; gap: 10px; }
.obs-node-bar { height: 6px; background: #eef2f7; border-radius: 4px; margin-top: 4px; overflow: hidden; }
.obs-node-bar-fill { height: 100%; background: #4a7dff; border-radius: 4px; }
.obs-node-io { font-size: 12px; color: #64748b; margin: 4px 0 0; word-break: break-all; }
.obs-message { padding: 8px 10px; border-radius: 8px; margin-bottom: 8px; background: #f6f8fb; }
.obs-message p { margin: 4px 0 0; white-space: pre-wrap; }
.obs-user { background: #eaf1ff; }
</style>
