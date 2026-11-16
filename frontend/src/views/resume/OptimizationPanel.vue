<template>
  <section class="optimization-panel" aria-labelledby="optimization-title">
    <div class="optimization-heading"><div><p class="career-eyebrow">求职准备 / 岗位对照</p><h2 id="optimization-title">对照目标岗位，打磨真实经历。</h2><p>分析当前账号已同步到服务器的简历。编辑区未保存的改动不参与分析，建议不会自动覆盖原稿。</p></div><span class="availability">确认后应用</span></div>
    <div class="optimization-layout"><form novalidate @submit.prevent="analyze"><label for="resume-target-jd">目标岗位 JD</label><textarea id="resume-target-jd" v-model="state.jd" :disabled="state.busy" maxlength="20000" rows="9" ref="jdInput" aria-describedby="analysis-requirements" placeholder="粘贴岗位职责与任职要求。" /><p class="optimization-note">首版支持技能和个人自评的保守文字整理。已有事实短语、否定和数字需保留，不支持自动补经历。</p><p id="analysis-requirements" class="optimization-note">{{ saving ? '简历正在保存，请稍候。' : !state.jd.trim() ? '请先填写上方目标岗位 JD，再点击分析。' : '将分析下方已保存简历；如刚修改过内容，请先在编辑区保存。' }}</p><button class="career-button career-button-primary" :disabled="state.busy||saving">{{ state.busy?'正在处理…':'分析已保存简历' }}</button></form><aside><h3>有依据，才值得修改</h3><ul><li>技能匹配为关键词基线，缺项表示未找到文本证据，不代表能力判断。</li><li>每条建议展示原文、改写理由和引用证据。</li><li>只应用你选择的建议，编辑后仍需通过服务端校验。</li></ul></aside></div>
    <section class="saved-source" aria-label="分析使用的简历">
      <h3>分析使用的简历</h3>
      <button type="button" class="career-button" :disabled="state.busy||saving" @click="actions.refreshResume">刷新已保存简历</button>
      <p v-if="state.savedResume">{{ preview.name || '未填写姓名' }} · {{ preview.target || '未填写意向岗位' }} · 保存版本 {{ state.savedResume.edit_revision }}</p>
      <p v-else class="optimization-note">{{ state.busy ? '正在读取…' : '尚未读取到服务器简历。请先在编辑区保存，再刷新。' }}</p>
      <details v-if="state.savedResume"><summary>查看已保存简历内容</summary>
        <section v-for="section in preview.sections" :key="section.title"><h4>{{ section.title }}</h4><div v-for="(item,index) in section.items" :key="index"><strong>{{ item.title }}</strong><p>{{ item.meta }}</p><p class="source-text">{{ item.description }}</p><p>{{ item.url }}</p></div></section>
        <p v-if="!preview.sections.length">尚未填写经历、技能或个人自评，请返回编辑区补充并保存。</p>
      </details>
    </section>
    <p v-if="state.status" class="optimization-status" role="status">{{ state.status }}</p>
    <section v-if="state.analysis" class="analysis-result" aria-label="分析结果">
      <h3>岗位对照</h3><p>已找到依据：{{ state.analysis.result.matches.join('、') || '暂无' }}</p><p>尚未找到依据：{{ state.analysis.result.gaps.join('、') || '暂无' }}</p>
      <p class="optimization-note">分析基于保存版本 {{ state.analysis.base_revision }}。没有识别到的技能不代表不存在，请人工核对。</p>
      <ul class="matching-evidence"><li v-for="item in state.analysis.result.matching?.evidence || []" :key="item.skill"><strong>{{ item.skill }}</strong> · {{ item.field_path }}<blockquote>{{ item.quote }}</blockquote></li></ul>
      <section v-if="state.analysis.result.star_reviews?.length" aria-label="STAR经历整理"><h3>按 STAR 整理经历</h3><p class="optimization-note">仅摘录已有原文。缺项请补充真实事实，无需硬凑数字；此处内容供预览，不自动写入经历。</p><article v-for="review in state.analysis.result.star_reviews" :key="review.field_path" class="suggestion-card"><h4>{{ review.label }}</h4><dl><template v-for="(label,key) in starLabels" :key="key"><dt>{{ label }}</dt><dd>{{ review.sections[key] || '待补充' }}</dd></template></dl><ul v-if="review.questions.length"><li v-for="question in review.questions" :key="question">{{ question }}</li></ul></article></section>
      <h3>预览与确认</h3><p v-if="!state.analysis.result.suggestions.length">暂无可应用建议，简历未修改。</p>
      <article v-for="item in state.analysis.result.suggestions" :key="item.id" class="suggestion-card">
        <label class="selection"><input v-model="state.selected" type="checkbox" :value="item.id" :disabled="state.busy||state.applied" />应用{{ fieldLabel(item.field_path) }}建议</label>
        <p>原文</p><blockquote>{{ item.original }}</blockquote><label :for="`suggestion-${item.id}`">建议内容（可编辑）</label><textarea :id="`suggestion-${item.id}`" v-model="state.edits[item.id]" :disabled="state.busy||state.applied" rows="4" maxlength="20000" />
        <p>理由：{{ item.reason }}</p><ul><li v-for="(e,index) in item.evidence" :key="index">依据 · {{ e.field_path }}<blockquote>{{ e.quote }}</blockquote></li></ul>
      </article>
      <button class="career-button career-button-primary" :disabled="state.busy||state.applied||!state.selected.length" @click="actions.apply">{{ state.applied ? '已应用' : `确认应用所选 ${state.selected.length} 条建议` }}</button>
    </section>
    <section class="analysis-history" aria-label="历史分析"><h3>历史分析</h3><button class="career-button" :disabled="state.busy" @click="actions.history">加载最近分析</button><ul><li v-for="row in state.history" :key="row.id"><button type="button" :disabled="state.busy" @click="actions.open(row.id)">{{ new Date(row.created_at).toLocaleString() }} · 保存版本 {{ row.base_revision }}</button></li></ul><p v-if="state.history && !state.history.length">暂无分析记录。</p></section>
  </section>
</template>
<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { resumePreview } from '@/features/interview/resume-preview.js'
import { resumeAPI } from '@/api'
import { platformAPI } from '@/features/career-platform'
import { createResumeOptimization } from '@/features/career-platform/resume-optimization.js'
const props=defineProps({saving:Boolean,active:Boolean})
const emit=defineEmits(['applied','busy'])
const state=reactive({jd:'',busy:false,status:'',analysis:null,selected:[],edits:{},applied:false,history:null,savedResume:null})
watch(()=>state.busy,value=>emit('busy',value),{flush:'sync'})
const actions=createResumeOptimization({api:platformAPI,getResume:()=>resumeAPI.get(),state,isBlocked:()=>props.saving,onApplied:receipt=>emit('applied',receipt)})
const jdInput=ref(null)
const preview=computed(()=>resumePreview(state.savedResume))
watch(()=>props.active,value=>{if(value) actions.refreshResume()},{immediate:true})
async function analyze(){
  if(!state.jd.trim()) jdInput.value?.focus()
  await actions.analyze()
}
const fieldLabel=field=>({skills:'专业技能',self_evaluation:'个人自评'}[field]||field)
const starLabels={situation:'S · 背景',task:'T · 任务',action:'A · 行动',result:'R · 结果'}
</script>
<style scoped>
.saved-source{margin-top:24px;padding:18px;border:1px solid var(--career-border);border-radius:8px;overflow-wrap:anywhere}.saved-source h3,.saved-source h4{font-weight:600;margin:12px 0}.saved-source summary{cursor:pointer;margin-top:12px}.saved-source section{margin-top:18px}.source-text{white-space:pre-wrap}
.suggestion-card dl{display:grid;grid-template-columns:90px minmax(0,1fr);gap:10px;margin:14px 0}.suggestion-card dt{font-weight:600}.suggestion-card dd{margin:0;white-space:pre-wrap}
.analysis-result,.analysis-history{margin-top:28px;border-top:1px solid var(--career-border);padding-top:24px;overflow-wrap:anywhere}.analysis-result h3,.analysis-history h3{font-size:18px;margin-bottom:14px}.suggestion-card{padding:20px;border:1px solid var(--career-border);border-radius:8px;margin:18px 0}.suggestion-card textarea{display:block;box-sizing:border-box;width:100%;border:1px solid #ccd8ce;border-radius:8px;padding:12px;margin:12px 0;font:inherit;line-height:1.8}.suggestion-card p{margin:10px 0}.selection{display:flex;align-items:center;gap:10px}.analysis-result blockquote{white-space:pre-wrap;background:#f4f6f2;padding:12px;margin:10px 0;overflow-wrap:anywhere}.analysis-history li{margin:12px 0}.analysis-history li button{text-align:left;text-decoration:underline}.matching-evidence{margin:16px 0}.optimization-panel button:disabled{opacity:.55;cursor:not-allowed}
.optimization-panel{padding:28px;background:#fff;border:1px solid var(--career-border);border-radius:12px;margin:24px 0}.optimization-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.optimization-heading h2{font-size:24px;font-weight:600;margin:12px 0}.optimization-heading p,.optimization-note{color:var(--career-muted);font-size:14px;line-height:1.8}.availability{font-size:12px;color:#80672f;background:#faf6ea;border:1px solid #d5c5a0;padding:6px 10px;white-space:nowrap;border-radius:5px}.optimization-layout{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:36px;margin-top:28px}.optimization-layout label{display:block;margin-bottom:10px;font-size:14px}.optimization-layout textarea{width:100%;padding:16px;border:1px solid #ccd8ce;border-radius:8px;font:inherit;line-height:1.8;resize:vertical}.optimization-note{font-size:12px;margin:12px 0 18px}.optimization-layout aside{padding:24px;background:#f1f5ee;border-radius:8px;color:#5f7163;line-height:1.9}.optimization-layout h3{font-size:18px;font-weight:600;color:#365e45;margin-bottom:14px}.optimization-layout ul{list-style:disc;padding-left:20px}.optimization-layout li{margin-bottom:12px}.optimization-layout aside p{font-size:12px;margin-top:22px}.optimization-status{padding:14px;background:#edf3ed;margin-top:18px;overflow-wrap:anywhere}.optimization-panel :is(textarea,button):focus-visible{outline:2px solid #527c60;outline-offset:4px}@media(max-width:760px){.optimization-panel{padding:20px}.optimization-heading{flex-direction:column}.optimization-layout{grid-template-columns:1fr;gap:20px}.optimization-heading h2{font-size:22px}}
</style>
