export interface User {
  id: string
  username: string
  is_admin: boolean
  telegram_thread_id: number
  created_at: string
}

export interface FileItem {
  id: string
  display_name: string
  original_filename: string
  mime_type: string
  size_bytes: number
  folder_path: string | null
  is_trashed: boolean
  trashed_at: string | null
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Stats {
  total_files: number
  total_bytes: number
  by_type: { mime_type: string; count: number; size_bytes: number }[]
  total_users?: number
  by_user?: { username: string; count: number; size_bytes: number }[]
}
