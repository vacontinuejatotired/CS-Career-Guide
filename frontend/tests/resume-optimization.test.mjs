import test from 'node:test'
import assert from 'node:assert/strict'
import { createResumeOptimization } from '../src/features/career-platform/resume-optimization.js'

function fixture() {
  const calls=[], applied=[]
  const row={id:'analysis',base_revision:3,result:{matches:['Java'],gaps:['Redis'],suggestions:[{id:'suggestion',suggested:'使用Java开发项目'}]}}
  const state={jd:'Java Redis',busy:false,status:'',analysis:null,selected:[],edits:{},applied:false,history:null}
  const api={analyze:async body=>{calls.push(['analyze',body]);return structuredClone(row)},
    apply:async (id,body)=>{calls.push(['apply',id,body]);return {applied_revision:4}},
    analyses:async()=>({results:[row]}),analysis:async()=>structuredClone(row)}
  let counter=0
  const options={api,getResume:async()=>({edit_revision:3}),state,requestId:()=>`request-${++counter}`,onApplied:value=>applied.push(value)}
  return {calls,applied,state,api,row,options,actions:createResumeOptimization(options)}
}

test('analysis reads saved revision, unwraps production response, never auto applies',async()=>{
  const f=fixture();await f.actions.analyze()
  assert.equal(f.calls[0][1].resume_revision,3)
  assert.deepEqual(f.state.selected,[])
  assert.equal(f.state.edits.suggestion,'使用Java开发项目')
  assert.equal(f.calls.length,1);assert.equal(f.applied.length,0)
})

test('explicit apply submits selected edited text only and notifies workspace',async()=>{
  const f=fixture();await f.actions.analyze();f.state.selected=['suggestion'];f.state.edits.suggestion='使用Java实现项目'
  await f.actions.apply();await f.actions.apply()
  const body=f.calls[1][2]
  assert.deepEqual(body.accepted_suggestion_ids,['suggestion'])
  assert.deepEqual(body.suggestion_edits,{suggestion:'使用Java实现项目'})
  assert.equal(body.base_revision,3);assert.equal(f.applied.length,1)
  assert.equal(f.calls.filter(c=>c[0]==='apply').length,1)
})

test('lost application response reuses request ID and preserves edited input',async()=>{
  const f=fixture();await f.actions.analyze();f.state.selected=['suggestion']
  let fail=true
  f.api.apply=async(id,body)=>{f.calls.push(['apply',id,body]);if(fail){fail=false;throw new Error('lost response')}return {applied_revision:4}}
  await f.actions.apply();assert.equal(f.state.applied,false);assert.equal(f.state.busy,false)
  await f.actions.apply()
  assert.equal(f.calls[1][2].request_id,f.calls[2][2].request_id)
  assert.equal(f.state.edits.suggestion,'使用Java开发项目')
})

test('analysis retries keep same key; changed JD gets a new key',async()=>{
  const f=fixture();let fail=true
  f.api.analyze=async body=>{f.calls.push(['analyze',body]);if(fail){fail=false;throw {response:{status:504}}}return f.row}
  await f.actions.analyze();assert.match(f.state.status,/超时/)
  await f.actions.analyze();assert.equal(f.calls[0][1].request_id,f.calls[1][1].request_id)
  f.state.jd='Python';await f.actions.analyze()
  assert.notEqual(f.calls[1][1].request_id,f.calls[2][1].request_id)
})

test('conflict keeps selection and text; old draft is never marked applied',async()=>{
  const f=fixture();await f.actions.analyze();f.state.selected=['suggestion']
  f.api.apply=async()=>{throw {response:{status:409}}}
  await f.actions.apply();assert.match(f.state.status,/重新分析/)
  assert.equal(f.applied.length,0);assert.equal(f.state.applied,false)
  assert.deepEqual(f.state.selected,['suggestion'])
})

test('history uses already unwrapped API and opens snapshot without writing',async()=>{
  const f=fixture();await f.actions.history();assert.equal(f.state.history.length,1)
  await f.actions.open('analysis');assert.equal(f.state.analysis.id,'analysis')
  assert.deepEqual(f.state.selected,[]);assert.equal(f.calls.length,0)
})

test('in-flight operations and workspace save prevent duplicate analysis or application',async()=>{
  const f=fixture();f.state.busy=true;await f.actions.analyze();assert.equal(f.calls.length,0)
  f.state.busy=false
  const actions=createResumeOptimization({...f.options,isBlocked:()=>true})
  await actions.analyze();assert.equal(f.calls.length,0)
})
