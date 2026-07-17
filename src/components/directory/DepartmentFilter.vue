<template>
  <div class="toolbar-filters triple-filter">
    <el-select :model-value="filters.level1" aria-label="按一级部门筛选" @update:model-value="update('level1', $event)">
      <el-option v-for="item in level1Options" :key="item" :label="item" :value="item" />
    </el-select>
    <el-select :model-value="filters.level2" aria-label="按二级部门筛选" @update:model-value="update('level2', $event)">
      <el-option v-for="item in level2Options" :key="item" :label="item" :value="item" />
    </el-select>
    <el-select :model-value="filters.level3" aria-label="按三级部门筛选" @update:model-value="update('level3', $event)">
      <el-option v-for="item in level3Options" :key="item" :label="item" :value="item" />
    </el-select>
  </div>
</template>

<script setup>
const props = defineProps({
  filters: { type: Object, required: true },
  level1Options: { type: Array, required: true },
  level2Options: { type: Array, required: true },
  level3Options: { type: Array, required: true },
});
const emit = defineEmits(["change"]);

function update(key, value) {
  props.filters[key] = value;
  emit("change", key);
}
</script>
