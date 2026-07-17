<template>
  <div class="main-topbar">
    <el-dropdown trigger="click" @command="$emit('command', $event)">
      <button class="operator avatar-button" type="button" aria-label="用户菜单">
        <span class="avatar">{{ displayName.slice(0, 1) }}</span>
        <span class="operator-copy"><strong>{{ displayName }}</strong></span>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="mine">个人中心</el-dropdown-item>
          <el-dropdown-item command="password">修改密码</el-dropdown-item>
          <el-dropdown-item command="manual">操作手册</el-dropdown-item>
          <el-dropdown-item command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
defineProps({ displayName: { type: String, required: true } });
defineEmits(["command"]);
</script>
