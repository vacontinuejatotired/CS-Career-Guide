<template>
  <div class="business-page background-page"><main class="career-container">
    <BusinessPageHeader eyebrow="背景与规划 / 个人背景" title="先把你的情况说清楚" description="整理已经具备的能力与经历，让后续建议有一个真实、具体的起点。"><router-link to="/career-evaluation" class="career-button">查看已有推荐</router-link></BusinessPageHeader>
    <div class="background-layout">
      <nav class="background-steps" aria-label="填写步骤"><a href="#background-basic"><span>01</span><div><strong>基本信息</strong><small>学校、专业与年级</small></div></a><a href="#background-skills"><span>02</span><div><strong>已有能力</strong><small>技能与专业基础</small></div></a><a href="#background-experience"><span>03</span><div><strong>经历与想法</strong><small>项目、兴趣与目标</small></div></a></nav>
      <form class="business-stack background-form" @submit.prevent="nextToAssessment">
        <section id="background-basic" class="business-panel"><div class="business-panel-head"><h2>基本信息</h2><span class="business-tag">让建议贴近你的阶段</span></div><div class="business-form-grid">
          <div class="business-field"><label for="background-name">姓名</label><input id="background-name" v-model="formData.name" type="text" autocomplete="name" placeholder="如何称呼你" /></div>
          <div class="business-field"><label for="background-school">学校</label><input id="background-school" v-model="formData.school" type="text" placeholder="所在院校" /></div>
          <div class="business-field"><label for="background-major">专业</label><input id="background-major" v-model="formData.major" type="text" placeholder="例如：计算机科学与技术" /></div>
          <div class="business-field"><label for="background-grade">年级</label><input id="background-grade" v-model="formData.grade" type="text" placeholder="例如：大三" /></div>
          <fieldset class="background-gender"><legend>性别 <span>选填</span></legend><label><input v-model="formData.gender" name="gender" type="radio" value="男" />男</label><label><input v-model="formData.gender" name="gender" type="radio" value="女" />女</label><label><input v-model="formData.gender" name="gender" type="radio" value="" />不填写</label></fieldset>
        </div></section>
        <section id="background-skills" class="business-panel"><div class="business-panel-head"><h2>你已经接触过哪些能力</h2><span class="business-muted">已选 {{ formData.skills.length }} 项</span></div><p class="business-muted">按真实学习或实践经历选择，暂时不会的内容可以先不选。</p><div v-for="group in backgroundSkillGroups" :key="group.name" class="background-skill-group"><h3>{{ group.name }}</h3><div class="background-skill-options"><label v-for="skill in group.skills" :key="skill" :class="{ 'is-checked': formData.skills.includes(skill) }"><input v-model="formData.skills" type="checkbox" :value="skill" /><span>{{ skill }}</span></label></div></div><div class="business-field background-other"><label for="background-other">其他技能与补充</label><input id="background-other" v-model="formData.otherSkills" type="text" placeholder="也可以补充这里没有列出的工具或能力" /></div></section>
        <section id="background-experience" class="business-panel"><div class="business-panel-head"><h2>说说经历与下一步想法</h2></div><div class="business-field"><label for="background-description">经历与个人情况</label><textarea id="background-description" v-model="formData.selfDescription" rows="6" placeholder="可以写一段课程项目、实习、研究或团队合作经历，说明自己做了什么、喜欢什么。" /><small>具体经历比“学习能力强”更有帮助，不需要编造成果或数字。</small></div><div class="business-field background-goal"><label for="background-goal">职业期望</label><input id="background-goal" v-model="formData.goal" type="text" placeholder="例如：想了解后端实习，或者还没确定方向" /></div></section>
        <p v-if="error" class="business-notice is-error" role="alert">{{ error }}</p>
        <div class="background-form-actions"><p>确认填写内容后，保存背景并生成职业方向建议。</p><button type="submit" class="career-button career-button-primary" :disabled="loading"><span v-if="loading" class="loading loading-spinner loading-xs"></span>{{ loading ? '正在分析背景…' : '保存并查看职业推荐 →' }}</button></div>
      </form>
      <aside class="business-stack background-summary"><section class="business-panel"><h2>这次填写的背景</h2><dl><div><dt>学校</dt><dd>{{ formData.school || '尚未填写' }}</dd></div><div><dt>专业</dt><dd>{{ formData.major || '尚未填写' }}</dd></div><div><dt>年级</dt><dd>{{ formData.grade || '尚未填写' }}</dd></div><div><dt>技能</dt><dd>{{ formData.skills.length }} 项</dd></div></dl></section><section class="background-writing-tip"><h2>从一个具体例子开始</h2><p>“参与项目”可以再展开：负责什么模块、遇到什么问题、尝试了哪些方案，以及结果如何验证。</p><router-link to="/resume" class="career-link">也可以先整理简历 →</router-link></section></aside>
    </div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { aiAPI, userAPI } from '@/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')

// 从localStorage加载数据，如果没有则使用默认值
const loadFormData = () => {
  try {
    const savedData = localStorage.getItem('selfIntroduction')
    if (savedData) {
      const parsedData = JSON.parse(savedData)
      // 确保所有必要的字段都存在
      return {
        name: parsedData.name || '',
        school: parsedData.school || '',
        major: parsedData.major || '',
        grade: parsedData.grade || '',
        gender: parsedData.gender || '',
        skills: Array.isArray(parsedData.skills) ? parsedData.skills : [],
        otherSkills: parsedData.otherSkills || '',
        selfDescription: parsedData.selfDescription || '',
        goal: parsedData.goal || ''
      }
    }
  } catch (error) {
  }
  // 返回默认值
  return {
    name: '',
    school: '',
    major: '',
    grade: '',
    gender: '',
    skills: [],
    otherSkills: '',
    selfDescription: '',
    goal: ''
  }
}

const formData = ref(loadFormData())

// 页面加载时从localStorage恢复数据
onMounted(() => {
  formData.value = loadFormData()
})



// 生成自我介绍内容的哈希值，用于缓存键
function generateCacheKey(selfIntroductionText) {
  let hash = 0
  for (let i = 0; i < selfIntroductionText.length; i++) {
    const char = selfIntroductionText.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return 'career_rec_cache_' + Math.abs(hash).toString(36)
}

// 检查是否有有效的缓存
function getCachedRecommendation(selfIntroductionText) {
  try {
    const cacheKey = generateCacheKey(selfIntroductionText)
    const cachedData = localStorage.getItem(cacheKey)

    if (cachedData) {
      const parsed = JSON.parse(cachedData)
      // 检查缓存是否过期（有效期24小时）
      const now = Date.now()
      if (parsed.expireTime && parsed.expireTime > now) {
        return parsed.data
      } else {
        localStorage.removeItem(cacheKey)
      }
    }
  } catch (error) {
  }
  return null
}

// 保存缓存
function setCachedRecommendation(selfIntroductionText, data) {
  try {
    const cacheKey = generateCacheKey(selfIntroductionText)
    const expireTime = Date.now() + (24 * 60 * 60 * 1000) // 24小时

    const cacheData = {
      data: data,
      expireTime: expireTime,
      cachedAt: Date.now()
    }

    localStorage.setItem(cacheKey, JSON.stringify(cacheData))
  } catch (error) {
  }
}

async function nextToAssessment() {
  loading.value = true
  error.value = ''
  try {
    // 保存自我介绍到localStorage
    localStorage.setItem('selfIntroduction', JSON.stringify(formData.value))

    const userData = {
      name: formData.value.name || '',
      gender: formData.value.gender || '',
      school: formData.value.school || '',
      major: formData.value.major || '',
      grade: formData.value.grade || '',
      skills: formData.value.skills.join(',') || '',
      other_skills: formData.value.otherSkills || '',
      self_introduction: formData.value.selfDescription || '',
      career_goal: formData.value.goal || ''
    }

    await userAPI.updateProfile(userData)

    // 构建用户自我介绍文本（包含专业和年级信息，供大模型识别）
    const selfIntroductionText = `姓名: ${formData.value.name || ''}\n学校: ${formData.value.school || ''}\n专业: ${formData.value.major || ''}\n年级: ${formData.value.grade || ''}\n性别: ${formData.value.gender || ''}\n技能: ${formData.value.skills.join('、') || '无'}\n其他技能: ${formData.value.otherSkills || '无'}\n条件自述: ${formData.value.selfDescription || '无'}\n职业期望: ${formData.value.goal || '无'}`



    // ========== 检查缓存 ==========
    const cachedData = getCachedRecommendation(selfIntroductionText)

    if (cachedData) {
      // 使用缓存结果（瞬间显示）
      const recommendations = cachedData.recommendations

      // 存储推荐结果到localStorage
      localStorage.setItem('careerRecommendations', JSON.stringify(recommendations))

      // 存储原始分析
      if (cachedData.raw_analysis) {
        localStorage.setItem('careerRecommendationRaw', cachedData.raw_analysis)
      }

      // 存储会话ID
      if (cachedData.session_id) {
        localStorage.setItem('careerRecommendationSessionId', cachedData.session_id)
      }

      // 跳转到测评页面
      loading.value = false
      router.push('/career-evaluation')
      return
    }

    // ========== 没有缓存，调用API ==========

    try {
      // 使用aiAPI.careerRecommendation方法
      const responseData = await aiAPI.careerRecommendation(selfIntroductionText)

      if (!responseData.success) {
        error.value = `职业推荐失败: ${responseData.error}`
        loading.value = false
        return
      }

      // 解析后端返回的推荐结果（支持新旧两种格式）
      let cards = []
      let accordion = null

      // 新格式：包含 cards 和 accordion
      if (responseData.cards && Array.isArray(responseData.cards)) {
        cards = responseData.cards
        accordion = responseData.accordion || null
      } else if (responseData.recommendations && Array.isArray(responseData.recommendations)) {
        // 旧格式：兼容之前的 recommendations 数组（同时支持accordion字段）
        cards = responseData.recommendations.map(rec => ({
          career: rec.career,
          matchScore: rec.matchScore,
          reason: rec.reason
        }))
        accordion = responseData.accordion || null
      } else {
        error.value = '推荐结果格式错误'
        loading.value = false
        return
      }

      // 验证推荐结果格式
      if (!Array.isArray(cards) || cards.length === 0) {
        error.value = '推荐结果为空或格式错误'
        loading.value = false
        return
      }

      // 存储卡片数据到localStorage（用于卡片展示）
      localStorage.setItem('careerRecommendations', JSON.stringify(cards))

      // 存储手风琴数据到localStorage（用于详细分析展示）
      if (accordion) {
        localStorage.setItem('careerAnalysis', JSON.stringify(accordion))
      }

      // 存储大模型的原始响应到localStorage
      if (responseData.raw_analysis) {
        localStorage.setItem('careerRecommendationRaw', responseData.raw_analysis)
      } else if (responseData.recommendations) {
        localStorage.setItem('careerRecommendationRaw', JSON.stringify(responseData.recommendations))
      } else {
        localStorage.setItem('careerRecommendationRaw', '')
      }

      // 存储会话ID到localStorage
      if (responseData.session_id) {
        localStorage.setItem('careerRecommendationSessionId', responseData.session_id)
      }

      // ========== 保存到缓存 ==========
      const cacheData = {
        recommendations: cards,
        raw_analysis: responseData.raw_analysis || '',
        session_id: responseData.session_id || '',
        match_score: responseData.match_score || 0
      }
      setCachedRecommendation(selfIntroductionText, cacheData)

    } catch (apiError) {
      error.value = `调用职业推荐API失败: ${apiError.message}`
      loading.value = false
      return
    }

    // 跳转到测评页面
    router.push('/career-evaluation')
  } catch (err) {
    router.push('/career-evaluation')
  } finally {
    loading.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  formData.value = loadFormData()
})

onUnmounted(() => {
  // Clean up
})
const backgroundSkillGroups = [
  {
    "name": "开发与工程",
    "skills": [
      "Python 开发",
      "PostgreSQL 数据库",
      "RESTfulAPI设计",
      "并发 / 异步编程",
      "Linux 使用与脚本",
      "Git / 版本管理"
    ]
  },
  {
    "name": "数据与智能",
    "skills": [
      "数据分析",
      "机器学习",
      "深度学习框架",
      "NLP",
      "CV(图像处理)",
      "数据可视化(Plotly)"
    ]
  },
  {
    "name": "通用能力",
    "skills": [
      "基本电脑操作",
      "效率管理",
      "效率管理工具:任务管理",
      "英文资料阅读能力",
      "安全意识意识",
      "学习与问题解决能力"
    ]
  },
  {
    "name": "专业基础",
    "skills": [
      "线性代数与矩阵运算",
      "概率论与统计推断",
      "离散数学",
      "数据结构",
      "算法设计",
      "计算机网络"
    ]
  }
]
</script>

<style scoped>
.background-layout {
  display: grid;
  grid-template-columns: 175px minmax(0, 1fr) 240px;
  gap: 24px;
  align-items: start;
}
.background-steps {
  position: sticky;
  top: 88px;
  display: grid;
  gap: 7px;
}
.background-steps a {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  padding: 12px 10px;
  border-radius: 5px;
}
.background-steps a:hover {
  background: #edf3fb;
}
.background-steps a > span {
  display: grid;
  place-items: center;
  width: 23px;
  height: 23px;
  flex: none;
  border: 1px solid #cad7e7;
  border-radius: 50%;
  color: #6d89aa;
  font-size: 10px;
}
.background-steps strong {
  color: #475467;
  font-size: 13px;
  font-weight: 500;
}
.background-steps small {
  display: block;
  margin-top: 5px;
  color: #8a97a8;
  font-size: 11px;
  line-height: 1.8;
}
.background-form section {
  scroll-margin-top: 88px;
}
.background-form .business-panel {
  padding: 24px;
}
.background-gender {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 20px;
}
.background-gender legend {
  margin-bottom: 10px;
  color: #586577;
  font-size: 13px;
}
.background-gender legend span {
  margin-left: 10px;
  color: #98a2b3;
  font-size: 12px;
}
.background-gender label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #667085;
  font-size: 13px;
}
.background-skill-group {
  margin-top: 24px;
}
.background-skill-group h3 {
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
  color: #667085;
}
.background-skill-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.background-skill-options label {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 12px;
  background: #fafbfd;
  border: 1px solid #e3e9f1;
  border-radius: 5px;
  color: #586577;
  font-size: 13px;
  line-height: 1.7;
  cursor: pointer;
}
.background-skill-options label.is-checked {
  border-color: #a5c4eb;
  background: #f1f6fe;
  color: #1d5da6;
}
.background-skill-options input {
  flex: none;
}
.background-other, .background-goal {
  margin-top: 24px;
}
.background-form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 2px 0 10px;
}
.background-form-actions > p {
  color: #8a97a8;
  font-size: 12px;
  line-height: 1.8;
}
.background-form-actions button {
  flex: none;
}
.background-summary {
  position: sticky;
  top: 88px;
}
.background-summary .business-panel {
  padding: 20px;
}
.background-summary h2 {
  font-size: 14px;
}
.background-summary dl {
  margin-top: 16px;
}
.background-summary dl > div {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 10px 0;
  border-top: 1px solid #edf0f4;
  font-size: 12px;
  line-height: 1.8;
}
.background-summary dt {
  color: #8a97a8;
  flex: none;
}
.background-summary dd {
  color: #586577;
  text-align: right;
  overflow-wrap: anywhere;
}
.background-writing-tip {
  padding: 4px 12px;
}
.background-writing-tip h2 {
  font-size: 14px;
  color: #586577;
}
.background-writing-tip p {
  color: #7a8799;
  font-size: 13px;
  line-height: 1.9;
  margin: 12px 0 16px;
}
.background-writing-tip a {
  font-size: 12px;
}
@media (max-width: 1100px) {
  .background-layout {
    grid-template-columns: 150px minmax(0, 1fr);
  }
  .background-summary {
    display: none;
  }
}
@media (max-width: 760px) {
  .background-layout {
    grid-template-columns: 1fr;
  }
  .background-steps {
    display: none;
  }
  .background-skill-options {
    grid-template-columns: 1fr;
  }
  .background-form-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
