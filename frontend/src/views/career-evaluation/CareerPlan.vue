<template>
  <div class="business-page plan-page"><main class="career-container">
    <BusinessPageHeader eyebrow="背景与规划 / 职业规划报告" title="把职业方向，拆成下一步行动" :description="targetJob ? '本次目标：' + targetJob + '。结合已填写的背景，查看准备重点与阶段安排。' : '先梳理背景并选择目标方向，再查看对应的准备建议。'"><router-link to="/career-evaluation" class="career-button">调整目标方向</router-link><router-link to="/resume" class="career-button career-button-primary">整理简历 →</router-link></BusinessPageHeader>
    <div v-if="loading" class="business-panel plan-state" role="status"><span class="loading loading-spinner loading-sm"></span><h2>正在生成职业规划</h2><p>根据已填写的个人背景和目标方向整理建议，请稍候。</p></div>
    <div v-else-if="error" class="business-panel plan-state"><h2>这份报告还没有准备好</h2><p class="business-muted">{{ error }}</p><router-link to="/career-paths/employment/self-introduction" class="career-button">返回填写个人背景</router-link></div>
    <div v-else class="plan-layout">
      <nav class="plan-toc" aria-label="报告目录"><p>报告目录</p><a href="#plan-profile">个人画像与匹配</a><a href="#plan-market">市场与城市参考</a><a href="#plan-roadmap">阶段成长路线</a><a href="#plan-learning">学习重点</a><a href="#plan-strategy">求职策略与提醒</a><a href="#plan-schedule">近期行动计划</a></nav>
      <div class="business-stack plan-body">
        <section id="plan-profile" class="business-panel"><div class="report-section-label">01 / 从当前背景出发</div><h2>个人画像与匹配</h2><p class="report-intro">{{ report.profile?.talent_portrait || '本次未提供个人画像。' }}</p><p class="report-intro">{{ report.profile?.personality_job_fit }}</p><div class="report-pair"><div><h3>可以发挥的优势</h3><ul><li v-for="(item,index) in report.profile?.strengths || []" :key="index">{{ item }}</li></ul></div><div><h3>优先补充的地方</h3><ul><li v-for="(item,index) in report.profile?.weaknesses || []" :key="index">{{ item }}</li></ul></div></div></section>
        <section id="plan-market" class="business-panel"><div class="report-section-label">02 / 了解外部机会</div><div class="business-panel-head"><h2>市场与城市参考</h2><span v-if="report.market?.market_heat" class="business-tag">{{ report.market.market_heat }}</span></div><p class="report-note">以下为本次报告提供的参考建议，具体薪资与招聘条件应结合实际岗位核实。</p><table v-if="report.market?.salary_growth_forecast?.length" class="report-table"><thead><tr><th>阶段</th><th>薪资参考</th><th>条件与前提</th></tr></thead><tbody><tr v-for="(item,index) in report.market.salary_growth_forecast" :key="index"><td>{{ item.year }}</td><td>{{ item.range }}</td><td>{{ item.condition }}</td></tr></tbody></table><div class="report-city-list"><article v-for="(item,index) in report.market?.city_suggestions || []" :key="index"><h3>{{ item.city }}<span v-if="item.fit_score !== undefined">适配参考 {{ item.fit_score }}</span></h3><p>{{ item.reason }}</p></article></div></section>
        <section id="plan-roadmap" class="business-panel"><div class="report-section-label">03 / 分阶段准备</div><h2>阶段成长路线</h2><ol class="report-roadmap"><li v-for="(item,index) in report.growth_plan?.to_graduation_roadmap || []" :key="index"><span class="report-roadmap-node" aria-hidden="true"></span><div><span class="business-tag">{{ item.phase }}</span><h3>{{ item.goal }}</h3><ul><li v-for="(action,i) in item.actions || []" :key="i">{{ action }}</li></ul></div></li></ol></section>
        <section id="plan-learning" class="business-panel"><div class="report-section-label">04 / 补充学习与实践</div><h2>学习重点</h2><article v-for="(item,index) in report.growth_plan?.learning_path || []" :key="index" class="report-learning-row"><h3>{{ item.stage }}</h3><div class="report-topics"><span v-for="(topic,i) in item.topics || []" :key="i" class="business-tag">{{ topic }}</span></div><p v-if="item.projects?.length">实践项目：{{ item.projects.join('、') }}</p></article></section>
        <section id="plan-strategy" class="business-panel"><div class="report-section-label">05 / 准备求职材料</div><h2>求职策略与提醒</h2><div class="report-pair"><div><h3>可以尝试的行动</h3><ul><li v-for="(item,index) in report.strategy?.job_hunting_strategy || []" :key="index">{{ item }}</li></ul></div><div><h3>需要留意的问题</h3><ul><li v-for="(item,index) in report.strategy?.risk_alerts || []" :key="index">{{ item }}</li></ul></div></div></section>
        <section id="plan-schedule" class="business-panel"><div class="report-section-label">06 / 从近期行动开始</div><h2>近期行动计划</h2><h3 class="report-schedule-title">本周重点</h3><p class="report-intro">{{ report.weekly_plan?.focus || '本次未提供周计划重点。' }}</p><table v-if="report.weekly_plan?.schedule?.length" class="report-table"><thead><tr><th>时间</th><th>准备事项</th><th>建议投入</th></tr></thead><tbody><tr v-for="(item,index) in report.weekly_plan.schedule" :key="index"><td>{{ item.day }}</td><td>{{ item.task }}</td><td>{{ item.hours }} 小时</td></tr></tbody></table><h3 class="report-schedule-title">本月目标</h3><p class="report-intro">{{ report.monthly_plan?.theme || '本次未提供月计划主题。' }}</p><ul><li v-for="(item,index) in report.monthly_plan?.targets || []" :key="index">{{ item }}</li></ul></section>
      </div>
      <aside class="business-stack plan-context"><section class="business-panel"><h2>这份计划的起点</h2><dl><div><dt>目标方向</dt><dd>{{ targetJob }}</dd></div><div><dt>报告来源</dt><dd>{{ cacheHit ? '已保存的分析结果' : '本次生成' }}</dd></div></dl><p class="business-muted">建议结合自己的时间与真实机会调整，不必同时完成所有事项。</p></section><section class="plan-next-step"><h2>从一件具体的事开始</h2><router-link to="/resume" class="career-link">完善一段简历经历 →</router-link><router-link to="/company-reviews" class="career-link">了解相关企业与职位 →</router-link><router-link to="/interview" class="career-link">练习讲清一个项目 →</router-link></section></aside>
    </div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { onMounted, ref } from 'vue'
import { aiAPI } from '@/api'

const loading = ref(true)
const error = ref('')
const report = ref({})
const targetJob = ref('')
const cacheHit = ref(false)

function getUserProfileFromLocalStorage() {
  const raw = localStorage.getItem('selfIntroduction')
  if (!raw) return null
  const data = JSON.parse(raw)
  return {
    major: data.major || '',
    education: '本科',
    skills: data.skills || [],
    personality: data.selfDescription || '',
    graduation_year: new Date().getFullYear() + 1,
    school: data.school || '',
    grade: data.grade || '',
    self_introduction: data.selfDescription || '',
    career_goal: data.goal || ''
  }
}

function getTargetJobFromLocalStorage() {
  const selected = localStorage.getItem('selectedCareers')
  if (selected) {
    const careers = JSON.parse(selected)
    if (Array.isArray(careers) && careers.length > 0) return careers[0]
  }

  const rec = localStorage.getItem('careerRecommendations')
  if (rec) {
    const recommendations = JSON.parse(rec)
    if (Array.isArray(recommendations) && recommendations.length > 0) {
      return recommendations[0].career
    }
  }
  return ''
}

function generateCacheKey(userProfile, targetJob) {
  const profileStr = JSON.stringify({
    major: userProfile.major,
    education: userProfile.education,
    skills: userProfile.skills.sort(),
    personality: userProfile.personality,
    school: userProfile.school,
    grade: userProfile.grade,
    self_introduction: userProfile.self_introduction,
    career_goal: userProfile.career_goal
  })
  const combined = `${targetJob}_${profileStr}`
  try {
    return btoa(encodeURIComponent(combined)).replace(/[+/=]/g, (c) => ({'+':'-', '/':'_', '=':''}[c]))
  } catch (e) {
    console.warn('btoa failed, using alternative method:', e)
    return Array.from(new TextEncoder().encode(combined))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  }
}

function getCachedReport(cacheKey) {
  try {
    const cachedData = localStorage.getItem(`careerReport_${cacheKey}`)
    if (cachedData) {
      const parsed = JSON.parse(cachedData)
      if (parsed.expireTime && parsed.expireTime > Date.now()) {
        return parsed.report
      }
    }
  } catch (e) {
    console.error('读取缓存失败:', e)
  }
  return null
}

function setCachedReport(cacheKey, reportData) {
  try {
    const cachedData = {
      report: reportData,
      expireTime: Date.now() + 7 * 24 * 60 * 60 * 1000
    }
    localStorage.setItem(`careerReport_${cacheKey}`, JSON.stringify(cachedData))
  } catch (e) {
    console.error('写入缓存失败:', e)
  }
}

onMounted(async () => {
  try {
    const userProfile = getUserProfileFromLocalStorage()
    targetJob.value = getTargetJobFromLocalStorage()

    if (!userProfile || !targetJob.value) {
      error.value = '缺少用户资料或目标职业，请先完成第一阶段测评。'
      loading.value = false
      return
    }

    const cacheKey = generateCacheKey(userProfile, targetJob.value)
    const cachedReport = getCachedReport(cacheKey)

    if (cachedReport) {
      cacheHit.value = true
      report.value = cachedReport
      console.log('缓存命中，直接使用缓存数据')
    } else {
      const resp = await aiAPI.careerReport(userProfile, targetJob.value)
      if (!resp.success) {
        throw new Error(resp.error || '职业报告生成失败')
      }

      report.value = resp.data || {}
      setCachedReport(cacheKey, report.value)
    }

    localStorage.setItem('careerReport', JSON.stringify(report.value))
  } catch (e) {
    error.value = e.message || '生成职业报告失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.plan-layout {
  display: grid;
  grid-template-columns: 155px minmax(0, 1fr) 230px;
  gap: 24px;
  align-items: start;
}
.plan-toc {
  display: grid;
  gap: 4px;
  position: sticky;
  top: 88px;
}
.plan-toc > p {
  font-size: 11px;
  color: #98a2b3;
  padding: 5px 9px 12px;
}
.plan-toc a {
  padding: 10px 9px;
  color: #667085;
  font-size: 12px;
  border-radius: 4px;
  line-height: 1.7;
}
.plan-toc a:hover {
  color: #1768c4;
  background: #edf4ff;
}
.plan-body section {
  scroll-margin-top: 88px;
}
.plan-body .business-panel {
  padding: 25px;
}
.report-section-label {
  font-size: 11px;
  color: #8a97a8;
  margin-bottom: 11px;
}
.plan-body h2 {
  font-size: 19px;
  margin-bottom: 16px;
}
.report-intro {
  color: #667085;
  font-size: 14px;
  line-height: 1.95;
  margin: 10px 0;
}
.report-pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 26px;
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #e5eaf1;
}
.report-pair h3 {
  font-size: 13px;
  font-weight: 500;
  color: #475467;
}
.plan-body ul {
  list-style: disc;
  padding-left: 18px;
  margin-top: 12px;
}
.plan-body ul > li {
  color: #667085;
  font-size: 13px;
  line-height: 1.9;
  margin-top: 8px;
}
.report-note {
  color: #8a97a8;
  font-size: 12px !important;
  line-height: 1.8;
}
.report-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  text-align: left;
}
.report-table th {
  padding: 10px;
  font-size: 12px;
  color: #8a97a8;
  font-weight: 500;
  background: #f5f7fa;
}
.report-table td {
  padding: 12px 10px;
  color: #667085;
  font-size: 13px;
  line-height: 1.8;
  border-bottom: 1px solid #edf0f4;
}
.report-table td:first-child {
  color: #475467;
  white-space: nowrap;
}
.report-city-list article {
  padding: 18px 0 0;
  margin-top: 18px;
  border-top: 1px solid #edf0f4;
}
.report-city-list h3 {
  display: flex;
  align-items: center;
  gap: 14px;
}
.report-city-list h3 span {
  color: #8a97a8;
  font-size: 11px;
  font-weight: 400;
}
.report-city-list p {
  font-size: 13px;
  color: #667085;
  margin-top: 8px;
}
.report-roadmap {
  display: grid;
  gap: 24px;
  margin-top: 25px;
}
.report-roadmap > li {
  display: grid;
  grid-template-columns: 14px minmax(0,1fr);
  gap: 15px;
  position: relative;
}
.report-roadmap > li:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 4px;
  width: 1px;
  top: 12px;
  bottom: -24px;
  background: #d4e1f0;
}
.report-roadmap-node {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 2px solid #739fce;
  background: #fff;
  margin-top: 6px;
  z-index: 1;
}
.report-roadmap h3 {
  margin-top: 10px;
  font-size: 14px;
}
.report-roadmap ul {
  margin-top: 8px;
}
.report-learning-row {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #edf0f4;
}
.report-learning-row h3 {
  font-size: 14px;
}
.report-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
.report-learning-row p {
  color: #7a8799;
  font-size: 13px;
  margin-top: 12px;
}
.report-schedule-title {
  font-size: 14px;
  margin-top: 24px;
  color: #475467;
}
.plan-context {
  position: sticky;
  top: 88px;
}
.plan-context .business-panel {
  padding: 20px;
}
.plan-context h2 {
  font-size: 14px;
}
.plan-context dl {
  margin-top: 18px;
}
.plan-context dl > div {
  padding: 11px 0;
  border-top: 1px solid #edf0f4;
}
.plan-context dt {
  font-size: 11px;
  color: #8a97a8;
}
.plan-context dd {
  font-size: 13px;
  color: #475467;
  margin-top: 6px;
  overflow-wrap: anywhere;
}
.plan-context .business-muted {
  margin-top: 14px;
  font-size: 12px;
}
.plan-next-step {
  padding: 4px 12px;
}
.plan-next-step h2 {
  font-size: 14px;
  color: #667085;
  margin-bottom: 16px;
}
.plan-next-step > a {
  display: block;
  font-size: 12px;
  margin-top: 15px;
}
.plan-state {
  text-align: center;
  padding: 60px 24px;
}
.plan-state h2 {
  margin: 16px 0 10px;
}
.plan-state p {
  color: #7a8799;
  font-size: 14px;
}
.plan-state .career-button {
  margin-top: 22px;
}
@media (max-width: 1100px) {
  .plan-layout {
    grid-template-columns: 145px minmax(0,1fr);
  }
  .plan-context {
    display: none;
  }
}
@media (max-width: 760px) {
  .plan-layout {
    grid-template-columns: 1fr;
  }
  .plan-toc {
    display: none;
  }
  .report-pair {
    grid-template-columns: 1fr;
  }
  .report-table td {
    font-size: 12px;
  }
}
</style>

