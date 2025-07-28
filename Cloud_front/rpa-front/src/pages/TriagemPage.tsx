import {
  DataGrid,
  GridColDef,
  getGridStringOperators,
  getGridNumericOperators,
  getGridDateOperators,
  getGridBooleanOperators,
} from '@mui/x-data-grid';
import { ptBR } from '@mui/x-data-grid/locales';
import { Chip, IconButton, Tooltip, Paper, Box, Typography } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import CloseIcon from '@mui/icons-material/Close';
import DoneIcon from '@mui/icons-material/Done';
import { useFetch } from '../hooks/useFetch';
import { useEffect, useState, useRef } from 'react';

// Interface para tipar os dados da triagem.
interface ITriagem {
  os_id: number;
  pasta: string;
  triagem_status: 'Pendente' | 'processando' | 'falha' | 'Triada';
  tomados_status: 'Concluído' | 'Processando' | 'Pendente' | 'Nenhum';
  gerou_extrato: boolean;
  updated_at: string;
}

// Operadores de filtro para simplificar a UI
const stringContainsOperator = getGridStringOperators().filter((op) => op.value === 'contains');
const stringEqualsOperator = getGridStringOperators().filter((op) => op.value === 'equals');
const numericEqualsOperator = getGridNumericOperators().filter((op) => op.value === '=');
const dateIsOperator = getGridDateOperators().filter((op) => op.value === 'is');
const booleanIsOperator = getGridBooleanOperators().filter((op) => op.value === 'is');

/* ---------- baixa ZIP com todos os .txt ---------- */
const downloadZip = async (pasta: string) => {
  try {
    const resp = await fetch(`http://localhost:8000/tomados/${encodeURIComponent(pasta)}`);
    if (!resp.ok) {
      console.error("Não foi possível gerar o ZIP: ", resp.statusText);
      alert("Não foi possível gerar o ZIP: " + resp.statusText);
      return;
    }
    if (resp.headers.get('Content-Type') !== 'application/zip') {
      console.error("A resposta não contém um arquivo ZIP.");
      alert("A resposta não contém um arquivo ZIP.");
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${pasta}_TXT.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Erro ao tentar baixar o arquivo ZIP:", error);
    alert("Ocorreu um erro ao tentar baixar o arquivo.");
  }
};

/* ---------- colunas ---------- */
const cols: GridColDef<ITriagem>[] = [
  { field: 'os_id', headerName: 'OS', width: 80, hideable: false, filterOperators: numericEqualsOperator },
  { field: 'pasta', headerName: 'Apelido', flex: 1, minWidth: 150, hideable: false, filterOperators: stringContainsOperator },
  {
    field: 'triagem_status',
    headerName: 'Triagem',
    width: 110,
    hideable: false,
    filterOperators: stringEqualsOperator,
    renderCell: ({ value }) => {
      const map: Record<string, { label: string; color: 'default' | 'info' | 'error' | 'success' }> = {
        Pendente: { label: 'Pendente', color: 'default' },
        processando: { label: 'Processando', color: 'info' },
        falha: { label: 'Erro', color: 'error' },
        Triada: { label: 'Triada', color: 'success' },
      };
      const { label, color } = map[value] ?? { label: String(value), color: 'default' };
      return <Chip label={label} color={color} size="small" />;
    },
  },
  {
    field: 'tomados_status',
    headerName: 'Tomados',
    width: 120,
    align: 'center',
    headerAlign: 'center',
    sortable: false,
    filterable: false,
    renderCell: ({ value, row }) => {
      if (value === 'Concluído') {
        return (
          <Tooltip title="Baixar GERAL.txt">
            <IconButton size="small" onClick={() => downloadZip(`${row.os_id}-${row.pasta}`)}>
              <DownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        );
      }
      if (value === 'Processando') {
        return (
          <Tooltip title="Tomados em processamento…">
            <HourglassEmptyIcon sx={{ color: 'warning.main' }} fontSize="small" />
          </Tooltip>
        );
      }
      if (value === 'Pendente') {
        return <Chip label="Pendente" size="small" />;
      }
      return <CloseIcon color="disabled" fontSize="small" />;
    },
  },
  {
    field: 'gerou_extrato',
    headerName: 'Extrato',
    width: 90,
    align: 'center',
    headerAlign: 'center',
    type: 'boolean',
    filterOperators: booleanIsOperator,
    renderCell: ({ value }) => value ? <DoneIcon color="success" fontSize="small" /> : <CloseIcon color="disabled" fontSize="small" />,
  },
  {
    field: 'updated_at',
    headerName: 'Atualizado',
    flex: 1,
    minWidth: 140,
    type: 'dateTime',
    hideable: false,
    filterOperators: dateIsOperator,
    valueGetter: (value) => value && new Date(value),
    renderCell: ({ value }) => value ? (value as Date).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '',
  },
];

/* ---------- componente ---------- */
export default function TriagemPage() {
  const [refreshFlag, setRefreshFlag] = useState(0);
  const isInitialLoad = useRef(true);

  // Usando o hook da forma correta, passando o tipo do objeto individual.
  const { data, loading, error } =
    useFetch<ITriagem>(`http://localhost:8000/triagem?rf=${refreshFlag}`);

  useEffect(() => {
    document.title = 'Triagem';
    const intervalId = setInterval(() => {
      setRefreshFlag((prevFlag) => prevFlag + 1);
    }, 20_000); // Atualiza a cada 20 segundos

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
        Triagem
      </Typography>
      <Paper sx={{ p: 2, width: '100%', borderRadius: '12px', boxShadow: 3, overflow: 'hidden' }}>
        <DataGrid
          autoHeight
          rows={data}
          loading={loading && isInitialLoad.current}
          columns={cols}
          getRowId={row => row.os_id}
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
              borderColor: '#f1c40f'
            },
            '& .MuiDataGrid-row:nth-of-type(odd)': { backgroundColor: 'grey.50' },
            '& .MuiDataGrid-row:hover': { backgroundColor: 'rgba(241, 196, 15, 0.1)' },
            '& .MuiDataGrid-cell:focus-within': { outline: '1px solid #f1c40f', outlineOffset: '-1px' },
            '& .MuiDataGrid-footerContainer': { borderTop: '1px solid', borderColor: 'grey.300' }
          }}
        />
      </Paper>
    </Box>
  );
}
