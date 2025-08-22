import {
  DataGrid,
  GridColDef,
  getGridStringOperators,
  getGridNumericOperators,
  getGridDateOperators,
  getGridBooleanOperators,
} from '@mui/x-data-grid';
import { ptBR } from '@mui/x-data-grid/locales';
import {
  Chip, IconButton, Tooltip, Paper, Box, Typography,
  ToggleButtonGroup, ToggleButton
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import CloseIcon from '@mui/icons-material/Close';
import DoneIcon from '@mui/icons-material/Done';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { useEffect, useState, useRef, useMemo, useCallback } from 'react';

/* ---------- Tipagem ---------- */
interface ITriagem {
  os_id: number;
  pasta: string;
  triagem_status: 'Pendente' | 'processando' | 'falha' | 'Triada';
  tomados_status: 'Concluído' | 'Processando' | 'Pendente' | 'Nenhum';
  gerou_extrato: boolean;
  updated_at: string;
  ok_usuario?: boolean;
}

/* ---------- Operadores ---------- */
const stringContainsOperator = getGridStringOperators().filter(op => op.value === 'contains');
const stringEqualsOperator   = getGridStringOperators().filter(op => op.value === 'equals');
const numericEqualsOperator  = getGridNumericOperators().filter(op => op.value === '=');
const dateIsOperator         = getGridDateOperators().filter(op => op.value === 'is');
const booleanIsOperator      = getGridBooleanOperators().filter(op => op.value === 'is');

/* ---------- Estilo Reutilizável para o Filtro ---------- */
const toggleButtonSx = {
  textTransform:'none',
  fontWeight: 500,
  '&.Mui-selected': {
    backgroundColor:'rgba(241, 196, 15, .2)',
    color:'#b28d0b',
    fontWeight: 700,
    '&:hover': {
      backgroundColor:'rgba(241, 196, 15, .3)'
    }
  }
};

// --- INÍCIO DA CORREÇÃO ---
// 1. Cria um objeto de localização personalizado, aproveitando o padrão ptBR
//    e substituindo apenas os textos do filtro booleano.
const customLocaleText = {
  ...ptBR.components.MuiDataGrid.defaultProps.localeText,
  filterValueAny: 'Ambos',
  filterValueTrue: 'Possui',
  filterValueFalse: 'Não Possui',
};
// --- FIM DA CORREÇÃO ---

/* ---------- baixa ZIP ---------- */
async function downloadZip(pasta: string) {
  try {
    const resp = await fetch(`http://10.0.0.78:8000/tomados/${encodeURIComponent(pasta)}`);
    if (!resp.ok || resp.headers.get('Content-Type') !== 'application/zip') {
      alert('Não foi possível gerar o ZIP.');
      return;
    }
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `${pasta}_TXT.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    alert('Erro ao baixar o arquivo.');
  }
}

/* ---------- Componente ---------- */
export default function TriagemPage() {
  const [refreshFlag, setRefreshFlag] = useState(0);
  const isInitialLoad = useRef(true);

  const { data, loading, error } =
    useFetch<ITriagem>(`http://10.0.0.78:8000/triagem?rf=${refreshFlag}`);

  const [filtroOk, setFiltroOk] = useState<'todas' | 'ok' | 'pendentes'>('pendentes');
  const [rowsState, setRowsState] = useState<ITriagem[]>([]);

  useEffect(() => {
    document.title = 'Triagem';
    const id = setInterval(() => setRefreshFlag(f => f + 1), 20_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (data) setRowsState(data);
    if (!loading) isInitialLoad.current = false;
  }, [data, loading]);

  const toggleOk = useCallback(async (row: ITriagem) => {
    const current = !!row.ok_usuario;
    setRowsState(r => r.map(x => x.os_id === row.os_id ? { ...x, ok_usuario: !current } : x));
    try {
      await api.post(`/mark_ok/${row.os_id}`, { ok: !current });
    } catch {
      setRowsState(r => r.map(x => x.os_id === row.os_id ? { ...x, ok_usuario: current } : x));
      alert('Não foi possível atualizar o status.');
    }
  }, []);

  const rowsFiltradas = useMemo(() => {
    if (filtroOk === 'ok')        return rowsState.filter(r => r.ok_usuario);
    if (filtroOk === 'pendentes') return rowsState.filter(r => !r.ok_usuario);
    return rowsState;
  }, [rowsState, filtroOk]);

  /* ---------- Colunas ---------- */
  const cols: GridColDef<ITriagem>[] = useMemo(() => [
    {
      field: 'ok_usuario',
      headerName: 'Verificado',
      width: 90,
      align: 'center',
      headerAlign: 'center',
      sortable: false,
      filterable: false,
      renderCell: ({ row }) => (
        <Tooltip title={row.ok_usuario ? 'Marcado como OK' : 'Marcar como OK'}>
          <IconButton size="small" onClick={() => toggleOk(row)}>
            {row.ok_usuario
              ? <CheckCircleIcon color="success" fontSize="small" />
              : <RadioButtonUncheckedIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
      ),
    },
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
          Pendente:    { label: 'Pendente',    color: 'default' },
          processando: { label: 'Processando', color: 'info'    },
          falha:       { label: 'Erro',        color: 'error'   },
          Triada:      { label: 'Triada',      color: 'success' },
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
      filterable: true,
      type: 'boolean',
      filterOperators: booleanIsOperator,
      valueGetter: (value) => value === 'Concluído',
      renderCell: ({ row }) => {
        if (row.tomados_status === 'Concluído') {
          return (
            <Tooltip title="Baixar GERAL.txt">
              <IconButton size="small" onClick={() => downloadZip(`${row.os_id}-${row.pasta}`)}>
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          );
        }
        if (row.tomados_status === 'Processando') {
          return (
            <Tooltip title="Tomados em processamento…">
              <HourglassEmptyIcon sx={{ color: 'warning.main' }} fontSize="small" />
            </Tooltip>
          );
        }
        if (row.tomados_status === 'Pendente') return <Chip label="Pendente" size="small" />;
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
      renderCell: ({ value }) => value
        ? <DoneIcon color="success" fontSize="small" />
        : <CloseIcon color="disabled" fontSize="small" />,
    },
    {
      field: 'updated_at',
      headerName: 'Atualizado',
      flex: 1,
      minWidth: 140,
      type: 'dateTime',
      hideable: false,
      filterOperators: dateIsOperator,
      valueGetter: v => v && new Date(v),
      renderCell: ({ value }) =>
        value ? (value as Date).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '',
    },
  ], [toggleOk]);

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">Ocorreu um erro ao buscar os dados.</Typography>
        <Typography variant="body1">{String(error)}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <Typography variant="h4" component="h1">Triagem</Typography>
        <ToggleButtonGroup
          value={filtroOk}
          exclusive
          onChange={(_, v) => v && setFiltroOk(v)}
          aria-label="filtro OK"
        >
          <ToggleButton value="pendentes" sx={toggleButtonSx}>Pendentes</ToggleButton>
          <ToggleButton value="ok"        sx={toggleButtonSx}>OK</ToggleButton>
          <ToggleButton value="todas"     sx={toggleButtonSx}>Todas</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Paper sx={{ p:2, width:'100%', borderRadius:'12px', boxShadow:3, overflow:'hidden' }}>
        <DataGrid
          autoHeight
          rows={rowsFiltradas}
          loading={loading && isInitialLoad.current}
          columns={cols}
          getRowId={row => row.os_id}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination:{ paginationModel:{ pageSize:10 } } }}
          disableRowSelectionOnClick
          disableColumnSelector
          // --- INÍCIO DA CORREÇÃO ---
          // 2. Utiliza o objeto de localização personalizado no DataGrid.
          localeText={customLocaleText}
          // --- FIM DA CORREÇÃO ---
          slotProps={{ filterPanel:{ filterFormProps:{ operatorInputProps:{ sx:{ display:'none' } } } } }}
          sx={{
            border:0,
            '& .MuiDataGrid-columnHeaders':{ backgroundColor:'grey.100', color:'grey.800', fontWeight:'bold', borderBottom:'2px solid', borderColor:'#f1c40f' },
            '& .MuiDataGrid-row:nth-of-type(odd)':{ backgroundColor:'grey.50' },
            '& .MuiDataGrid-row:hover':{ backgroundColor:'rgba(241,196,15,.1)' },
            '& .MuiDataGrid-cell:focus-within':{ outline:'1px solid #f1c40f', outlineOffset:'-1px' },
            '& .MuiDataGrid-footerContainer':{ borderTop:'1px solid', borderColor:'grey.300' }
          }}
        />
      </Paper>
    </Box>
  );
}
