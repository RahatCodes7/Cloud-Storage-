import axios from 'axios'
import type { AuthResponse, FileItem, Stats } from '../types'

// VITE_API_URL is set on Vercel to the Render backend URL (e.g. https://trove.onrender.com)
// Falls back to '' (same-origin proxy) for local development
const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE + '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // Don't do window.location redirect here — that creates a full page
    // reload loop. ProtectedRoute and AuthContext handle 401 redirects
    // gracefully via React Router.
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (username: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { username, password }),
  register: (username: string, password: string) =>
    api.post<AuthResponse>('/auth/register', { username, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

export const filesApi = {
  list: (params?: { q?: string; type?: string; folder?: string; sort?: string; trashed?: boolean }) =>
    api.get<FileItem[]>('/files', { params }),
  upload: (file: File, folder_path?: string, onProgress?: (pct: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    if (folder_path) form.append('folder_path', folder_path)
    return api.post<FileItem>('/files', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
  },
  update: (id: string, data: { display_name?: string; folder_path?: string | null }) =>
    api.patch<FileItem>('/files/' + id, data),
  delete: (id: string) => api.delete('/files/' + id),
  deletePermanent: (id: string) => api.delete('/files/' + id + '/permanent'),
  restore: (id: string) => api.post<FileItem>('/files/' + id + '/restore'),
  download: (id: string) => API_BASE + '/api/files/' + id + '/download',
  preview: (id: string) => API_BASE + '/api/files/' + id + '/preview',
  createShareLink: (id: string, expires_in_hours?: number, max_downloads?: number) =>
    api.post('/files/' + id + '/share', null, { params: { expires_in_hours, max_downloads } }),
}

export const statsApi = {
  get: () => api.get<Stats>('/stats'),
}

export default api
