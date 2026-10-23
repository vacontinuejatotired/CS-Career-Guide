<template>
  <header class="business-heading">
    <div><p v-if="eyebrow" class="career-eyebrow">{{ eyebrow }}</p><h1>{{ title }}</h1><p v-if="description" class="business-description">{{ description }}</p></div>
    <div v-if="$slots.default" class="business-heading-actions"><slot /></div>
  </header>
</template>
<script setup>
defineProps({ title: { type: String, required: true }, eyebrow: String, description: String })
</script>
