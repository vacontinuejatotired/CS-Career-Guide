import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { computed, ref } from 'vue'

// Execute the actual page actions against the same unwrapped response contract
// used by installAuthInterceptors; no HTTP server or model is needed here.
const source = readFileSync(new URL('../src/views/career-platform/Evaluation.vue', import.meta.url), 'utf8')
const script = source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm, '')
function page(api) {
  return new Function('computed', 'ref', 'onMounted', 'api', 'newRequestId', 'platformFailure',
    script + '\nreturn {loadRuns,runEvaluation,openRun,exportRun,runs,selected,status,datasetVersion,strategy};')(
    computed, ref, () => {}, api, () => 'fixture-request-id', () => '请求失败')
}

test('evaluation renders unwrapped run, listing and detail and uses the 943-question dev set', async () => {
  const run = { id: 'fixture', parameters: {}, sample_count: 9, failure_count: 0, results: [{query_id:'dev-01'}] }
  let submitted
  const actions = page({
    evaluate: async body => {submitted = body; return run},
    evaluations: async () => ({count: 1, results: [run]}),
    evaluation: async () => run,
  })
  await actions.runEvaluation()
  assert.equal(submitted.dataset_version, 'xiaolin-eval-dev-v1')
  assert.equal(submitted.strategy, 'xiaolin-baseline')
  assert.equal(actions.selected.value.id, run.id)
  assert.equal(actions.runs.value.length, 1)
  assert.match(actions.status.value, /9 条样本/)
  await actions.openRun('fixture')
  assert.equal(actions.selected.value.results[0].query_id, 'dev-01')
})

test('mismatched strategy errors retain previous results and display the backend reason', async () => {
  const actions = page({evaluate: async () => {throw {response: {status:400, data:{details:{strategy:['语料不匹配']}}}}}})
  const previous = {id:'previous'}
  actions.selected.value = previous
  await actions.runEvaluation()
  assert.equal(actions.selected.value.id, previous.id)
  assert.match(actions.status.value, /语料不匹配/)
})

test('export downloads the stored unwrapped payload without another evaluation', async () => {
  const run = {id:'saved', results:[{query_id:'one'}], parameters:{corpus_size:943}}
  let blob
  const originalDocument = globalThis.document
  const originalURL = globalThis.URL
  globalThis.document = {createElement: () => ({click(){}})}
  globalThis.URL = {createObjectURL: value => {blob=value; return 'blob:fixture'}, revokeObjectURL(){}}
  try {
    await page({exportEvaluation: async () => run}).exportRun('saved')
    assert.deepEqual(JSON.parse(await blob.text()), run)
  } finally {
    globalThis.document = originalDocument
    globalThis.URL = originalURL
  }
})
