import client, { API_BASE_URL } from './client';

export interface Author {
  id: number;
  display_name: string;
  avatar_url: string | null;
}

export interface Post {
  id: number;
  content: string;
  image_url: string | null;
  created_at: string;
  likes_count: number;
  comments_count: number;
  user_liked: boolean;
  author: Author;
}

export interface Comment {
  id: number;
  content: string;
  created_at: string;
  author: Author;
}

export interface Profile {
  id: number;
  email: string;
  display_name: string;
  avatar_url: string | null;
  plan: string;
}

export const socialApi = {
  getFeed: async (skip = 0, limit = 20): Promise<Post[]> => {
    const { data } = await client.get<Post[]>('/social/feed', { params: { skip, limit } });
    return data;
  },

  createPost: async (content: string, imageUri?: string): Promise<Post> => {
    const form = new FormData();
    form.append('content', content);
    if (imageUri) {
      const filename = imageUri.split('/').pop() ?? 'photo.jpg';
      const ext = filename.split('.').pop()?.toLowerCase() ?? 'jpg';
      const mimeType = ext === 'png' ? 'image/png' : 'image/jpeg';
      form.append('image', { uri: imageUri, name: filename, type: mimeType } as any);
    }
    const { data } = await client.post<Post>('/social/posts', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  deletePost: async (postId: number): Promise<void> => {
    await client.delete(`/social/posts/${postId}`);
  },

  toggleLike: async (postId: number): Promise<{ liked: boolean; likes_count: number }> => {
    const { data } = await client.post(`/social/posts/${postId}/like`);
    return data;
  },

  getComments: async (postId: number): Promise<Comment[]> => {
    const { data } = await client.get<Comment[]>(`/social/posts/${postId}/comments`);
    return data;
  },

  addComment: async (postId: number, content: string): Promise<Comment> => {
    const { data } = await client.post<Comment>(`/social/posts/${postId}/comments`, { content });
    return data;
  },

  deleteComment: async (postId: number, commentId: number): Promise<void> => {
    await client.delete(`/social/posts/${postId}/comments/${commentId}`);
  },

  getProfile: async (): Promise<Profile> => {
    const { data } = await client.get<Profile>('/social/profile');
    return data;
  },

  updateProfile: async (displayName?: string, avatarUri?: string): Promise<Profile> => {
    const form = new FormData();
    if (displayName !== undefined) form.append('display_name', displayName);
    if (avatarUri) {
      const filename = avatarUri.split('/').pop() ?? 'avatar.jpg';
      const ext = filename.split('.').pop()?.toLowerCase() ?? 'jpg';
      const mimeType = ext === 'png' ? 'image/png' : 'image/jpeg';
      form.append('avatar', { uri: avatarUri, name: filename, type: mimeType } as any);
    }
    const { data } = await client.put<Profile>('/social/profile', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  getImageUrl: (path: string | null): string | null => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    return `${API_BASE_URL}${path}`;
  },
};
