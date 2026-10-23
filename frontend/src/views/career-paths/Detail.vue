<template>
  <div class="business-page direction-detail-page"><main class="career-container">
    <BusinessPageHeader :eyebrow="'职业路径 / ' + pathInfo.title" :title="pathInfo.title + '，先了解需要准备什么'" :description="pathInfo.subtitle"><router-link to="/career-paths" class="career-button">比较其他方向</router-link><button class="career-button career-button-primary" type="button" @click="startAssessment">梳理个人背景 →</button></BusinessPageHeader>
    <div class="direction-detail-layout"><div class="business-stack"><section class="business-panel"><div class="business-panel-head"><h2>方向说明</h2></div><p class="direction-detail-copy">{{ pathInfo.description }}</p></section><section class="business-panel"><div class="business-panel-head"><h2>准备建议</h2></div><ol class="direction-suggestions"><li v-for="(item,index) in pathInfo.suggestions" :key="index"><span>0{{ index + 1 }}</span><p>{{ item }}</p></li></ol></section><section class="business-panel"><div class="business-panel-head"><h2>继续了解的资源</h2><span class="business-tag">外部资源</span></div><div class="direction-resources"><a v-for="resource in pathInfo.resources" :key="resource.url" :href="resource.url" target="_blank" rel="noopener noreferrer"><h3>{{ resource.name }} <span aria-hidden="true">↗</span></h3><p>{{ resource.description }}</p></a></div></section></div><aside class="business-stack"><section class="business-panel"><h2>从自己的条件开始</h2><p class="business-muted direction-next">整理教育、技能、经历与个人偏好，看看当前有哪些基础，又需要补充什么。</p><button type="button" class="career-button" @click="startAssessment">填写个人背景</button></section><section v-if="pathInfo.hasAssessment" class="business-panel"><h2>已有明确的岗位目标？</h2><p class="business-muted direction-next">可以直接了解相关企业与职位。</p><label class="sr-only" for="direction-target">目标岗位</label><input id="direction-target" v-model="targetCareer" type="text" placeholder="例如：Java 后端实习" /><button type="button" class="career-button" :disabled="!targetCareer.trim()" @click="goToCompanyReviews">查看相关企业 →</button></section></aside></div>
  </main></div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const type = route.params.type
const targetCareer = ref('')

function startAssessment() {
  // 所有职业路径类型都先跳转到自我介绍页面
  router.push(`/career-paths/${type}/self-introduction`)
}

function goToCompanyReviews() {
  if (targetCareer.value.trim()) {
    // 跳转到红黑榜页面，并传递目标职业作为查询参数
    router.push({
      path: '/company-reviews',
      query: { job_title: targetCareer.value.trim() }
    })
  }
}

const pathInfo = computed(() => {
  const paths = {
    employment: {
      icon: '💼',
      title: '就业',
      subtitle: '进入企业工作，积累实战经验',
      hasAssessment: true,
      assessment: {
        title: '职业测评',
        description: '如果仍不知道未来想做什么，来评测一下吧，我们会根据你的自身情况给你推荐',
        buttonText: '开始测评'
      },
      description: '就业是大多数计算机专业学生的首选方向。通过进入企业工作，你可以将所学知识应用到实际项目中，积累实战经验，提升专业技能。就业方向包括互联网公司、金融机构、科技企业等，岗位涵盖软件开发、测试、产品经理等多个领域。',
      suggestions: [
        '打好计算机基础，掌握数据结构、算法等核心课程',
        '寻找实习机会，积累项目经验',
        '积极参加校园招聘，准备面试',
        '学习热门技术栈，如前端框架、后端语言等',
        '构建个人作品集，展示项目成果'
      ],
      resources: [
        { name: 'LeetCode', description: '算法刷题平台', url: 'https://leetcode.cn' },
        { name: '牛客网', description: '求职面试准备', url: 'https://www.nowcoder.com' },
        { name: '拉勾网', description: '互联网招聘平台', url: 'https://www.lagou.com' },
        { name: 'BOSS直聘', description: '直聊招聘平台', url: 'https://www.zhipin.com' }
      ]
    },
    postgraduate: {
      icon: '🎓',
      title: '考研',
      subtitle: '继续深造，提升学术水平',
      description: '考研是提升学历和学术水平的重要途径。通过考研，你可以选择在计算机相关领域进行更深入的学习和研究，为未来的职业发展打下更坚实的基础。考研方向包括计算机科学与技术、软件工程、人工智能等多个专业。',
      suggestions: [
        '提前了解目标院校的招生政策和考试科目',
        '制定合理的复习计划，重点复习专业课',
        '关注考研动态和政策变化',
        '准备英语和政治考试',
        '联系目标院校的导师，了解研究方向'
      ],
      resources: [
        { name: '中国研究生招生信息网', description: '考研官方网站', url: 'https://yz.chsi.com.cn' },
        { name: '考研论坛', description: '考研交流平台', url: 'https://bbs.kaoyan.com' },
        { name: '计算机考研网', description: '计算机专业考研信息', url: 'https://www.cskaoyan.com' },
        { name: '文都教育', description: '考研辅导机构', url: 'https://www.wendu.com' }
      ]
    },
    civil_service: {
      icon: '🏛️',
      title: '考公',
      subtitle: '成为公务员，服务社会',
      description: '考公是进入政府部门工作的重要途径。作为计算机专业的学生，你可以报考与计算机相关的公务员岗位，如网信办、科技部门、公安系统等。公务员工作稳定，福利待遇好，是很多人的理想选择。',
      suggestions: [
        '了解公务员考试的报考条件和考试科目',
        '系统复习行测和申论',
        '关注时事政治和社会热点',
        '参加公务员考试培训',
        '准备面试，提高综合素质'
      ],
      resources: [
        { name: '国家公务员局', description: '公务员考试官方网站', url: 'http://www.scs.gov.cn' },
        { name: '中公教育', description: '公务员考试辅导', url: 'https://www.offcn.com' },
        { name: '华图教育', description: '公务员考试辅导', url: 'https://www.huatu.com' },
        { name: '粉笔公考', description: '公务员考试APP', url: 'https://www.fenbi.com' }
      ]
    },
    military: {
      icon: '🎖️',
      title: '入伍',
      subtitle: '参军入伍，保家卫国',
      description: '入伍是一项光荣的选择。作为计算机专业的学生，你可以通过参军入伍，在部队中发挥专业特长，为国防事业做出贡献。入伍后，你可以从事与计算机相关的工作，如网络安全、信息化建设等。',
      suggestions: [
        '了解参军入伍的条件和流程',
        '保持良好的身体状态',
        '学习军事理论知识',
        '准备入伍体检',
        '了解部队的生活和工作环境'
      ],
      resources: [
        { name: '全国征兵网', description: '征兵官方网站', url: 'https://www.gfbzb.gov.cn' },
        { name: '国防部网站', description: '国防信息发布', url: 'http://www.mod.gov.cn' },
        { name: '中国军网', description: '军队新闻和信息', url: 'http://www.81.cn' },
        { name: '军事科学院', description: '军事科研机构', url: 'http://www.ams.ac.cn' }
      ]
    },
    entrepreneurship: {
      icon: '🚀',
      title: '创业',
      subtitle: '自主创业，实现梦想',
      description: '创业是实现个人价值和梦想的重要途径。作为计算机专业的学生，你可以利用所学知识，开发创新产品或服务，创办自己的企业。创业需要勇气和毅力，但也可能带来巨大的回报。',
      suggestions: [
        '寻找创新的创业方向和项目',
        '学习创业知识和技能',
        '组建优秀的创业团队',
        '了解创业政策和融资渠道',
        '做好市场调研和商业计划'
      ],
      resources: [
        { name: '创业邦', description: '创业资讯和服务', url: 'https://www.cyzone.cn' },
        { name: '36氪', description: '科技创业媒体', url: 'https://www.36kr.com' },
        { name: '创新工场', description: '创业投资机构', url: 'https://www.innovationworks.com' },
        { name: '车库咖啡', description: '创业孵化器', url: 'https://www.chekucafe.com' }
      ]
    }
  }

  return paths[type] || paths.employment
})

</script>

<style scoped>
.direction-detail-layout {
  display: grid;
  grid-template-columns: minmax(0,1fr) 280px;
  gap: 26px;
  max-width: 1180px;
}
.direction-detail-layout .business-panel {
  padding: 25px;
}
.direction-detail-copy {
  color: #667085;
  line-height: 2 !important;
}
.direction-suggestions {
  display: grid;
  gap: 0;
}
.direction-suggestions > li {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 17px 0;
  border-top: 1px solid #edf0f4;
}
.direction-suggestions > li:first-child {
  border-top: 0;
  padding-top: 0;
}
.direction-suggestions span {
  font-size: 11px;
  color: #8ba0b9;
  padding-top: 5px;
}
.direction-suggestions p {
  font-size: 14px;
  color: #667085;
}
.direction-resources {
  display: grid;
  grid-template-columns: repeat(2,minmax(0,1fr));
  gap: 0 24px;
}
.direction-resources > a {
  padding: 18px 0;
  border-top: 1px solid #edf0f4;
}
.direction-resources h3 {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 500;
}
.direction-resources h3 span {
  color: #7e9fc5;
  font-weight: 400;
}
.direction-resources p {
  color: #8a97a8;
  font-size: 13px;
  margin-top: 7px;
}
.direction-next {
  margin: 14px 0 20px;
  font-size: 13px !important;
}
.direction-detail-layout aside {
  position: sticky;
  top: 88px;
}
.direction-detail-layout aside h2 {
  font-size: 14px;
}
.direction-detail-layout aside input {
  width: 100%;
  margin-bottom: 13px;
  font-size: 13px;
}
.direction-detail-layout aside .career-button {
  width: 100%;
}
@media (max-width: 900px) {
  .direction-detail-layout {
    grid-template-columns: 1fr;
  }
  .direction-detail-layout aside {
    position: static;
  }
}
</style>
