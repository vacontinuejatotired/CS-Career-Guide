<template>
  <div class="career-paths-page">
    <main class="career-container">
      <header class="paths-heading">
        <div><p class="career-eyebrow">职业路径 / 发展方向</p><h1>五条路放在一起，<br />先比较，再决定</h1><p>从你想要的学习和工作方式出发，了解不同方向需要准备什么。</p></div>
        <router-link to="/career-paths/employment/self-introduction" class="career-button career-button-primary">梳理我的背景 →</router-link>
      </header>
      <div class="paths-layout">
        <section class="paths-table" aria-label="发展方向比较">
          <div class="paths-table-heading"><span>发展方向</span><span>重点准备</span><span>了解详情</span></div>
          <article v-for="(direction,index) in careerDirections" :key="direction.id" class="path-item">
            <div class="path-title"><span>0{{ index + 1 }}</span><div><h2>{{ direction.name }}</h2><p>{{ direction.tags.join(' / ') }}</p></div></div>
            <div class="path-description"><h3>{{ direction.focus }}</h3><p>{{ direction.description }}</p></div>
            <router-link :to="'/career-paths/' + direction.id" class="career-link">查看方向 →</router-link>
          </article>
          <p class="paths-note">具体报考、征集与招聘要求，以相关单位发布的信息为准。</p>
        </section>
        <aside class="paths-aside"><h2>选择之前，先问自己</h2><ol><li><span>01</span><div><h3>我更期待怎样的下一阶段？</h3><p>进入工作、继续深造，还是探索其他发展方式。</p></div></li><li><span>02</span><div><h3>我现在能投入什么？</h3><p>看看自己的基础、时间和已有经历。</p></div></li><li><span>03</span><div><h3>下一步可以先做哪件事？</h3><p>从一份计划、一段项目经历或一次练习开始。</p></div></li></ol><router-link to="/career-evaluation" class="career-button">查看我的职业规划 →</router-link></aside>
      </div>
      <section class="paths-tools"><div><h2>方向明确后，让准备更具体</h2><p>先把经历整理好，再了解岗位、练习表达。</p></div><div><router-link to="/resume" class="career-button">整理简历</router-link><router-link to="/company-reviews" class="career-button">了解企业与职位</router-link><router-link to="/interview" class="career-button">模拟面试 →</router-link></div></section>
    </main>
  </div>
</template>
<script setup>
import { careerDirections } from '@/data/careerDirections.js'
</script>
<style scoped>
.career-paths-page {
  padding: 36px 0 64px;
  background: var(--career-bg);
  min-height: calc(100vh - 152px);
}
.paths-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 30px;
}
.paths-heading h1 {
  margin: 15px 0 14px;
  font-size: 36px;
  line-height: 1.35;
  letter-spacing: -.035em;
  font-weight: 650;
  color: var(--career-text);
}
.paths-heading>div>p:last-child {
  font-size: 15px;
  color: var(--career-muted);
  line-height: 1.8;
}
.paths-layout {
  display: grid;
  grid-template-columns: minmax(0,1fr) 280px;
  gap: 24px;
  align-items: start;
}
.paths-table {
  border: 1px solid var(--career-border);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}
.paths-table-heading {
  display: grid;
  grid-template-columns: 165px minmax(0,1fr) 84px;
  gap: 24px;
  padding: 13px 22px;
  background: #f1f5f9;
  border-bottom: 1px solid var(--career-border);
  font-size: 12px;
  color: var(--career-muted);
}
.path-item {
  display: grid;
  grid-template-columns: 165px minmax(0,1fr) 84px;
  align-items: center;
  gap: 24px;
  padding: 25px 22px;
}
.path-item+.path-item {
  border-top: 1px solid var(--career-border);
}
.path-title {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}
.path-title>span {
  font: 12px ui-monospace,Consolas,monospace;
  color: #8b98a9;
  padding-top: 5px;
}
.path-title h2 {
  font-size: 18px;
  color: #27374d;
  font-weight: 600;
}
.path-title p {
  margin-top: 6px;
  font-size: 12px;
  color: var(--career-muted);
}
.path-description h3 {
  font-size: 14px;
  font-weight: 500;
  color: #344054;
}
.path-description p {
  font-size: 13px;
  line-height: 1.8;
  color: var(--career-muted);
  margin-top: 6px;
}
.path-item>a {
  font-size: 13px;
  white-space: nowrap;
}
.paths-note {
  padding: 14px 22px;
  background: #fafbfd;
  border-top: 1px solid var(--career-border);
  font-size: 12px;
  color: #7a8799;
  line-height: 1.8;
}
.paths-aside {
  padding: 22px;
  border: 1px solid var(--career-border);
  border-radius: 8px;
  background: #fff;
}
.paths-aside>h2 {
  font-size: 16px;
  font-weight: 600;
  color: #344054;
}
.paths-aside ol {
  margin-top: 22px;
  display: grid;
  gap: 24px;
}
.paths-aside li {
  display: flex;
  gap: 12px;
}
.paths-aside li>span {
  font: 11px ui-monospace,Consolas,monospace;
  color: #6790bd;
  padding-top: 4px;
}
.paths-aside h3 {
  font-size: 13px;
  color: #344054;
  font-weight: 500;
}
.paths-aside p {
  font-size: 13px;
  line-height: 1.8;
  color: var(--career-muted);
  margin-top: 6px;
}
.paths-aside .career-button {
  width: 100%;
  margin-top: 26px;
  font-size: 13px;
}
.paths-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 25px 0;
  margin-top: 30px;
  border-top: 1px solid var(--career-border);
}
.paths-tools h2 {
  font-size: 18px;
  font-weight: 600;
  color: #344054;
}
.paths-tools p {
  font-size: 14px;
  color: var(--career-muted);
  margin-top: 8px;
}
.paths-tools>div:last-child {
  display: flex;
  gap: 10px;
}
@media(max-width:1100px) {
  .paths-layout {
    grid-template-columns: minmax(0,1fr) 250px;
  }
  .path-item,.paths-table-heading {
    grid-template-columns: 130px minmax(0,1fr) 80px;
    gap: 16px;
  }
  .paths-tools {
    align-items: flex-start;
    flex-direction: column;
  }
}
@media(max-width:760px) {
  .paths-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .paths-heading h1 {
    font-size: 29px;
  }
  .paths-layout {
    grid-template-columns: 1fr;
  }
  .paths-table-heading {
    display: none;
  }
  .path-item {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .paths-tools>div:last-child {
    flex-wrap: wrap;
  }
}
</style>
