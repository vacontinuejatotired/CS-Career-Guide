<template>
  <div class="app-shell min-h-screen bg-base-200">
    <Navbar />
    <div class="app-content w-full">
      <router-view />
    </div>
    <Footer />
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue' // 根组件
import Footer from './components/Footer.vue'
</script>
