import {
  DataGrid,
  GridColDef,
  getGridStringOperators,
  getGridNumericOperators,
  getGridDateOperators,
} from '@mui/x-data-grid';
import { ptBR } from '@mui/x-data-grid/locales';
import { Chip, Tooltip, Paper, Box, Typography } from '@mui/material';
import { useFetch } from '../hooks/useFetch';
import { useEffect } from 'react';

// Operadores de filtro (sem alterações)
const stringContainsOperator = getGridStringOperators().filter(
  (operator) => operator.value === 'contains',
);
const stringEqualsOperator = getGridStringOperators().filter(
  (operator) => operator.value === 'equals',
);
const numericEqualsOperator = getGridNumericOperators().filter(
  (operator) => operator.value === '=',
);
const dateIsOperator = getGridDateOperators().filter(
    (operator) => operator.value === 'is',
);

// Definição de colunas (sem alterações, a versão com valueGetter está correta)
const cols: GridColDef[] = [
  {
    field: 'os_id',
    headerName: 'OS',
    width: 70,
    hideable: false,
    filterOperators: numericEqualsOperator,
  },
  {
    field: 'apelido',
    headerName: 'Apelido',
    flex: 1,
    minWidth: 140,
    hideable: false,
    filterOperators: stringContainsOperator,
  },
  {
    field: 'status',
    headerName: 'Status',
    width: 110,
    hideable: false,
    filterOperators: stringEqualsOperator,
    renderCell: ({ value }) => {
      let label = value;
      let color: 'success' | 'error' | 'warning' | 'default' = 'default';
      let tip   = '';
      switch (value) {
        case 'sucesso':
          label = 'Sucesso';
          color = 'success';
          tip   = 'Download concluído';
          break;
        case 'falha':
          label = 'Não existe';
          color = 'warning';
          tip   = 'OS não encontrada';
          break;
        default:
          label = value;
      }
      return (
        <Tooltip title={tip}>
          <Chip label={label} color={color as any} size="small" />
        </Tooltip>
      );
   },
},
  {
    field: 'tentativas',
    headerName: 'Tentativas',
    width: 90,
    hideable: false,
    type: 'number',
    filterOperators: numericEqualsOperator,
  },
  {
    field: 'anexos_total',
    headerName: 'Qtde Anexos',
    width: 110,
    hideable: false,
    type: 'number',
    filterOperators: numericEqualsOperator,
  },
  {
    field: 'created_at',
    headerName: 'Criado',
    flex: 1,
    minWidth: 135,
    hideable: false,
    type: 'dateTime',
    valueGetter: (value) => value && new Date(value as string),
    filterOperators: dateIsOperator,
    renderCell: ({ value }) =>
      value
        ? (value as Date).toLocaleString('pt-BR', {
            dateStyle: 'short',
            timeStyle: 'short',
          })
        : '',
  },
  {
    field: 'updated_at',
    headerName: 'Atualizado',
    flex: 1,
    minWidth: 135,
    hideable: false,
    type: 'dateTime',
    valueGetter: (value) => value && new Date(value as string),
    filterOperators: dateIsOperator,
    renderCell: ({ value }) =>
      value
        ? (value as Date).toLocaleString('pt-BR', {
            dateStyle: 'short',
            timeStyle: 'short',
          })
        : '',
  },
];

export default function DownloadsPage() {
  const { data, loading, error } = useFetch<any>('http://localhost:8000/downloads');
     useEffect(() => {
    document.title = 'Downloads';
  }, []);

  if (loading) return <div>Carregando…</div>;
  if (error)   return <div>{error}</div>;

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Downloads
      </Typography>
      <Paper sx={{ p: 2, width: '100%', borderRadius: '12px', boxShadow: 3, overflow: 'hidden' }}>
        <DataGrid
          autoHeight
          rows={data || []}
          columns={cols}
          getRowId={row => row.os_id}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 10 },
            },
          }}
          disableRowSelectionOnClick
          disableColumnSelector
          localeText={ptBR.components.MuiDataGrid.defaultProps.localeText}

          // ===================================================================
          // ESTRUTURA CORRIGIDA
          // ===================================================================
          slotProps={{
            filterPanel: {
              // Adicionamos o nível 'filterFormProps' que faltava
              filterFormProps: {
                operatorInputProps: {
                  sx: {
                    display: 'none',
                  },
                },
              },
            },
          }}
          // ===================================================================

          sx={{
            border: 0,
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: 'grey.100',
              color: 'grey.800',
              fontWeight: 'bold',
              borderBottom: '2px solid',
              borderColor: '#f1c40f'
            },
            '& .MuiDataGrid-cell': {
              borderRight: 'none',
            },
            '& .MuiDataGrid-row:nth-of-type(odd)': {
              backgroundColor: 'grey.50',
            },
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'rgba(241, 196, 15, 0.1)',
            },
            '& .MuiDataGrid-cell:focus-within': {
              outline: '1px solid #f1c40f',
              outlineOffset: '-1px',
            },
            '& .MuiDataGrid-footerContainer': {
              borderTop: '1px solid',
              borderColor: 'grey.300'
            }
          }}
        />
      </Paper>
    </Box>
  );
}