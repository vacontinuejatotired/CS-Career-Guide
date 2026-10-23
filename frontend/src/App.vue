<template>
  <div class="app-shell min-h-screen bg-base-200">
    <Navbar />
    <div class="app-content w-full">
      <router-view />
    </div>
    <Footer />
    <AIFloat v-if="showAI" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getToken, isPublicPath } from './auth/session.js'
import Navbar from './components/Navbar.vue' // 根组件
import Footer from './components/Footer.vue'
import AIFloat from './components/AIFloat.vue'

const route = useRoute()
const showAI = computed(() => route.matched.length > 0 && !isPublicPath(route.path) && !!getToken())
</script>
