import { api } from './client'

export interface Author {
  id: number
  display_name: string
  avatar_url: string | null
}

export interface Post {
  id: number
  content: string
  image_url: string | null
  created_at: string
  likes_count: number
  comments_count: number
  user_liked: boolean
  author: Author
}

export interface Comment {
  id: number
  content: string
  created_at: string
  author: Author
}

export interface Profile {
  id: number
  email: string
  display_name: string
  avatar_url: string | null
  plan: string
}

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function imageUrl(path: string | null): string | null {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${BASE}${path}`
}

export const socialApi = {
  getFeed: (skip = 0, limit = 20) =>
    api.get<Post[]>('/social/feed', { params: { skip, limit } }).then(r => r.data),

  createPost: (content: string, file?: File) => {
    const form = new FormData()
    form.append('content', content)
    if (file) form.append('image', file)
    return api.post<Post>('/social/posts', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  deletePost: (id: number) => api.delete(`/social/posts/${id}`),

  toggleLike: (id: number) =>
    api.post<{ liked: boolean; likes_count: number }>(`/social/posts/${id}/like`).then(r => r.data),

  getComments: (id: number) =>
    api.get<Comment[]>(`/social/posts/${id}/comments`).then(r => r.data),

  addComment: (id: number, content: string) =>
    api.post<Comment>(`/social/posts/${id}/comments`, { content }).then(r => r.data),

  deleteComment: (postId: number, commentId: number) =>
    api.delete(`/social/posts/${postId}/comments/${commentId}`),

  getProfile: () => api.get<Profile>('/social/profile').then(r => r.data),

  updateProfile: (displayName?: string, avatar?: File) => {
    const form = new FormData()
    if (displayName !== undefined) form.append('display_name', displayName)
    if (avatar) form.append('avatar', avatar)
    return api.put<Profile>('/social/profile', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}
