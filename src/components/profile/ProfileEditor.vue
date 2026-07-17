<template>
  <el-form class="form-grid" :model="form" @submit.prevent>
    <label>姓名<el-input v-model="form.name" /></label>
    <label>科室部门<el-input v-model="form.department" /></label>
    <label>职级/岗位<el-input v-model="form.role" /></label>
    <label>联系方式<el-input v-model="form.contact" /></label>
    <label class="wide">负责领域<el-input v-model="form.domainsText" placeholder="用顿号或逗号分隔" /></label>
    <label class="wide">自画像<el-input v-model="form.selfPortrait" type="textarea" :rows="5" /></label>
    <div class="form-actions wide">
      <el-button class="secondary-button" @click="$emit('cancel')">取消编辑</el-button>
      <el-button class="primary-button" type="primary" @click="$emit('save')">保存主页</el-button>
      <span role="status">{{ status }}</span>
    </div>
  </el-form>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
  status: { type: String, default: "" },
});
defineEmits(["cancel", "save"]);
</script>
