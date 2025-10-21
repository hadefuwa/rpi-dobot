import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.get('/auth/me');
        if (response.data.user) {
          setUser(response.data.user);
        }
      } catch (error) {
        // User not authenticated
        console.log('Not authenticated');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (username, password) => {
    try {
      setIsLoading(true);
      const response = await api.post('/auth/login', { username, password });
      
      if (response.data.success) {
        setUser(response.data.user);
        toast.success(`Welcome back, ${response.data.user.username}!`);
        return true;
      }
    } catch (error) {
      const message = error.response?.data?.error || 'Login failed';
      toast.error(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      toast.success('Logged out successfully');
    }
  }, []);

  return {
    user,
    login,
    logout,
    isLoading
  };
}
