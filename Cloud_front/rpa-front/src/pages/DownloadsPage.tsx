import {
  DataGrid,
  GridColDef,
  getGridStringOperators,
  getGridNumericOperators,
  getGridDateOperators,
} from '@mui/x-data-grid';
import { ptBR } from '@mui/x-data-grid/locales';
import { Chip, Tooltip, Paper, Box, Typography } from '@mui/material';
import { useFetch } from '../hooks/useFetch'; // Supondo que o hook useFetch exista
import { useEffect, useState, useRef } from 'react';

// Interface para tipar os dados dos downloads.
interface IDownload {
  os_id: number;
  apelido: string;
  status: 'sucesso' | 'falha' | 'aguardando' | 'pendente';
  tentativas: number;
  anexos_total: number;
  motivo?: string;
  created_at: string;
  updated_at: string;
}

/* ─── Operadores de Filtro ─────────────────────────────── */
const stringContainsOperator = getGridStringOperators().filter((op) => op.value === 'contains');
const stringEqualsOperator = getGridStringOperators().filter((op) => op.value === 'equals');
const numericEqualsOperator = getGridNumericOperators().filter((op) => op.value === '=');
const dateIsOperator = getGridDateOperators().filter((op) => op.value === 'is');

/* ─── Definição das Colunas ────────────────────────────────── */
const cols: GridColDef<IDownload>[] = [
  { field: 'os_id', headerName: 'OS', width: 70, hideable: false, filterOperators: numericEqualsOperator },
  { field: 'apelido', headerName: 'Apelido', flex: 1, minWidth: 140, hideable: false, filterOperators: stringContainsOperator },
  {
    field: 'status',
    headerName: 'Status',
    width: 180,
    type: 'singleSelect',
    hideable: false,
    filterOperators: stringEqualsOperator,
    valueOptions: [
        { value: 'sucesso', label: 'Sucesso' },
        { value: 'falha', label: 'Falha' },
        { value: 'aguardando', label: 'Aguardando' },
        { value: 'pendente', label: 'Pendente' }
    ],
    renderCell: ({ value, row }) => {
      let label = value;
      let color: 'success' | 'error' | 'warning' | 'default' = 'default';
      let tip = '';

      if (value === 'falha') {
        if (row.motivo && row.motivo.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().includes('excesso de anexos')) {
          label = 'Excesso de anexos';
          tip = 'A OS foi ignorada pois excede o limite de anexos permitido.';
          color = 'error';
        } else {
          label = 'OS não encontrada';
          tip = 'Não foi possível encontrar essa OS no portal após algumas tentativas.';
          color = 'warning';
        }
      } else if (value === 'sucesso') {
        label = 'Sucesso';
        color = 'success';
        tip = 'Download concluído';
      } else if (value === 'aguardando') {
        label = 'Aguardando';
        color = 'warning';
        tip = 'OS ainda não encontrada — aguardando nova tentativa';
      } else if (value === 'pendente') {
        label = 'Pendente';
        color = 'default';
        tip = 'Na fila de processamento';
      } else {
        label = String(value);
      }

      return (
        <Tooltip title={tip}>
          <Chip label={label} color={color} size="small" />
        </Tooltip>
      );
    },
  },
  { field: 'tentativas',   headerName: 'Tentativas',   width: 100, type: 'number', hideable: false, filterOperators: numericEqualsOperator },
  { field: 'anexos_total', headerName: 'Qtde Anexos', width: 115, type: 'number', hideable: false, filterOperators: numericEqualsOperator },
  {
    field: 'created_at',
    headerName: 'Criado',
    flex: 1,
    minWidth: 135,
    type: 'dateTime',
    hideable: false,
    valueGetter: (value) => value && new Date(value),
    filterOperators: dateIsOperator,
    renderCell: ({ value }) => value ? (value as Date).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '',
  },
  {
    field: 'updated_at',
    headerName: 'Atualizado',
    flex: 1,
    minWidth: 135,
    type: 'dateTime',
    hideable: false,
    valueGetter: (value) => value && new Date(value),
    filterOperators: dateIsOperator,
    renderCell: ({ value }) => value ? (value as Date).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '',
  },
];

/* ─── Componente Principal ─────────────────────────────── */
export default function DownloadsPage() {
  const [refreshFlag, setRefreshFlag] = useState(0);
  const isInitialLoad = useRef(true);

  // CORREÇÃO FINAL: Passamos apenas o tipo do *objeto* para o hook.
  // O hook useFetch<T> já retorna um T[], então useFetch<IDownload> retorna IDownload[].
  const { data, loading, error } =
    useFetch<IDownload>(`http://10.0.0.78:8000/downloads?rf=${refreshFlag}`);

  useEffect(() => {
    document.title = 'Downloads';
    const intervalId = setInterval(() => {
      setRefreshFlag((prevFlag) => prevFlag + 1);
    }, 20_000);

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!loading) {
      isInitialLoad.current = false;
    }
  }, [loading]);


  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          Ocorreu um erro ao buscar os dados.
        </Typography>
        <Typography variant="body1">{String(error)}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Downloads
      </Typography>

      <Paper sx={{ p: 2, width: '100%', borderRadius: '12px', boxShadow: 3, overflow: 'hidden' }}>
        <DataGrid
          autoHeight
          // Agora 'data' tem o tipo correto (IDownload[]) e pode ser usado diretamente.
          rows={data}
          loading={loading && isInitialLoad.current}
          columns={cols}
          getRowId={(row) => row.os_id}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          disableRowSelectionOnClick
          disableColumnSelector
          localeText={ptBR.components.MuiDataGrid.defaultProps.localeText}
          slotProps={{
            filterPanel: {
              filterFormProps: {
                operatorInputProps: { sx: { display: 'none' } },
              },
            },
          }}
          sx={{
            border: 0,
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: 'grey.100',
              color: 'grey.800',
              fontWeight: 'bold',
              borderBottom: '2px solid',
              borderColor: '#f1c40f',
            },
            '& .MuiDataGrid-row:nth-of-type(odd)': { backgroundColor: 'grey.50' },
            '& .MuiDataGrid-row:hover': { backgroundColor: 'rgba(241, 196, 15, 0.1)' },
            '& .MuiDataGrid-cell:focus-within': { outline: '1px solid #f1c40f', outlineOffset: '-1px' },
            '& .MuiDataGrid-footerContainer': { borderTop: '1px solid', borderColor: 'grey.300' },
          }}
        />
      </Paper>
    </Box>
  );
}
