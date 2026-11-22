export const MAX_UPLOADED_RESUMES = 2
export const UPLOAD_LIMIT_MESSAGE = '最多保存两份上传简历，请先删除旧简历后再上传。'

export function normalizeUploadedResumes(response) {
  return Array.isArray(response?.results) ? response.results : []
}

export function canUploadResume(count) {
  return Number(count) < MAX_UPLOADED_RESUMES
}

export function resumeRequestOptions(source, uploadedResumeId) {
  if (source !== 'uploaded') return { resumeMode: 'platform', uploadedResumeId: null }
  return {
    resumeMode: 'uploaded',
    uploadedResumeId: uploadedResumeId ? String(uploadedResumeId) : null
  }
}
