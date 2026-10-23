<template>
  <div class="business-page evaluation-page"><main class="career-container">
    <BusinessPageHeader eyebrow="背景与规划 / 职业方向" title="把方向选得更具体一些" description="先查看已有的职业建议，再选一个想进一步了解的方向，生成可执行的准备计划。"><router-link to="/career-paths/employment/self-introduction" class="career-button">填写或修改背景</router-link></BusinessPageHeader>
    <div class="evaluation-layout">
      <nav class="evaluation-nav" aria-label="背景与规划流程"><router-link to="/career-paths/employment/self-introduction"><span>01</span><div>梳理背景<small>经历、技能与目标</small></div></router-link><a href="#career-recommendations" class="is-current"><span>02</span><div>选择职业方向<small>结合建议自主选择</small></div></a><router-link to="/career-plan"><span>03</span><div>查看准备计划<small>行动安排与学习重点</small></div></router-link><div class="evaluation-nav-note">推荐是了解方向的起点，选择可以随着经历和兴趣继续调整。</div></nav>
      <div class="business-stack">
        <section id="career-recommendations" class="business-panel"><div class="business-panel-head"><div><h2>结合个人背景的职业建议</h2><p class="business-muted recommendation-hint">推荐理由比一个分数更重要，可以先看看哪些经历与岗位相连。</p></div><button v-if="careerAnalysis" type="button" class="career-link analysis-toggle" :aria-expanded="isAccordionOpen" @click="toggleAccordion">{{ isAccordionOpen ? '收起分析' : '查看详细分析' }}</button></div>
          <div v-if="recommendations.length" class="recommendation-list"><button v-for="(rec,index) in recommendations" :key="index" type="button" class="recommendation-option role-item" :class="{ selected: selectedCareers.includes(rec.career) }" :aria-pressed="selectedCareers.includes(rec.career)" @click="toggleSelection($event)"><span class="recommendation-career">{{ rec.career }}</span><span v-if="rec.matchScore !== null && rec.matchScore !== undefined" class="recommendation-score">匹配参考 {{ String(rec.matchScore).replace(/%$/, '') }}%</span><p>{{ rec.reason || '查看个人背景，结合岗位要求进一步判断。' }}</p><span class="recommendation-select">{{ selectedCareers.includes(rec.career) ? '已选择此方向' : '选择此方向 →' }}</span></button></div>
          <div v-else class="business-empty"><h3>还没有你的职业推荐</h3><p>先填写个人背景，或直接从下方职业分类里选择一个想了解的方向。</p><router-link to="/career-paths/employment/self-introduction" class="career-button">梳理个人背景 →</router-link></div>
          <div v-if="careerAnalysis && isAccordionOpen" class="business-prose career-analysis" v-html="renderedCareerAnalysis"></div>
        </section>
        <section class="business-panel career-categories"><div class="business-panel-head"><div><h2>也可以从职业分类开始探索</h2><p class="business-muted recommendation-hint">本次选择一个目标方向，后续可以返回调整。</p></div><span class="business-tag">单选</span></div><div class="career-category-grid"><section v-for="category in careerRoleGroups" :key="category.name" class="career-category"><h3>{{ category.name }}</h3><div class="career-role-options"><button v-for="role in category.roles" :key="role" type="button" class="role-item" :class="{ selected: selectedCareers.includes(role) }" :aria-pressed="selectedCareers.includes(role)" @click="toggleSelection($event)"><span>{{ role }}</span></button></div></section></div></section>
        <div class="career-selection-bar"><div><span>本次目标方向</span><strong>{{ selectedCareers[0] || '还没有选择' }}</strong><button v-if="selectedCareers.length" type="button" class="career-link" @click="removeSelection(selectedCareers[0])">清除</button></div><button type="button" class="career-button career-button-primary" :disabled="!selectedCareers.length" @click="goToCareerPlan">生成职业规划 →</button></div>
      </div>
    </div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

const router = useRouter()
const recommendations = ref([])
const isAccordionOpen = ref(false)
const careerAnalysis = ref(null)
const selectedCareers = ref([])
// 将职业分析数据转换为Markdown格式
const careerAnalysisMarkdown = computed(() => {
  if (!careerAnalysis.value) return ''

  let markdown = ''

  // 总体职业分析
  markdown += `# 总体职业分析

${careerAnalysis.value.overall}

`

  // 三个职业分析
  markdown += `# 职业推荐分析

`

  careerAnalysis.value.careers.forEach((career, index) => {
    markdown += `## ${index + 1}. ${career.title}

`

    // 匹配度（支持数字和字符串格式）
    if (career.matchScore) {
      const matchScoreStr = typeof career.matchScore === 'number' ? `${career.matchScore}%` : career.matchScore
      markdown += `- **匹配度**：${matchScoreStr}

`
    }

    // 推荐理由
    markdown += `### 推荐理由
`
    if (career.reasons && career.reasons.length > 0) {
      career.reasons.forEach(reason => {
        markdown += `- ${reason}
`
      })
    } else if (career.reason) {
      markdown += `- ${career.reason}
`
    } else {
      markdown += `- 暂无推荐理由
`
    }
    markdown += `
`

    // 技能匹配
    markdown += `### 技能匹配
`
    if (career.skills && career.skills.length > 0) {
      career.skills.forEach(skill => {
        markdown += `- ${skill}
`
      })
    } else if (career.skillsMatch && career.skillsMatch.length > 0) {
      career.skillsMatch.forEach(skill => {
        markdown += `- ${skill}
`
      })
    } else {
      markdown += `- 暂无技能匹配数据
`
    }
    markdown += `
`

    // 当前最大短板（新字段）
    if (career.weakestPoint) {
      markdown += `### 当前最大短板

${career.weakestPoint}

`
    }

    // 市场热度（新字段）
    if (career.marketDemand) {
      markdown += `### 市场热度

${career.marketDemand}

`
    }

    // 起薪范围（新字段）
    if (career.salaryRange) {
      markdown += `### 起薪范围

${career.salaryRange}

`
    }

    // 下一步建议（新字段，支持数组和字符串格式）
    if (career.nextStep) {
      markdown += `### 下一步建议
`
      if (Array.isArray(career.nextStep)) {
        career.nextStep.forEach((step, stepIndex) => {
          markdown += `${stepIndex + 1}. ${step}
`
        })
      } else {
        markdown += `${career.nextStep}
`
      }
      markdown += `
`
    } else if (career.suggestions && career.suggestions.length > 0) {
      markdown += `### 发展建议
`
      career.suggestions.forEach(suggestion => {
        markdown += `- ${suggestion}
`
      })
      markdown += `
`
    } else if (career.improvement) {
      markdown += `### 发展建议

${career.improvement}

`
    }
  })

  return markdown
})

// 渲染Markdown为HTML
const renderedCareerAnalysis = computed(() => {
  return marked(careerAnalysisMarkdown.value)
})

// 从大模型分析结果加载推荐数据
function loadRecommendations() {
  try {
    // 优先从localStorage读取cards数据（包含正确的matchScore和reason）
    const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
    if (careerRecommendationsStr) {
      const careerRecommendations = JSON.parse(careerRecommendationsStr)
      console.log('Loaded careerRecommendations:', careerRecommendations)
      if (Array.isArray(careerRecommendations) && careerRecommendations.length > 0) {
        recommendations.value = careerRecommendations.map(rec => ({
          career: rec.career || rec.职业,
          matchScore: rec.matchScore || rec.匹配度,
          reason: rec.reason || rec.推荐理由 || '基于您的背景和技能推荐'
        }))
        console.log('Loaded recommendations from careerRecommendations:', recommendations.value)
        return
      }
    }

    // 如果没有cards数据，尝试从careerAnalysis中获取（用于手风琴展示的详细数据）
    if (careerAnalysis.value && careerAnalysis.value.careers) {
      recommendations.value = careerAnalysis.value.careers.map(career => ({
        career: career.title,
        matchScore: career.matchScore ?? null,
        reason: career.reasons[0] || '基于您的背景和技能推荐'
      }))
      console.log('Loaded recommendations from career analysis:', recommendations.value)
    } else {
      recommendations.value = []
    }
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  }
}

// 从localStorage加载大模型分析结果
function loadCareerAnalysis() {
  try {
    // 从localStorage读取大模型分析结果
    const careerAnalysisStr = localStorage.getItem('careerAnalysis')
    if (careerAnalysisStr) {
      careerAnalysis.value = JSON.parse(careerAnalysisStr)
      console.log('Loaded career analysis from localStorage:', careerAnalysis.value)
    } else {
      // 尝试读取职业推荐数据
      const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
      if (careerRecommendationsStr) {
        const careerRecommendations = JSON.parse(careerRecommendationsStr)
        console.log('Loaded careerRecommendations for analysis:', careerRecommendations)
        // 解析职业推荐数据，提取职业分析数据
        if (Array.isArray(careerRecommendations)) {
          careerAnalysis.value = {
            overall: '以下方向来自已保存的职业推荐，可以结合你的背景逐项查看。',
            careers: careerRecommendations.map((rec, index) => ({
              title: rec.career || rec.职业,
              matchScore: `${rec.matchScore || rec.匹配度}%`,
              reasons: [rec.reason || rec.推荐理由 || '基于您的背景和技能推荐'],
              skills: rec.skillsMatch || rec.技能匹配 || [],
              suggestions: [rec.improvement || rec.发展建议 || '根据您的技能和背景，建议您进一步提升相关技能。']
            })),
            actionPlan: {
              short: '完成1个FastAPI+PostgreSQL+Vue的AI工具后台，部署至云服务器；同步整理NLP项目技术文档，发布至GitHub并撰写技术复盘博客。',
              medium: '使用PySpark重写项目中的数据预处理模块，对比Pandas性能差异；在Hugging Face Model Hub复现1个开源NLP模型，完成本地微调+API封装。',
              long: '精修简历，按三个方向定制版本；参加技术面试模拟；主动联系本地科技企业实习内推，发挥地域+Python+NLP复合优势。'
            }
          }
          console.log('Loaded career analysis from careerRecommendations:', careerAnalysis.value)
        } else {
          careerAnalysis.value = null
          console.log('No recommendations found in careerRecommendations')
        }
      } else {
        careerAnalysis.value = null
        console.log('No career analysis found in localStorage')
      }
    }
  } catch (error) {
    console.error('Failed to load career analysis:', error)
    careerAnalysis.value = null
  }
}

// 切换手风琴状态
function toggleAccordion() {
  isAccordionOpen.value = !isAccordionOpen.value
}

// 根据职业类型返回对应的图标
function getIconForCareer(career) {
  const careerLower = career.toLowerCase()
  if (careerLower.includes('后端') || careerLower.includes('java') || careerLower.includes('go') || careerLower.includes('python') || careerLower.includes('c++')) {
    return 'database'
  } else if (careerLower.includes('ai') || careerLower.includes('算法') || careerLower.includes('机器学习') || careerLower.includes('深度学习') || careerLower.includes('人工智能')) {
    return 'smart_toy'
  } else if (careerLower.includes('前端') || careerLower.includes('web') || careerLower.includes('react') || careerLower.includes('vue')) {
    return 'web'
  } else if (careerLower.includes('移动') || careerLower.includes('android') || careerLower.includes('ios') || careerLower.includes('flutter')) {
    return 'smartphone'
  } else if (careerLower.includes('数据') || careerLower.includes('分析') || careerLower.includes('大数据')) {
    return 'analytics'
  } else if (careerLower.includes('运维') || careerLower.includes('devops') || careerLower.includes('sre') || careerLower.includes('云')) {
    return 'cloud_sync'
  } else if (careerLower.includes('测试') || careerLower.includes('qa')) {
    return 'bug_report'
  } else if (careerLower.includes('嵌入式') || careerLower.includes('硬件') || careerLower.includes('芯片')) {
    return 'settings_input_component'
  } else if (careerLower.includes('销售') || careerLower.includes('支持') || careerLower.includes('客户')) {
    return 'support_agent'
  } else if (careerLower.includes('安全')) {
    return 'security'
  } else {
    return 'work'
  }
}

// 切换选择状态（单选模式）
function toggleSelection(event) {
  const careerName = event.currentTarget.querySelector('span:first-child').textContent.trim()
  selectedCareers.value = selectedCareers.value.includes(careerName) ? [] : [careerName]
}
function removeSelection(itemName) {
  selectedCareers.value = selectedCareers.value.filter(name => name !== itemName)
}

// 跳转到职业规划页面
function goToCareerPlan() {
  // 保存选择的职业到 localStorage 缓存中
  localStorage.setItem('selectedCareers', JSON.stringify(selectedCareers.value))

  // 跳转到职业规划页面
  router.push('/career-plan')
}

onMounted(() => {
  // 页面加载时的初始化逻辑
  loadCareerAnalysis()
  loadRecommendations()
})

onUnmounted(() => {
  // 页面卸载时的清理逻辑
})
const careerRoleGroups = [
  {
    "name": "后端开发",
    "roles": [
      "Java",
      "C++",
      "PHP",
      "Golang",
      "Python",
      "Node.js",
      "Rust",
      "C#工程师",
      "全栈开发",
      "安全工程师",
      "游戏后端",
      "游戏前端",
      "区块链",
      "信息技术岗",
      ".NET",
      "Delphi",
      "GIS工程师",
      "VB",
      "Perl",
      "Ruby",
      "Erlang",
      "后端工程师",
      "语音视频图形开发"
    ]
  },
  {
    "name": "人工智能",
    "roles": [
      "算法工程师",
      "深度学习",
      "自然语言处理",
      "机器学习",
      "计算机视觉",
      "语音识别",
      "推荐算法",
      "数据挖掘"
    ]
  },
  {
    "name": "前端开发",
    "roles": [
      "Web前端",
      "前端工程师",
      "游戏前端",
      "H5开发",
      "React/Vue",
      "小程序开发"
    ]
  },
  {
    "name": "客户端开发",
    "roles": [
      "安卓 (Android)",
      "iOS开发",
      "Flutter开发",
      "Unity3D",
      "游戏客户端"
    ]
  },
  {
    "name": "数据",
    "roles": [
      "数据分析师",
      "大数据开发",
      "数据仓库 (ETL)",
      "数据架构师"
    ]
  },
  {
    "name": "运维",
    "roles": [
      "运维工程师",
      "网络工程师",
      "安全运维",
      "SRE 工程师",
      "DBA (数据库管理)"
    ]
  },
  {
    "name": "测试",
    "roles": [
      "测试工程师",
      "自动化测试",
      "性能测试",
      "测试开发 (TestDev)"
    ]
  },
  {
    "name": "研发工程师",
    "roles": [
      "嵌入式软件开发",
      "嵌入式硬件开发",
      "固件开发",
      "FPGA/芯片设计"
    ]
  },
  {
    "name": "销售技术支持",
    "roles": [
      "售前技术工程师",
      "客户成功",
      "售后技术支持",
      "技术支持经理"
    ]
  }
]
</script>

<style scoped>
.evaluation-layout {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 28px;
  align-items: start;
}
.evaluation-nav {
  display: grid;
  gap: 9px;
  position: sticky;
  top: 88px;
}
.evaluation-nav > a {
  display: flex;
  align-items: start;
  gap: 11px;
  padding: 13px 10px;
  border-radius: 5px;
  color: #667085;
  font-size: 13px;
  line-height: 1.5;
}
.evaluation-nav > a > span {
  width: 23px;
  height: 23px;
  display: grid;
  place-items: center;
  flex: none;
  border: 1px solid #ccd7e5;
  border-radius: 50%;
  font-size: 10px;
  color: #8a97a8;
}
.evaluation-nav small {
  display: block;
  color: #8a97a8;
  font-size: 11px;
  margin-top: 7px;
}
.evaluation-nav > a.is-current {
  color: #1d5da6;
  background: #edf4ff;
}
.evaluation-nav > a.is-current > span {
  border-color: #8aafe0;
  background: #fff;
  color: #1768c4;
}
.evaluation-nav-note {
  padding: 18px 10px;
  margin-top: 12px;
  border-top: 1px solid var(--career-border);
  color: #8a97a8;
  font-size: 12px;
  line-height: 1.9;
}
.recommendation-hint {
  margin-top: 7px;
  font-size: 13px !important;
}
.analysis-toggle {
  flex: none;
  font-size: 13px;
}
.recommendation-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 12px;
  margin-top: 22px;
}
.recommendation-option {
  display: flex;
  flex-direction: column;
  text-align: left;
  padding: 18px;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  background: #fff;
}
.recommendation-option.selected {
  background: #f5f9ff;
  border-color: #84abe0;
}
.recommendation-career {
  color: #344054;
  font-size: 15px;
  font-weight: 600;
}
.recommendation-score {
  font-size: 11px;
  color: #7a8799;
  margin-top: 8px;
}
.recommendation-option > p {
  color: #667085;
  font-size: 13px;
  line-height: 1.85;
  margin: 12px 0 18px;
}
.recommendation-select {
  display: block;
  margin-top: auto;
  color: #4277b4;
  font-size: 12px;
}
.career-analysis {
  padding-top: 22px;
  margin-top: 22px;
  border-top: 1px solid var(--career-border);
}
.career-categories > .business-panel-head {
  margin-bottom: 24px;
}
.career-category-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 0;
  border: 1px solid var(--career-border);
  border-radius: 6px;
  overflow: hidden;
}
.career-category {
  padding: 19px;
  border-right: 1px solid #e5eaf1;
  border-bottom: 1px solid #e5eaf1;
  min-width: 0;
}
.career-category:nth-child(3n) {
  border-right: 0;
}
.career-category:nth-last-child(-n+3) {
  border-bottom: 0;
}
.career-category h3 {
  margin-bottom: 14px;
  font-size: 14px;
  font-weight: 600;
}
.career-role-options {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}
.career-role-options button {
  padding: 5px 9px;
  border: 1px solid #e0e6ef;
  border-radius: 4px;
  color: #667085;
  background: #f9fbfd;
  font-size: 12px;
  line-height: 1.6;
}
.career-role-options button:hover {
  border-color: #b0c6e1;
  background: #f1f6fc;
}
.career-role-options button.selected {
  border-color: #86ace0;
  background: #edf4ff;
  color: #1768c4;
}
.career-selection-bar {
  position: static;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 16px 20px;
  border: 1px solid #ccd9e8;
  border-radius: 7px;
  background: #fff;
  box-shadow: 0 4px 18px #1d29390a;
  z-index: 5;
}
.career-selection-bar > div {
  display: flex;
  align-items: center;
  gap: 16px;
}
.career-selection-bar span {
  color: #8a97a8;
  font-size: 12px;
}
.career-selection-bar strong {
  color: #344054;
  font-size: 14px;
  font-weight: 500;
}
.career-selection-bar .career-link {
  font-size: 12px;
}
@media (max-width: 1100px) {
  .evaluation-layout {
    grid-template-columns: 155px minmax(0,1fr);
    gap: 20px;
  }
  .career-category-grid {
    grid-template-columns: repeat(2,minmax(0,1fr));
  }
  .career-category:nth-child(3n) {
    border-right: 1px solid #e5eaf1;
  }
  .career-category:nth-child(2n) {
    border-right: 0;
  }
  .career-category:nth-last-child(-n+3) {
    border-bottom: 1px solid #e5eaf1;
  }
  .career-category:last-child {
    border-bottom: 0;
  }
}
@media (max-width: 760px) {
  .evaluation-layout {
    grid-template-columns: 1fr;
  }
  .evaluation-nav {
    display: none;
  }
  .recommendation-list,.career-category-grid {
    grid-template-columns: 1fr;
  }
  .career-category {
    border-right: 0 !important;
  }
  .career-selection-bar {
    flex-wrap: wrap;
  }
  .career-selection-bar > div {
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style>
