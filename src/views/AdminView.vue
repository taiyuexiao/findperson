<template>
  <section class="view active">
    <div class="page-heading admin-heading"><div><h1>后台管理</h1></div></div>
    <div class="admin-grid">
      <MetricCard label="参与人员数量" :value="admin.metrics.peopleCount" primary />
      <MetricCard label="发布内容数量" :value="admin.metrics.contentCount" />
      <MetricCard label="覆盖领域数" :value="admin.metrics.domainCount" />
      <MetricCard label="本周推荐量" :value="admin.metrics.weeklyRecommendationTotal" />
    </div>
    <div class="admin-layout">
      <div>
        <div class="module-title"><div><h2>本周推荐热度排行</h2></div></div>
        <RankingList :items="admin.ranking" />
      </div>
      <div>
        <div class="module-title">
          <div><h2>周日活数</h2></div>
          <div class="week-switcher">
            <button v-if="admin.activeWeek === 0" class="week-arrow" type="button" @click="admin.activeWeek = 1">‹</button>
            <span class="week-label">{{ admin.activeWeek ? '上周' : '本周' }}</span>
            <button v-if="admin.activeWeek === 1" class="week-arrow" type="button" @click="admin.activeWeek = 0">›</button>
          </div>
        </div>
        <ActivityTrend :items="admin.trend" :total="admin.trendTotal" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, watch } from "vue";
import { useAdminStore } from "../stores/admin.js";
import ActivityTrend from "../components/admin/ActivityTrend.vue";
import MetricCard from "../components/admin/MetricCard.vue";
import RankingList from "../components/admin/RankingList.vue";

const admin = useAdminStore();
onMounted(() => admin.loadAdminData());
watch(() => admin.activeWeek, () => admin.loadAdminData());
</script>
