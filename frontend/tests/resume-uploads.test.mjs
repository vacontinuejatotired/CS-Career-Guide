import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import {
  MAX_UPLOADED_RESUMES,
  UPLOAD_LIMIT_MESSAGE,
  canUploadResume,
  normalizeUploadedResumes,
  resumeRequestOptions,
} from '../src/features/resume/uploads.js'

test('uploaded resumes are capped at two and malformed lists stay empty', () => {
  assert.equal(MAX_UPLOADED_RESUMES, 2)
  assert.equal(canUploadResume(0), true)
  assert.equal(canUploadResume(1), true)
  assert.equal(canUploadResume(2), false)
  assert.match(UPLOAD_LIMIT_MESSAGE, /请先删除旧简历/)
  assert.deepEqual(normalizeUploadedResumes({ results: [{ id: 1 }] }), [{ id: 1 }])
  assert.deepEqual(normalizeUploadedResumes({ results: 'invalid' }), [])
  assert.deepEqual(normalizeUploadedResumes(null), [])
})

test('interview resume source maps to the backend selection contract', () => {
  assert.deepEqual(resumeRequestOptions('platform', '9'), { resumeMode: 'platform', uploadedResumeId: null })
  assert.deepEqual(resumeRequestOptions('uploaded', 9), { resumeMode: 'uploaded', uploadedResumeId: '9' })
  assert.deepEqual(resumeRequestOptions('uploaded', ''), { resumeMode: 'uploaded', uploadedResumeId: null })
})

test('personal center exposes upload, delete, file viewing and parsed status', async () => {
  const source = await readFile(new URL('../src/views/users/Index.vue', import.meta.url), 'utf8')
  assert.match(source, /id="uploaded-resumes"/)
  assert.match(source, /UPLOAD_LIMIT_MESSAGE/)
  assert.match(source, /resumeAPI\.listUploads/)
  assert.match(source, /resumeAPI\.uploadResume/)
  assert.match(source, /resumeAPI\.deleteUpload/)
  assert.match(source, /upload\.parsed_degraded/)
  assert.match(source, /upload\.file_url/)
})
