<template>
  <div class="career-auth-page">
    <div class="career-auth-layout">
      <aside class="career-auth-intro"><p class="career-eyebrow">CS CAREER GUIDE</p><h1>把走过的路，<br /><span>变成下一次的起点</span></h1><p>整理自己的背景与经历，找到适合的方向。每一次准备，都从一件具体的小事开始。</p><div class="career-auth-roadmap"><p>你的职业准备路径</p><div><i></i><span>了解方向<small>比较就业、深造与其他选择</small></span></div><div><i></i><span>整理经历<small>把课程、项目与实践写进简历</small></span></div><div><i></i><span>练习表达<small>通过模拟面试，讲清自己的思路</small></span></div></div><p class="career-auth-note">从自己的真实经历开始，一步步把准备做扎实。</p></aside>
      <section class="career-auth-card" aria-labelledby="auth-title">
        <p class="career-eyebrow">欢迎回来</p><h2 id="auth-title">继续你的准备</h2><p class="career-auth-description">使用用户名和密码登录，继续查看简历与职业规划。</p>
        <form @submit.prevent="login">
          <div class="career-auth-field"><label for="auth-username">用户名</label><input id="auth-username" v-model="form.username" type="text" autocomplete="username" placeholder="请输入用户名" required /></div>
          <div class="career-auth-field"><label for="auth-password">密码</label><input id="auth-password" v-model="form.password" type="password" autocomplete="current-password" placeholder="请输入密码" required /></div>

          <div v-if="error" class="career-auth-error" role="alert">{{ error }}</div>
          <button type="submit" class="career-button career-button-primary career-auth-submit" :disabled="loading"><span v-if="loading" class="loading loading-spinner loading-xs"></span>{{ loading ? '登录中…' : '登录' }}</button>
          <p class="career-auth-switch">还没有账号？<router-link :to="{ path: '/register', query: { redirect: safeRedirect(route.query.redirect) } }" class="career-link">创建账号</router-link></p>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '@/api'
import { clearSession, safeRedirect } from '@/auth/session.js'

const router = useRouter()
const route = useRoute()
const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

const login = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await authAPI.login(form.value)
    clearSession()
    // 设置新用户信息
    localStorage.setItem('token', response.token)
    localStorage.setItem('user', JSON.stringify(response.user))
    const redirect = safeRedirect(route.query.redirect)
    await router.replace(router.resolve(redirect).matched.length ? redirect : '/')
  } catch (err) {
    if (err.response) {
      error.value = err.response.data?.non_field_errors?.[0] || '登录失败，请检查用户名和密码'
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
