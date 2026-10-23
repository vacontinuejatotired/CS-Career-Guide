<template>
  <div class="career-auth-page">
    <div class="career-auth-layout">
      <aside class="career-auth-intro"><p class="career-eyebrow">CS CAREER GUIDE</p><h1>把走过的路，<br /><span>变成下一次的起点</span></h1><p>整理自己的背景与经历，找到适合的方向。每一次准备，都从一件具体的小事开始。</p><div class="career-auth-roadmap"><p>你的职业准备路径</p><div><i></i><span>了解方向<small>比较就业、深造与其他选择</small></span></div><div><i></i><span>整理经历<small>把课程、项目与实践写进简历</small></span></div><div><i></i><span>练习表达<small>通过模拟面试，讲清自己的思路</small></span></div></div><p class="career-auth-note">从自己的真实经历开始，一步步把准备做扎实。</p></aside>
      <section class="career-auth-card" aria-labelledby="auth-title">
        <p class="career-eyebrow">开启你的准备</p><h2 id="auth-title">创建你的账号</h2><p class="career-auth-description">填写账号信息，开始整理你的职业计划。</p>
        <form @submit.prevent="register">
          <div class="career-auth-field"><label for="auth-username">用户名</label><input id="auth-username" v-model="form.username" type="text" autocomplete="username" placeholder="请输入用户名" required /></div>
          <div class="career-auth-field"><label for="auth-password">密码</label><input id="auth-password" v-model="form.password" type="password" autocomplete="new-password" placeholder="设置你的登录密码" required /></div>
          <div class="career-auth-field"><label for="auth-confirm-password">确认密码</label><input id="auth-confirm-password" v-model="form.confirm_password" type="password" autocomplete="new-password" placeholder="再次输入密码" required /></div>
          <div v-if="error" class="career-auth-error" role="alert">{{ error }}</div>
          <button type="submit" class="career-button career-button-primary career-auth-submit" :disabled="loading"><span v-if="loading" class="loading loading-spinner loading-xs"></span>{{ loading ? '创建中…' : '创建账号' }}</button>
          <p class="career-auth-switch">已有账号？<router-link :to="{ path: '/login', query: { redirect: safeRedirect(route.query.redirect) } }" class="career-link">立即登录</router-link></p>
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
  password: '',
  confirm_password: ''
})
const loading = ref(false)
const error = ref('')

const register = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await authAPI.register(form.value)
    clearSession()
    // 设置新用户信息
    localStorage.setItem('token', response.token)
    localStorage.setItem('user', JSON.stringify(response.user))
    const redirect = safeRedirect(route.query.redirect)
    await router.replace(router.resolve(redirect).matched.length ? redirect : '/')
  } catch (err) {
    if (err.response) {
      if (err.response.data?.username) {
        error.value = err.response.data.username[0]
      } else if (err.response.data?.password) {
        error.value = err.response.data.password[0]
      } else if (err.response.data?.non_field_errors) {
        error.value = err.response.data.non_field_errors[0]
      } else {
        error.value = '注册失败，请稍后重试'
      }
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
