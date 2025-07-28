import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface Props {
  children: ReactNode;
}

export default function PrivateRoute({ children }: Props) {
  const { token } = useAuth();
  return token ? <>{children}</> : <Navigate to="/login" />;
}
