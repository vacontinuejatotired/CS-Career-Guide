import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { createInterviewService } from '../src/features/interview/service.js'
import { LegacyInterviewImplementation, formatLegacyResume } from '../src/features/interview/legacy/implementation.js'
import { readLegacyStream } from '../src/features/interview/legacy/stream.js'

const baseline = JSON.parse(await readFile(new URL('./fixtures/interview-legacy.json', import.meta.url), 'utf8'))

test('interview voice selection and cancellation reach each request; reviews remain text-only', async () => {
  const calls = []
  const implementation = new LegacyInterviewImplementation({readResume: () => null,
    chatStream: async (...args) => { calls.push(args); return response([{type:'chunk',content:'回复'}]) },
    saveReview() {}, transcribe() {},
  })
  const controller = new AbortController()
  const context = {style:'gentle',sessionId:'s1',enableTts:true,signal:controller.signal}
  await implementation.start(context)
  await implementation.answer({...context,answer:'回答'})
  await implementation.generateReview({...context,messages:[{type:'user',content:'经历'.repeat(50)}]})
  assert.deepEqual(calls.map(args => args[4].enableTts), [true,true,false])
  assert.ok(calls.every(args => args[4].signal === controller.signal))
})

function response(events) {
  return new Response(events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('') + 'data: [DONE]\n\n')
}

for (const scenario of baseline.turns) {
  test(`legacy ${scenario.style}: start, answer and review match original requests`, async () => {
    const calls = []
    const service = createInterviewService(new LegacyInterviewImplementation({
      readResume: () => JSON.stringify(scenario.resume),
      chatStream: async (...args) => {
        calls.push(args)
        return response([{ type: 'chunk', content: '测试内容' }])
      },
      saveReview: async () => ({ success: true }), transcribe: async () => ({ result: 'success' })
    }))
    const context = { style: scenario.style, sessionId: 'baseline-session' }
    await service.start(context)
    await service.answer({ ...context, answer: scenario.answer })
    const review = await service.generateReview({ ...context, messages: scenario.conversation })
    assert.deepEqual(calls.map(args => args.slice(0, 4)), scenario.requests)
    assert.ok(calls.every(args => args[4].enableTts === false))
    assert.deepEqual(review, { skipped: false, content: '测试内容' })
  })
}

test('stream handles split UTF-8, CRLF, DONE followed by session, and an unterminated final event once', async () => {
  const text = 'data: {"type":"chunk","content":"下一题"}\r\n\r\ndata: [DONE]\r\n\r\ndata: {"type":"end","session_id":"s1"}'
  const bytes = new TextEncoder().encode(text)
  const stream = new ReadableStream({ start(controller) {
    for (const byte of bytes) controller.enqueue(Uint8Array.of(byte))
    controller.close()
  } })
  const events = []
  await readLegacyStream(new Response(stream), event => events.push(event))
  assert.deepEqual(events, [{ type: 'chunk', content: '下一题' }, { type: 'end', session_id: 's1' }])
  assert.equal(stream.locked, false)
})

test('stream forwards audio and errors, ignores debug comments and malformed data', async () => {
  const events = []
  await readLegacyStream(new Response(': ping\n\ndata: bad-json\n\ndata: {"type":"audio","audio":"fake"}\n\ndata: {"type":"error","content":"failed"}\n\n'), event => events.push(event))
  assert.deepEqual(events, [{ type: 'audio', audio: 'fake' }, { type: 'error', content: 'failed' }])
  await assert.rejects(readLegacyStream(new Response('', { status: 503 })), /503/)
  await assert.rejects(readLegacyStream(new Response('')), /未收到任何数据/)
})

test('review keeps existing save payload and excludes the closing placeholder', async () => {
  let saved
  const messages = [...baseline.turns[0].conversation, { type: 'ai', content: '面试结束，感谢你的参与！正在生成面试复盘...' }]
  const service = createInterviewService(new LegacyInterviewImplementation({
    readResume: () => null, chatStream: async () => response([{ type: 'chunk', content: '优点' }, { type: 'chunk', content: '与建议' }]),
    saveReview: async data => { saved = data; return { success: true } }, transcribe: async data => data
  }))
  const chunks = []
  const review = await service.generateReview({ messages, style: 'technical', sessionId: 's1' }, event => chunks.push(event.content))
  assert.deepEqual(chunks, ['优点', '与建议'])
  await service.saveReview({ messages, content: review.content, style: 'technical', sessionId: 's1', remainingTime: 720 })
  assert.deepEqual(saved, { session_id: 's1', review_content: '优点与建议', interview_style: 'technical', interview_duration: 3, question_count: 1, answer_count: 1 })
  const audio = new FormData()
  assert.equal(await service.transcribe(audio), audio)
})

test('short conversations do not call the model, and a missing resume stays optional', async () => {
  let calls = 0
  const implementation = new LegacyInterviewImplementation({
    readResume: () => null, chatStream: async () => { calls++; return response([{ type: 'chunk', content: '问题' }]) },
    saveReview() {}, transcribe() {}
  })
  const result = await implementation.generateReview({ messages: [], style: 'gentle' })
  assert.equal(result.skipped, true)
  assert.equal(calls, 0)
  assert.equal(formatLegacyResume(null), null)
  await implementation.start({ style: 'gentle', sessionId: '' })
  assert.equal(calls, 1)
})

test('an alternative implementation runs through the same facade without legacy HTTP dependencies', async () => {
  const alternative = {
    async start(context, onEvent) { await onEvent({ type: 'chunk', content: `new:${context.style}` }) },
    answer() { return this.marker }, generateReview() {}, saveReview() {}, transcribe() {}, marker: 'replacement'
  }
  const service = createInterviewService(alternative)
  const events = []
  await service.start({ style: 'technical' }, event => events.push(event))
  assert.deepEqual(events, [{ type: 'chunk', content: 'new:technical' }])
  assert.equal(service.answer(), 'replacement')
  assert.throws(() => createInterviewService({}), /must provide start/)
})

test('unavailable browser storage does not prevent a legacy interview from starting', async () => {
  let request
  const implementation = new LegacyInterviewImplementation({
    readResume() { throw new Error('storage unavailable') },
    chatStream: async (...args) => { request = args; return response([{ type: 'chunk', content: '你好' }]) },
    saveReview() {}, transcribe() {}
  })
  const original = console.error
  console.error = () => {}
  try {
    await implementation.start({ style: 'gentle', sessionId: 's1' })
  } finally {
    console.error = original
  }
  assert.ok(request[0].includes('现在开始面试。'))
  assert.ok(!request[0].includes('【面试者简历信息】'))
})
