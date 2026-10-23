<template>
  <div class="business-page advice-form-page"><main class="career-container">
    <BusinessPageHeader eyebrow="企业与职位 / 经验分享" title="写一条对后来的人有用的建议" description="从自己经历过的面试、实习或工作出发，尽量写清具体情境与适用范围。"><router-link to="/company-reviews" class="career-button">返回企业与职位</router-link></BusinessPageHeader>
    <div class="advice-form-layout"><form class="business-stack" @submit.prevent="handleSubmit">
      <section class="business-panel"><div class="business-panel-head"><h2>这条建议与什么经历有关</h2><span class="business-tag">基本信息</span></div><div class="business-form-grid">
        <div class="business-field"><label for="advice-company">企业名称 *</label><input id="advice-company" v-model="formData.company" type="text" required /></div><div class="business-field"><label for="advice-position">岗位名称 *</label><input id="advice-position" v-model="formData.position" type="text" required /></div>
        <div class="business-field"><label for="advice-name">分享者姓名 *</label><input id="advice-name" v-model="formData.senior_name" type="text" required /></div><div class="business-field"><label for="advice-year">毕业年份 *</label><input id="advice-year" v-model="formData.graduation_year" type="text" placeholder="例如：2023" required /></div>
        <div class="business-field full-width"><label for="advice-current">目前就职企业 <span>选填</span></label><input id="advice-current" v-model="formData.current_company" type="text" /></div>
      </div></section>
      <section class="business-panel"><div class="business-panel-head"><h2>具体经历与建议</h2></div><div class="business-field"><label for="advice-content">详细建议 *</label><textarea id="advice-content" v-model="formData.advice" rows="6" required placeholder="可以写准备过程、实际遇到的问题、企业或岗位的特点，以及你建议后来者如何准备。" /><small>避免泄露他人隐私或企业机密，把事实与个人感受分开说明。</small></div><div class="business-form-grid advice-additions"><div class="business-field"><label for="advice-salary">薪资信息 <span>选填</span></label><input id="advice-salary" v-model="formData.salary_info" type="text" placeholder="写明时间与薪资结构，或留空" /></div><div class="business-field advice-rating"><label for="advice-rating">个人评分 *</label><div><input id="advice-rating" v-model="formData.rating" type="number" min="1" max="5" step="0.5" required /><span>/ 5</span></div></div><div class="business-field full-width"><label for="advice-pros">认可的方面</label><input id="advice-pros" v-model="prosInput" type="text" placeholder="用逗号分隔，例如：导师反馈及时,项目实践充分" /></div><div class="business-field full-width"><label for="advice-cons">需要提前了解的方面</label><input id="advice-cons" v-model="consInput" type="text" placeholder="用逗号分隔，说明具体情况" /></div></div></section>
      <div v-if="success" class="business-notice" role="status"><strong>{{ successMessage }}</strong><p>审核通过后会显示在经验分享中。</p></div><div v-if="error" class="business-notice is-error" role="alert">{{ errorMessage }}</div>
      <div class="advice-submit"><p>请确认内容真实、具体，提交后需等待审核。</p><button type="submit" class="career-button career-button-primary" :disabled="isSubmitting">{{ isSubmitting ? '提交中…' : '提交建议 →' }}</button></div>
    </form><aside class="business-panel advice-writing-guide"><h2>什么样的建议更有帮助</h2><ol><li><strong>说明经历的时间与范围</strong><p>实习、校招与正式工作可能有不同体验。</p></li><li><strong>写具体发生过的事情</strong><p>准备了什么，遇到哪些问题，怎样解决。</p></li><li><strong>给出能执行的下一步</strong><p>让读者知道可以从哪里开始准备。</p></li></ol></aside></div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const formData = ref({
  company: '',
  position: '',
  senior_name: '',
  graduation_year: '',
  current_company: '',
  advice: '',
  salary_info: '',
  pros: [],
  cons: [],
  rating: 4.0
})

const prosInput = ref('')
const consInput = ref('')
const isSubmitting = ref(false)
const success = ref(false)
const successMessage = ref('')
const error = ref(false)
const errorMessage = ref('')

const handleSubmit = async () => {
  // 处理优缺点输入
  formData.value.pros = prosInput.value.split(',').map(item => item.trim()).filter(Boolean)
  formData.value.cons = consInput.value.split(',').map(item => item.trim()).filter(Boolean)

  isSubmitting.value = true
  success.value = false
  error.value = false

  try {
    const response = await api.post('/ai/senior-advice/', formData.value)
    if (!response.success) throw new Error(response.message || response.error || '提交失败，请重试')
    successMessage.value = response.message || '建议已提交，等待审核'
    success.value = true

    // 重置表单
    formData.value = {
      company: '',
      position: '',
      senior_name: '',
      graduation_year: '',
      current_company: '',
      advice: '',
      salary_info: '',
      pros: [],
      cons: [],
      rating: 4.0
    }
    prosInput.value = ''
    consInput.value = ''
  } catch (err) {
    success.value = false
    error.value = true
    errorMessage.value = err.response?.data?.error || err.response?.data?.message || err.message || '提交失败，请重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.advice-form-layout {
  display: grid;
  grid-template-columns: minmax(0,1fr) 280px;
  gap: 28px;
  max-width: 1100px;
}
.advice-form-layout form .business-panel {
  padding: 25px;
}
.advice-additions {
  margin-top: 24px;
}
.advice-rating > div {
  display: flex;
  align-items: center;
  gap: 12px;
}
.advice-rating input {
  width: 95px;
}
.advice-rating span {
  color: #8a97a8;
  font-size: 13px;
}
.advice-submit {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 3px 0;
}
.advice-submit p {
  color: #8a97a8;
  font-size: 12px;
  line-height: 1.8;
}
.advice-submit button {
  flex: none;
}
.advice-writing-guide {
  position: sticky;
  top: 88px;
  padding: 22px;
}
.advice-writing-guide h2 {
  font-size: 14px;
}
.advice-writing-guide ol {
  display: grid;
  gap: 23px;
  margin-top: 24px;
}
.advice-writing-guide strong {
  color: #586577;
  font-size: 13px;
  font-weight: 500;
}
.advice-writing-guide p {
  color: #8a97a8;
  font-size: 12px;
  margin-top: 7px;
  line-height: 1.9;
}
@media (max-width: 900px) {
  .advice-form-layout {
    grid-template-columns: 1fr;
  }
  .advice-writing-guide {
    position: static;
  }
}
</style>
