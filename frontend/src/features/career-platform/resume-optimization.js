import { newRequestId } from './api.js'

export function createResumeOptimization({ api, getResume, state, requestId = newRequestId, onApplied = () => {}, isBlocked = () => false }) {
  let analysisRequest, applyRequest
  const unwrap = response => response?.data ?? response
  function failure(error) {
    const code = error.response?.status
    return code === 409 ? '已保存简历或请求内容发生变化，请重新分析。'
      : code === 404 ? '未找到已保存简历或分析记录，请先保存简历。'
      : code === 400 ? '建议未通过原文依据校验。仅支持保留事实短语和数字的保守整理，请调整后重试。'
      : code === 504 ? '模型响应超时，输入已保留，可以手动重试。'
      : code === 502 ? '模型返回格式无效，输入已保留，可以手动重试。'
      : '请求未完成，输入已保留，请检查登录或稍后重试。'
  }
  function show(row) {
    state.analysis = row; state.selected = []; state.edits = {}
    state.applied = false
    for (const item of row.result?.suggestions ?? []) state.edits[item.id] = item.suggested
    applyRequest = undefined
  }
  async function analyze() {
    if (state.busy) return
    if (isBlocked()) { state.status = '简历正在保存，请保存完成后再分析。'; return }
    if (state.mode === 'job' && !state.jd.trim()) { state.status = '请先填写目标岗位 JD，再分析已保存简历。'; return }
    state.busy = true; state.status = ''
    try {
      const saved = unwrap(await getResume())
      if (!Number.isInteger(saved?.edit_revision)) throw new Error('missing saved revision')
      const previousRevision = state.savedResume?.edit_revision
      state.savedResume = saved
      if (previousRevision !== undefined && previousRevision !== saved.edit_revision) {
        state.status = '服务器简历已更新，请核对下方预览后再次分析。'; return
      }
      const input = { jd_text: state.mode === 'general' ? '' : state.jd.trim(), resume_revision: saved.edit_revision }
      const fingerprint = JSON.stringify(input)
      if (analysisRequest?.fingerprint !== fingerprint) analysisRequest = { fingerprint, id: requestId() }
      const row = unwrap(await api.analyze({ ...input, request_id: analysisRequest.id }))
      show(row)
      state.status = row.result.suggestions.length ? '分析完成。请选择需要应用的建议；确认前不会修改简历。' : '分析完成，暂无符合原文依据规则的改写建议。可查看经历整理及待补充问题。'
    } catch (error) { state.status = failure(error) }
    finally { state.busy = false }
  }
  async function apply() {
    if (state.busy || isBlocked() || state.applied || !state.analysis || !state.selected.length) return
    state.busy = true; state.status = ''
    try {
      const ids = [...state.selected].sort()
      const input = { base_revision: state.analysis.base_revision, accepted_suggestion_ids: ids,
        suggestion_edits: Object.fromEntries(ids.map(id => [id, state.edits[id]])) }
      const fingerprint = JSON.stringify([state.analysis.id, input])
      if (applyRequest?.fingerprint !== fingerprint) applyRequest = { fingerprint, id: requestId() }
      const receipt = unwrap(await api.apply(state.analysis.id, { ...input, request_id: applyRequest.id }))
      state.applied = true
      state.status = `已应用所选建议，保存版本为 ${receipt.applied_revision}。`
      onApplied(receipt)
    } catch (error) { state.status = failure(error) }
    finally { state.busy = false }
  }
  async function history() {
    if (state.busy) return
    state.busy = true
    try { state.history = unwrap(await api.analyses()).results }
    catch (error) { state.status = failure(error) }
    finally { state.busy = false }
  }
  async function open(id) {
    if (state.busy) return
    state.busy = true
    try { show(unwrap(await api.analysis(id))); state.status = '正在查看历史分析；应用时会重新检查当前简历。' }
    catch (error) { state.status = failure(error) }
    finally { state.busy = false }
  }
  async function refreshResume() {
    if (state.busy || isBlocked()) return
    state.busy = true; state.status = ''; state.savedResume = null
    try {
      const saved = unwrap(await getResume())
      if (!Number.isInteger(saved?.edit_revision)) throw new Error('missing saved revision')
      state.savedResume = saved
    } catch (error) { state.status = failure(error) }
    finally { state.busy = false }
  }
  return { analyze, apply, history, open, refreshResume }
}
