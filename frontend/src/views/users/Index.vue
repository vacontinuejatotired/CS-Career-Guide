<template>
  <div class="business-page account-page"><main class="career-container">
    <BusinessPageHeader eyebrow="我的账号 / 个人中心" title="从上次准备的地方继续" description="查看已有的个人背景、简历与面试复盘，把下一步准备落到一件具体的事上。"><button type="button" class="career-button" @click="openEditModal">编辑资料</button><router-link to="/resume" class="career-button career-button-primary">继续整理简历 →</router-link></BusinessPageHeader>
    <p v-if="message" class="business-notice account-message" :class="{ 'is-error': messageType === 'error' }" role="status">{{ message }}</p>
    <div class="account-layout">
      <aside class="business-panel account-profile">
        <div class="account-avatar"><img v-if="avatarPreview || user?.avatar" :src="avatarPreview || user.avatar" alt="个人头像" /><span v-else>{{ (user?.username || '我').slice(0,1) }}</span></div>
        <h2>{{ user?.username || '我的账号' }}</h2><p>{{ user?.profile || '还没有填写个人介绍' }}</p>
        <button type="button" class="career-link account-upload" :disabled="uploadingAvatar" @click="triggerAvatarUpload">{{ uploadingAvatar ? '上传中…' : '更换头像' }}</button><input ref="avatarInput" type="file" accept="image/*" hidden @change="handleAvatarChange" />
        <dl><div><dt>学校</dt><dd>{{ user?.school || '尚未填写' }}</dd></div><div><dt>专业</dt><dd>{{ user?.major || '尚未填写' }}</dd></div><div><dt>学历</dt><dd>{{ user?.education || '尚未填写' }}</dd></div><div><dt>邮箱</dt><dd>{{ user?.email || '尚未填写' }}</dd></div><div><dt>地区</dt><dd>{{ user?.address || '尚未填写' }}</dd></div></dl>
        <router-link to="/career-paths/employment/self-introduction" class="career-button">完善个人背景</router-link>
      </aside>
      <div class="business-stack account-content">
        <section class="business-panel"><div class="business-panel-head"><h2>我的简历</h2><router-link to="/resume" class="career-link">{{ resume ? '继续编辑 →' : '创建简历 →' }}</router-link></div><template v-if="resume"><div class="account-resume-summary"><div><span class="account-document-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6"/></svg></span><div><h3>{{ resume.name || '我的简历' }}</h3><p>{{ resume.target_position || '还没有填写目标岗位' }}</p></div></div><router-link to="/resume" class="career-button">打开工作台</router-link></div><div class="account-resume-details"><div><span>教育经历</span><strong>{{ resume.education?.length || 0 }} 条</strong></div><div><span>项目经历</span><strong>{{ resume.projects?.length || 0 }} 条</strong></div><div><span>实习经历</span><strong>{{ resume.experience?.length || 0 }} 条</strong></div></div></template><div v-else class="business-empty"><h3>把真实经历整理成第一份简历</h3><p>从教育、课程项目或实习经历开始，不需要一次写完所有内容。</p><router-link to="/resume" class="career-button">开始整理 →</router-link></div></section>
        <section class="business-panel"><div class="business-panel-head"><h2>个人背景与职业建议</h2><router-link to="/career-evaluation" class="career-link">查看职业方向 →</router-link></div><details v-if="selfIntroduction" class="account-background"><summary>查看已填写的背景</summary><p>{{ selfIntroduction }}</p></details><div v-if="recommendations.length" class="account-recommendations"><article v-for="(rec,index) in recommendations" :key="index"><span class="account-order">0{{ index + 1 }}</span><div><h3>{{ rec.career }}</h3><p>{{ rec.reason || '可前往职业方向页面查看分析。' }}</p></div></article></div><div v-else class="business-muted">还没有已保存的职业推荐，可以先填写个人背景。</div></section>
        <section class="business-panel"><div class="business-panel-head"><h2>模拟面试复盘</h2><router-link to="/interview" class="career-link">开始一次练习 →</router-link></div><div v-if="loadingReviews" class="business-empty" role="status">正在加载面试记录…</div><div v-else-if="!interviewReviews.length" class="business-empty"><h3>还没有面试复盘</h3><p>围绕自己的简历练习回答，结束后在这里回顾。</p></div><div v-else class="account-review-list"><article v-for="review in interviewReviews" :key="review.id || review.session_id"><div><h3>模拟面试复盘</h3><p>{{ review.created_at ? new Date(review.created_at).toLocaleDateString('zh-CN') : '时间未记录' }}<span v-if="review.pair_count"> · {{ review.pair_count }} 组问答</span></p><p v-if="review.latest_content" class="account-review-excerpt">{{ review.latest_content }}</p></div><button type="button" class="career-button" @click="viewReviewDetail(review.session_id)">查看复盘</button></article></div></section>
      </div>
    </div>
    <div v-if="showEditModal" class="business-dialog-backdrop" role="dialog" aria-modal="true" aria-labelledby="profile-edit-title" @keydown.esc="showEditModal = false"><section class="business-dialog"><header><h2 id="profile-edit-title">编辑个人资料</h2><button type="button" class="career-button" @click="showEditModal = false" aria-label="关闭个人资料编辑">关闭 ×</button></header><form @submit.prevent="saveProfile"><div class="business-form-grid"><div v-for="field in accountEditFields" :key="field.key" class="business-field"><label :for="'account-' + field.key">{{ field.label }}</label><input :id="'account-' + field.key" v-model="editForm[field.key]" :type="field.key === 'email' ? 'email' : 'text'" /></div><div class="business-field full-width"><label for="account-profile">个人介绍</label><textarea id="account-profile" v-model="editForm.profile" rows="3" /></div></div><footer><button type="button" class="career-button" @click="showEditModal = false">取消</button><button type="submit" class="career-button career-button-primary">保存资料</button></footer></form></section></div>
    <div v-if="showReviewModal" class="business-dialog-backdrop" role="dialog" aria-modal="true" aria-labelledby="account-review-title" @keydown.esc="closeReviewModal"><section class="business-dialog account-review-dialog"><header><h2 id="account-review-title">面试复盘详情</h2><button type="button" class="career-button" @click="closeReviewModal" aria-label="关闭面试复盘">关闭 ×</button></header><div class="business-dialog-body"><div v-if="loadingReviewDetail" class="business-empty" role="status">正在加载复盘…</div><template v-else-if="currentReview"><div class="account-review-metadata"><span>面试风格：{{ currentReview.interview_style || '未记录' }}</span><span>时长：{{ currentReview.interview_duration ?? '未记录' }} 分钟</span><span>问答：{{ currentReview.question_count ?? 0 }} / {{ currentReview.answer_count ?? 0 }}</span><span v-if="currentReview.overall_score !== null && currentReview.overall_score !== undefined">综合评分：{{ currentReview.overall_score }}</span></div><div class="account-review-full">{{ currentReview.review_content }}</div><section v-for="section in accountReviewSections" :key="section.key" v-show="currentReview[section.key]" class="account-review-section"><h3>{{ section.label }}</h3><ul><li v-for="(item,index) in String(currentReview[section.key] || '').split('\n').filter(s => s.trim())" :key="index">{{ item }}</li></ul></section></template></div></section></div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI, resumeAPI, interviewAPI } from '@/api'

const router = useRouter()

const user = ref(null)
const showEditModal = ref(false)
const avatarInput = ref(null)
const avatarPreview = ref(null)
const uploadingAvatar = ref(false)
const editForm = ref({
  username: '',
  email: '',
  profile: '',
  school: '',
  major: '',
  education: '',
  address: ''
})
const message = ref('')
const messageType = ref('') // success, error, info
const recommendations = ref([])
const selfIntroduction = ref('')
const resume = ref(null)
const interviewReviews = ref([])
const loadingReviews = ref(false)
const showReviewModal = ref(false)
const currentReview = ref(null)
const loadingReviewDetail = ref(false)

onMounted(async () => {
  try {
    const response = await userAPI.getProfile()
    user.value = response
    // 初始化编辑表单
    editForm.value = {
      username: user.value?.username || '',
      email: user.value?.email || '',
      profile: user.value?.profile || '',
      school: user.value?.school || '',
      major: user.value?.major || '',
      education: user.value?.education || '',
      address: user.value?.address || ''
    }

    // 加载职业推荐数据
    loadRecommendations()

    // 加载自我介绍数据
    loadSelfIntroduction()

    // 加载简历数据
    loadResume()

    // 加载面试复盘数据
    loadInterviewReviews()
  } catch (err) {
    console.error('获取用户信息失败:', err)
    console.error('错误详情:', err.response?.data || err.message)
  }
})

// 加载简历数据
const loadResume = async () => {
  try {
    const data = await resumeAPI.get()
    resume.value = data
    console.log('Loaded resume:', resume.value)
  } catch (error) {
    console.log('Resume not found or not created yet:', error)
    resume.value = null
  }
}

// 加载职业推荐数据
const loadRecommendations = () => {
  try {
    const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
    if (careerRecommendationsStr) {
      recommendations.value = JSON.parse(careerRecommendationsStr)
      console.log('Loaded career recommendations from localStorage:', recommendations.value)
    } else {
      // 尝试从 aiResponse 中获取推荐数据
      const aiResponseStr = localStorage.getItem('aiResponse')
      if (aiResponseStr) {
        const aiResponse = JSON.parse(aiResponseStr)
        if (aiResponse.recommendations) {
          recommendations.value = aiResponse.recommendations
          console.log('Loaded career recommendations from aiResponse:', recommendations.value)
        }
      }
    }
  } catch (error) {
    console.error('Failed to load career recommendations:', error)
  }
}

// 加载自我介绍数据
const loadSelfIntroduction = () => {
  try {
    const selfIntroductionStr = localStorage.getItem('selfIntroduction')
    if (selfIntroductionStr) {
      const selfIntroData = JSON.parse(selfIntroductionStr)
      // 构建自我介绍文本
      selfIntroduction.value = `姓名: ${selfIntroData.name || ''}\n学校: ${selfIntroData.school || ''}\n性别: ${selfIntroData.gender || ''}\n技能: ${selfIntroData.skills?.join('、') || '无'}\n其他技能: ${selfIntroData.otherSkills || '无'}\n条件自述: ${selfIntroData.selfDescription || '无'}\n职业期望: ${selfIntroData.goal || '无'}`
      console.log('Loaded self introduction from localStorage:', selfIntroduction.value)
    }
  } catch (error) {
    console.error('Failed to load self introduction:', error)
  }
}

// 加载面试复盘数据
const loadInterviewReviews = async () => {
  loadingReviews.value = true
  try {
    const response = await interviewAPI.listReviews()
    if (response.success) {
      interviewReviews.value = response.data
      console.log('Loaded interview reviews:', interviewReviews.value)
    }
  } catch (error) {
    console.error('Failed to load interview reviews:', error)
  } finally {
    loadingReviews.value = false
  }
}



// 打开编辑模态框时，同步用户数据到表单
const openEditModal = () => {
  showEditModal.value = true
  editForm.value = {
    username: user.value?.username || '',
    email: user.value?.email || '',
    self_introduction: user.value?.self_introduction || '',
    school: user.value?.school || '',
    major: user.value?.major || '',
    education: user.value?.education || '',
    address: user.value?.address || ''
  }
}

const triggerAvatarUpload = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 显示预览
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)

  // 上传头像
  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)

    const response = await userAPI.uploadAvatar(formData)
    user.value = response
    // 更新 localStorage 中的用户数据
    localStorage.setItem('user', JSON.stringify(response))
    // 清空预览，显示 user.avatar
    avatarPreview.value = null
    showMessage('头像上传成功', 'success')
  } catch (err) {
    console.error('上传头像失败:', err)
    showMessage('上传头像失败，请重试', 'error')
  } finally {
    uploadingAvatar.value = false
  }
}

const saveProfile = async () => {
  try {
    const response = await userAPI.updateProfile(editForm.value)
    user.value = response
    // 更新 localStorage 中的用户数据
    localStorage.setItem('user', JSON.stringify(response))
    showEditModal.value = false
    showMessage('个人资料更新成功', 'success')
  } catch (err) {
    console.error('更新个人资料失败:', err)
    showMessage('更新失败，请重试', 'error')
  }
}

const showMessage = (msg, type = 'info') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

const goToResume = () => {
  router.push('/resume')
}

const goToInterview = () => {
  router.push('/interview')
}

const viewReviewDetail = async (sessionId) => {
  console.log('View review detail:', sessionId)
  loadingReviewDetail.value = true
  try {
    const response = await interviewAPI.getReview(sessionId)
    if (response.success) {
      currentReview.value = response.data
      showReviewModal.value = true
    }
  } catch (error) {
    console.error('Failed to load review detail:', error)
  } finally {
    loadingReviewDetail.value = false
  }
}

const closeReviewModal = () => {
  showReviewModal.value = false
  currentReview.value = null
}



const accountEditFields = [
  { key: 'username', label: '用户名' }, { key: 'email', label: '邮箱' },
  { key: 'school', label: '学校' }, { key: 'major', label: '专业' },
  { key: 'education', label: '学历' }, { key: 'address', label: '地区' },
]
const accountReviewSections = [
  { key: 'strengths', label: '可以继续发挥的地方' },
  { key: 'weaknesses', label: '下一次优先改进' }, { key: 'suggestions', label: '具体建议' },
]
</script>

<style scoped>
.account-layout {
  display: grid;
  grid-template-columns: 245px minmax(0, 1fr);
  gap: 26px;
  align-items: start;
}
.account-profile {
  padding: 24px 20px;
  position: sticky;
  top: 88px;
}
.account-avatar {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  background: #edf4ff;
  border: 1px solid #d1e0f4;
  border-radius: 50%;
  overflow: hidden;
  color: #1768c4;
  font-size: 22px;
  font-weight: 500;
}
.account-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.account-profile h2 {
  font-size: 18px;
  margin: 15px 0 8px;
}
.account-profile > p {
  color: #8a97a8;
  font-size: 12px;
  line-height: 1.8;
}
.account-upload {
  display: inline-block;
  font-size: 12px;
  margin-top: 12px;
}
.account-profile dl {
  margin: 24px 0;
}
.account-profile dl > div {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 14px;
  padding: 11px 0;
  border-top: 1px solid #edf0f4;
  font-size: 12px;
  line-height: 1.8;
}
.account-profile dt {
  color: #98a2b3;
}
.account-profile dd {
  color: #667085;
  overflow-wrap: anywhere;
}
.account-profile > .career-button {
  width: 100%;
}
.account-content > .business-panel {
  padding: 24px;
}
.account-content .business-panel-head {
  margin-bottom: 22px;
}
.account-resume-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px;
  border: 1px solid #e0e7f0;
  border-radius: 6px;
  background: #fafcfe;
}
.account-resume-summary > div {
  display: flex;
  align-items: center;
  gap: 14px;
}
.account-document-icon {
  display: block;
  width: 34px;
  height: 40px;
  flex: none;
  color: #83a2c6;
}
.account-document-icon svg {
  width: 100%;
  height: 100%;
}
.account-resume-summary h3 {
  font-size: 15px;
  font-weight: 500;
}
.account-resume-summary p {
  color: #8a97a8;
  font-size: 12px;
  margin-top: 6px;
}
.account-resume-details {
  display: flex;
  gap: 40px;
  margin-top: 20px;
}
.account-resume-details > div {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}
.account-resume-details span {
  color: #98a2b3;
}
.account-resume-details strong {
  font-weight: 500;
  color: #667085;
}
.account-background {
  padding-bottom: 18px;
  margin-bottom: 6px;
  border-bottom: 1px solid #edf0f4;
}
.account-background summary {
  cursor: pointer;
  font-size: 13px;
  color: #667085;
}
.account-background p {
  color: #8a97a8;
  font-size: 13px;
  white-space: pre-wrap;
  margin-top: 15px;
}
.account-recommendations {
  display: grid;
}
.account-recommendations > article {
  display: flex;
  gap: 15px;
  padding: 18px 0;
  border-bottom: 1px solid #edf0f4;
}
.account-recommendations > article:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}
.account-order {
  color: #91a5bd;
  font-size: 11px;
  padding-top: 3px;
}
.account-recommendations h3 {
  font-size: 14px;
  font-weight: 500;
}
.account-recommendations p {
  font-size: 13px;
  color: #8a97a8;
  margin-top: 7px;
  line-height: 1.9;
}
.account-review-list article {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 0;
  border-top: 1px solid #edf0f4;
}
.account-review-list article:first-child {
  border-top: 0;
  padding-top: 0;
}
.account-review-list h3 {
  font-size: 14px;
  font-weight: 500;
}
.account-review-list p {
  color: #8a97a8;
  font-size: 12px;
  margin-top: 7px;
}
.account-review-excerpt {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.account-review-list .career-button {
  flex: none;
}
.account-message {
  margin-bottom: 22px;
}
.account-review-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 22px;
  color: #8a97a8;
  font-size: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--career-border);
}
.account-review-full {
  white-space: pre-wrap;
  color: #586577;
  font-size: 14px;
  line-height: 1.95;
  margin-top: 20px;
}
.account-review-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #edf0f4;
}
.account-review-section h3 {
  color: #475467;
  font-size: 14px;
}
.account-review-section ul {
  margin-top: 12px;
  list-style: disc;
  padding-left: 20px;
}
.account-review-section li {
  color: #7a8799;
  font-size: 13px;
  line-height: 1.9;
}
.account-review-dialog {
  max-width: 830px;
}
@media (max-width: 900px) {
  .account-layout {
    grid-template-columns: 1fr;
  }
  .account-profile {
    position: static;
  }
  .account-resume-details {
    flex-wrap: wrap;
    gap: 18px;
  }
}
</style>
