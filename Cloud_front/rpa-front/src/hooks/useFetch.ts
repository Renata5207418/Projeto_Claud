import { useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { api } from '../services/api';

export function useFetch<T = any>(endpoint: string) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let cancel = false;
    setLoading(true);

    api
      .get<T[]>(endpoint, { withCredentials: true })
      .then(res => !cancel && setData(res.data))
      .catch((err: AxiosError) => {
        console.error(err);
        if (!cancel) setError('Erro ao carregar dados');
      })
      .finally(() => !cancel && setLoading(false));

    return () => { cancel = true; };
  }, [endpoint]);

  return { data, loading, error };
}
