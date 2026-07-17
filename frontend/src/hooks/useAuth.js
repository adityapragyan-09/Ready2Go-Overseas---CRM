import { useAuthContext } from '../context/AuthContext';

/**
 * Custom hook to access authentication state and handlers
 */
export const useAuth = () => {
  const context = useAuthContext();
  return {
    user: context.user,
    loading: context.loading,
    login: context.login,
    logout: context.logout,
    updateUser: context.updateUser,
    isAuthenticated: context.isAuthenticated,
    mustChangePassword: context.mustChangePassword,
  };
};
