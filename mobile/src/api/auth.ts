import client from './client';

export interface LoginResponse {
  access_token: string;
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const { data } = await client.post<LoginResponse>('/auth/login', { email, password });
    return data;
  },

  register: async (email: string, password: string): Promise<LoginResponse> => {
    const { data } = await client.post<LoginResponse>('/auth/register', {
      email,
      password,
      plan: 'freemium',
    });
    return data;
  },
};
