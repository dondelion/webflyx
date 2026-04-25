import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Voice profiles
export const voicesApi = {
  list: () => api.get("/voices").then((r) => r.data),
  get: (id: string) => api.get(`/voices/${id}`).then((r) => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post("/voices", data).then((r) => r.data),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.patch(`/voices/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/voices/${id}`),
};

// Samples
export const samplesApi = {
  list: (voiceId: string) =>
    api.get(`/voices/${voiceId}/samples`).then((r) => r.data),
  upload: (voiceId: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api
      .post(`/voices/${voiceId}/samples`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  waveform: (voiceId: string, sampleId: string) =>
    api
      .get(`/voices/${voiceId}/samples/${sampleId}/waveform`)
      .then((r) => r.data),
  streamUrl: (voiceId: string, sampleId: string) =>
    `/api/voices/${voiceId}/samples/${sampleId}/stream`,
  delete: (voiceId: string, sampleId: string) =>
    api.delete(`/voices/${voiceId}/samples/${sampleId}`),
};

// Chunks
export const chunksApi = {
  listForSample: (voiceId: string, sampleId: string) =>
    api
      .get(`/voices/${voiceId}/samples/${sampleId}/chunks`)
      .then((r) => r.data),
  listAll: (voiceId: string) =>
    api.get(`/voices/${voiceId}/chunks`).then((r) => r.data),
  create: (
    voiceId: string,
    sampleId: string,
    data: { start_sec: number; end_sec: number; transcript?: string; selected?: boolean }
  ) =>
    api
      .post(`/voices/${voiceId}/samples/${sampleId}/chunks`, data)
      .then((r) => r.data),
  update: (voiceId: string, chunkId: string, data: { transcript?: string; selected?: boolean }) =>
    api.patch(`/voices/${voiceId}/chunks/${chunkId}`, data).then((r) => r.data),
  delete: (voiceId: string, chunkId: string) =>
    api.delete(`/voices/${voiceId}/chunks/${chunkId}`),
  transcribe: (voiceId: string, chunkId: string) =>
    api
      .post(`/voices/${voiceId}/chunks/${chunkId}/transcribe`)
      .then((r) => r.data),
  coverage: (voiceId: string) =>
    api.get(`/voices/${voiceId}/coverage`).then((r) => r.data),
};

// Training
export const trainingApi = {
  start: (voiceId: string, data: { mode: string; chunk_ids?: string[] }) =>
    api.post(`/voices/${voiceId}/train`, data).then((r) => r.data),
  listJobs: (voiceId: string) =>
    api.get(`/voices/${voiceId}/training-jobs`).then((r) => r.data),
  getJob: (voiceId: string, jobId: string) =>
    api.get(`/voices/${voiceId}/training-jobs/${jobId}`).then((r) => r.data),
  cancel: (voiceId: string, jobId: string) =>
    api.delete(`/voices/${voiceId}/training-jobs/${jobId}`),
};

// TTS
export const ttsApi = {
  synthesizeUrl: (voiceId: string) => `/api/voices/${voiceId}/synthesize`,
};

// Auth / API keys
export const authApi = {
  listKeys: () => api.get("/auth/keys").then((r) => r.data),
  createKey: (data: { name: string; voice_id?: string }) =>
    api.post("/auth/keys", data).then((r) => r.data),
  deleteKey: (keyId: string) => api.delete(`/auth/keys/${keyId}`),
};
