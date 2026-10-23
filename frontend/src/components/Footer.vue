<template>
  <footer class="site-footer">
    <div class="career-container site-footer-inner">
      <p>© {{ new Date().getFullYear() }} CS Career Guide <span>计算机大学生职业指南</span></p>
      <nav aria-label="页脚导航"><router-link to="/career-paths">职业路径</router-link><router-link to="/career-evaluation">背景与规划</router-link><router-link to="/resume">简历</router-link><router-link to="/interview">AI 面试</router-link></nav>
    </div>
  </footer>
</template>
<style scoped>
.site-footer {
  background: #fff;
  border-top: 1px solid var(--career-border);
}
.site-footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-height: 88px;
  padding-block: 24px;
}
.site-footer p,.site-footer a {
  font-size: 12px;
  line-height: 1.7;
  color: var(--career-muted);
}
.site-footer p span {
  padding-left: 14px;
}
.site-footer nav {
  display: flex;
  gap: 22px;
}
.site-footer a:hover {
  color: var(--career-blue);
}
@media(max-width:760px) {
  .site-footer-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .site-footer p span {
    display: block;
    padding-left: 0;
  }
}
</style>
