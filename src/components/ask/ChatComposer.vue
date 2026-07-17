<template>
  <div class="chat-composer-wrap">
    <div class="ask-composer chat-composer" role="search">
      <div class="composer-input-row">
        <el-input
          :model-value="modelValue"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 5 }"
          placeholder="例如：我想申请大模型 Key，应该找谁？"
          @update:model-value="$emit('update:modelValue', $event)"
          @keydown.enter.exact.prevent="$emit('send')"
        />
        <el-button class="primary-button composer-send-button" type="primary" :disabled="disabled" @click="$emit('send')">
          <el-icon><Right /></el-icon>
          发送
        </el-button>
      </div>
      <div class="composer-actions">
        <span class="composer-helper">支持问题找人、信息维护、内容发布、评价补充</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Right } from "@element-plus/icons-vue";

defineProps({
  modelValue: { type: String, default: "" },
  disabled: Boolean,
});
defineEmits(["update:modelValue", "send"]);
</script>
