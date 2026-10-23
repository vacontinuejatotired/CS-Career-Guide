<template>
  <div class="home-page">
    <section class="home-hero">
      <div class="career-container hero-grid">
        <div class="hero-copy">
          <p class="career-eyebrow"><span></span>计算机专业学生 · 职业探索与求职准备</p>
          <h1>找到适合你的方向，<br /><em>准备好下一次机会</em></h1>
          <p class="hero-description">先想清楚毕业后走哪条路，再把课程项目、实习和技能整理成看得见的材料。从了解方向，到完成简历、练习面试，一步步开始。</p>
          <div class="hero-actions"><router-link to="/career-paths" class="career-button career-button-primary">探索职业方向 <span aria-hidden="true">→</span></router-link><router-link to="/resume" class="career-button">完善我的简历</router-link></div>
          <div class="hero-notes"><span><b>✓</b> 五类发展方向</span><span><b>✓</b> 从自己的经历开始准备</span></div>
        </div>
        <div class="path-preview" aria-label="职业准备路径示意">
          <div class="preview-heading"><span>从这里，找到下一步</span><router-link to="/career-paths">查看全部方向 →</router-link></div>
          <div class="preview-directions"><router-link v-for="(direction,index) in careerDirections" :key="direction.id" :to="'/career-paths/' + direction.id" class="preview-direction"><span class="direction-number">0{{ index + 1 }}</span><strong>{{ direction.name }}</strong><span class="direction-focus">{{ direction.tags.join(' / ') }}</span><span class="direction-arrow" aria-hidden="true">↗</span></router-link></div>
          <div class="preview-steps"><span>求职准备，从具体的材料开始</span><div><router-link to="/career-paths/employment/self-introduction"><i></i>梳理背景</router-link><b aria-hidden="true">→</b><router-link to="/resume"><i></i>整理简历</router-link><b aria-hidden="true">→</b><router-link to="/interview"><i></i>练习面试</router-link></div></div>
        </div>
      </div>
    </section>
    <section class="career-container home-section">
      <div class="section-heading"><div><h2>你现在走到哪一步</h2><p>不用一次完成所有事，从当前最需要的一步开始。</p></div><span class="section-caption">YOUR NEXT STEP</span></div>
      <div class="next-steps"><article v-for="step in nextSteps" :key="step.title"><span class="step-caption">{{ step.stage }}</span><h3>{{ step.title }}</h3><p>{{ step.description }}</p><router-link :to="step.to" class="career-link">{{ step.action }} <span aria-hidden="true">→</span></router-link></article></div>
    </section>
    <section class="career-container home-section">
      <div class="section-heading"><div><h2>五条路，各有各的准备方式</h2><p>就业、考研、考公、入伍和创业，先了解，再选择。</p></div><router-link to="/career-paths" class="career-link">比较发展方向 →</router-link></div>
      <div class="directions-layout">
        <div class="direction-list"><router-link v-for="(direction,index) in careerDirections" :key="direction.id" :to="'/career-paths/' + direction.id" class="direction-row"><span class="direction-number">0{{ index + 1 }}</span><div><h3>{{ direction.name }}<span>{{ direction.tags.join(' / ') }}</span></h3><p>{{ direction.description }}</p></div><span class="row-action">了解方向 →</span></router-link></div>
        <aside class="direction-help"><div class="help-node" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M7 25V8h18M7 18h10V8" stroke="currentColor" stroke-width="1.5"/><circle cx="7" cy="25" r="3" fill="white" stroke="currentColor" stroke-width="1.5"/><circle cx="17" cy="18" r="3" fill="white" stroke="currentColor" stroke-width="1.5"/><circle cx="25" cy="8" r="3" fill="white" stroke="currentColor" stroke-width="1.5"/></svg></div><h3>还没想好，也没关系</h3><p>把你的教育背景、技能和经历说清楚，让职业建议有具体的起点。</p><router-link to="/career-paths/employment/self-introduction" class="career-button">梳理我的背景 →</router-link><small>已有规划报告？<router-link to="/career-evaluation" class="career-link">继续查看</router-link></small></aside>
      </div>
    </section>
    <section class="career-container home-section">
      <div class="section-heading"><div><h2>把想法，变成下一次行动</h2><p>准备材料、了解岗位，再通过练习发现需要补充的地方。</p></div></div>
      <div class="tool-list"><router-link v-for="tool in tools" :key="tool.title" :to="tool.to"><span class="tool-index">{{ tool.label }}</span><h3>{{ tool.title }} <span aria-hidden="true">↗</span></h3><p>{{ tool.description }}</p></router-link></div>
    </section>
  </div>
</template>
<script setup>
import { careerDirections } from '@/data/careerDirections.js'
const nextSteps = [
  { stage: '方向还没确定', title: '先比较，再决定', description: '了解不同发展方向的准备内容和适合的目标，把模糊的想法变成具体的选择。', to: '/career-paths', action: '了解职业路径' },
  { stage: '想法需要梳理', title: '把背景变成起点', description: '整理教育、技能与项目经历，结合自己的兴趣和偏好，获得下一步的规划建议。', to: '/career-paths/employment/self-introduction', action: '填写个人背景' },
  { stage: '准备实习与求职', title: '改简历，再练面试', description: '一边编辑，一边预览简历。再围绕自己的项目与经历练习回答，查看面试复盘。', to: '/resume', action: '进入简历工作台' },
]
const tools = [
  { label: 'RESUME', title: '简历工作台', description: '整理真实经历，编辑、预览和导出简历。', to: '/resume' },
  { label: 'OPPORTUNITIES', title: '企业与职位', description: '查看职位信息、企业评价与学长学姐建议。', to: '/company-reviews' },
  { label: 'INTERVIEW', title: 'AI 模拟面试', description: '围绕个人经历练习表达，结束后查看复盘。', to: '/interview' },
]
</script>
<style scoped>
.home-page {
  padding-bottom: 64px;
}
.home-hero {
  padding: 54px 0 48px;
  border-bottom: 1px solid var(--career-border);
  background: #fff;
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0,1.15fr) minmax(390px,1fr);
  gap: 80px;
  align-items: center;
}
.hero-copy .career-eyebrow {
  display: flex;
  align-items: center;
  gap: 10px;
}
.hero-copy .career-eyebrow>span {
  width: 18px;
  height: 1px;
  background: #a7b6c7;
}
.hero-copy h1 {
  margin: 22px 0 20px;
  font-size: clamp(34px,3.3vw,46px);
  line-height: 1.3;
  letter-spacing: -.04em;
  font-weight: 650;
  color: var(--career-text);
}
.hero-copy h1 em {
  font-style: normal;
  color: #164d85;
}
.hero-description {
  max-width: 490px;
  font-size: 16px;
  line-height: 1.85;
  color: #586577;
}
.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 26px;
}
.hero-actions .career-button {
  min-height: 44px;
}
.hero-notes {
  display: flex;
  gap: 24px;
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid var(--career-border);
  color: var(--career-muted);
  font-size: 13px;
}
.hero-notes b {
  margin-right: 5px;
  color: var(--career-teal);
  font-weight: 500;
}
.path-preview {
  border: 1px solid #d1dbe7;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 16px 35px -28px #1d293955;
}
.preview-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 15px 18px;
  background: #f5f7fa;
  border-bottom: 1px solid var(--career-border);
  color: #667085;
  font-size: 13px;
}
.preview-heading a {
  font-size: 12px;
  color: var(--career-blue);
}
.preview-directions {
  padding: 8px 18px;
}
.preview-direction {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 0;
  border-bottom: 1px solid #edf0f4;
}
.preview-direction:last-child {
  border-bottom: 0;
}
.direction-number {
  color: #8290a3;
  font: 12px ui-monospace,Consolas,monospace;
}
.preview-direction strong {
  color: #344054;
  font-size: 14px;
  font-weight: 600;
}
.direction-focus {
  margin-left: auto;
  color: #7a8799;
  font-size: 12px;
}
.direction-arrow {
  color: #6b8db7;
}
.preview-direction:hover strong {
  color: var(--career-blue);
}
.preview-steps {
  padding: 14px 18px 18px;
  background: #f8fafc;
  border-top: 1px solid var(--career-border);
}
.preview-steps>span {
  font-size: 12px;
  color: var(--career-muted);
}
.preview-steps>div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 13px;
}
.preview-steps a {
  color: #344054;
  font-size: 13px;
}
.preview-steps i {
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 6px;
  border: 1.5px solid var(--career-blue);
  border-radius: 50%;
}
.preview-steps b {
  color: #a0afbf;
  font-size: 13px;
  font-weight: 400;
}
.home-section {
  margin-top: 40px;
}
.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 19px;
}
.section-heading h2 {
  font-size: 21px;
  font-weight: 600;
  color: var(--career-text);
}
.section-heading p {
  margin-top: 7px;
  font-size: 14px;
  color: var(--career-muted);
  line-height: 1.65;
}
.section-heading>a {
  font-size: 13px;
  flex: none;
}
.section-caption {
  font-size: 11px;
  color: #8b98aa;
  letter-spacing: .06em;
}
.next-steps {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  border-top: 2px solid #344054;
}
.next-steps article {
  padding: 23px 28px 6px 0;
}
.next-steps article+article {
  padding-left: 28px;
  border-left: 1px solid var(--career-border);
}
.step-caption {
  font-size: 12px;
  color: #7a8799;
}
.next-steps h3 {
  margin: 10px 0;
  color: #27374d;
  font-size: 18px;
  font-weight: 600;
}
.next-steps p {
  color: var(--career-muted);
  font-size: 14px;
  line-height: 1.8;
}
.next-steps a {
  display: inline-block;
  font-size: 14px;
  margin-top: 17px;
}
.directions-layout {
  display: grid;
  grid-template-columns: minmax(0,1fr) 290px;
  gap: 24px;
  align-items: start;
}
.direction-list {
  background: #fff;
  border: 1px solid var(--career-border);
  border-radius: 8px;
  overflow: hidden;
}
.direction-row {
  display: grid;
  grid-template-columns: 24px minmax(0,1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 19px 22px;
}
.direction-row+.direction-row {
  border-top: 1px solid var(--career-border);
}
.direction-row:hover {
  background: #f8fbff;
}
.direction-row h3 {
  color: #344054;
  font-size: 15px;
  font-weight: 600;
}
.direction-row h3 span {
  margin-left: 12px;
  color: #7a8799;
  font-size: 12px;
  font-weight: 400;
}
.direction-row p {
  color: var(--career-muted);
  font-size: 13px;
  margin-top: 6px;
  line-height: 1.65;
}
.row-action {
  font-size: 12px;
  color: #5e7fa6;
  white-space: nowrap;
}
.direction-help {
  padding: 24px;
  background: #fff;
  border: 1px solid var(--career-border);
  border-radius: 8px;
}
.help-node {
  width: 42px;
  height: 42px;
  padding: 6px;
  color: var(--career-blue);
  background: var(--career-blue-soft);
  border-radius: 8px;
}
.direction-help h3 {
  font-size: 17px;
  font-weight: 600;
  margin: 18px 0 10px;
  color: #344054;
}
.direction-help p {
  font-size: 14px;
  color: var(--career-muted);
  line-height: 1.85;
}
.direction-help .career-button {
  width: 100%;
  margin-top: 22px;
}
.direction-help small {
  display: block;
  margin-top: 16px;
  font-size: 12px;
  color: #7a8799;
  text-align: center;
}
.tool-list {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  background: #fff;
  border: 1px solid var(--career-border);
  border-radius: 8px;
  overflow: hidden;
}
.tool-list>a {
  padding: 24px;
}
.tool-list>a+a {
  border-left: 1px solid var(--career-border);
}
.tool-list>a:hover {
  background: #f8fbff;
}
.tool-index {
  font: 11px ui-monospace,Consolas,monospace;
  letter-spacing: .06em;
  color: #7a8799;
}
.tool-list h3 {
  display: flex;
  justify-content: space-between;
  margin: 12px 0 8px;
  font-size: 16px;
  color: #344054;
}
.tool-list h3>span {
  font-weight: 400;
  color: #6b8db7;
}
.tool-list p {
  color: var(--career-muted);
  font-size: 13px;
  line-height: 1.75;
}
@media(max-width:1060px) {
  .hero-grid {
    gap: 36px;
    grid-template-columns: minmax(0,1fr) minmax(340px,1fr);
  }
  .hero-copy h1 {
    font-size: 36px;
  }
  .directions-layout {
    grid-template-columns: minmax(0,1fr) 260px;
  }
}
@media(max-width:760px) {
  .home-hero {
    padding: 32px 0;
  }
  .hero-grid,.directions-layout {
    grid-template-columns: 1fr;
  }
  .hero-copy h1 {
    font-size: 31px;
  }
  .hero-notes {
    gap: 14px;
    font-size: 12px;
  }
  .next-steps,.tool-list {
    grid-template-columns: 1fr;
  }
  .next-steps article,.next-steps article+article {
    padding: 20px 0;
    border-left: 0;
  }
  .next-steps article+article {
    border-top: 1px solid var(--career-border);
  }
  .tool-list>a+a {
    border-left: 0;
    border-top: 1px solid var(--career-border);
  }
  .section-caption {
    display: none;
  }
  .direction-row {
    grid-template-columns: 20px 1fr;
    padding: 16px;
    gap: 12px;
  }
  .row-action {
    display: none;
  }
  .direction-row h3 span {
    display: block;
    margin: 5px 0 0;
  }
  .section-heading {
    align-items: flex-start;
  }
}
</style>
