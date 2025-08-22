import { useEffect, useState, useRef } from 'react';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';

import {
  DataGrid,
  GridColDef,
  getGridStringOperators,
  getGridNumericOperators,
} from '@mui/x-data-grid';
import { ptBR } from '@mui/x-data-grid/locales';
import {
  Paper,
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Tooltip, // CORREÇÃO: Importando o Tooltip que estava faltando.
} from '@mui/material';

/* ---------- Interfaces de Tipagem ---------- */
// Tipo para os dados brutos da API
interface RawMensagem {
  os_id: number;
  apelido: string;
  assunto: string;
  descricao: string;
  lido: any;
}

// Tipo para os dados já tratados e usados no componente
interface Mensagem {
  id: number;
  os: number;
  apelido: string;
  assunto: string;
  descricao: string;
  lido: boolean;
}

/* ---------- Operadores de Filtro ---------- */
const stringContainsOperator = getGridStringOperators().filter((op) => op.value === 'contains');
const numericEqualsOperator = getGridNumericOperators().filter((op) => op.value === '=');

export default function MensagensPage() {
  const [msgs, setMsgs] = useState<Mensagem[]>([]);
  const [displayedMsgs, setDisplayedMsgs] = useState<Mensagem[]>([]);
  const [filtro, setFiltro] = useState<'todas' | 'nao_lidas' | 'lidas'>('nao_lidas');

  const [refreshFlag, setRefreshFlag] = useState(0);
  const isInitialLoad = useRef(true);

  // 1. Usando o hook useFetch para buscar os dados brutos
  const { data: rawMsgs, loading, error } =
    useFetch<RawMensagem>(`/mensagens?rf=${refreshFlag}`);

  // 2. Efeito para o título da página e para o intervalo de atualização
  useEffect(() => {
    document.title = 'Mensagens dos Clientes';
    const intervalId = setInterval(() => {
      setRefreshFlag((prevFlag) => prevFlag + 1);
    }, 30_000); // Atualiza a cada 30 segundos

    return () => clearInterval(intervalId);
  }, []);

  // 3. Efeito para transformar os dados brutos em dados tratados
  useEffect(() => {
    if (rawMsgs && Array.isArray(rawMsgs)) {
      const mensagensComConteudo = rawMsgs.filter(
        (m) => m.apelido || m.assunto || m.descricao
      );

      const mappedMsgs: Mensagem[] = mensagensComConteudo.map((m) => ({
        id: m.os_id,
        os: m.os_id,
        apelido: m.apelido,
        assunto: m.assunto,
        descricao: m.descricao,
        lido: Boolean(m.lido),
      }));
      setMsgs(mappedMsgs);
    }
  }, [rawMsgs]);

  // 4. Efeito para aplicar o filtro local (Lidas/Não Lidas/Todas)
  useEffect(() => {
    let filtradas: Mensagem[];
    if (filtro === 'lidas') filtradas = msgs.filter((m) => m.lido);
    else if (filtro === 'nao_lidas') filtradas = msgs.filter((m) => !m.lido);
    else filtradas = msgs;

    setDisplayedMsgs(filtradas);
  }, [msgs, filtro]);

  // Efeito para o spinner de carregamento inicial
  useEffect(() => {
    if (!loading) {
      isInitialLoad.current = false;
    }
  }, [loading]);

  /* ---------- Marcar como lida (lógica mantida) ---------- */
  const handleLidoChange = (id: number) => {
    // Optimistic update
    setMsgs((currentMsgs) =>
      currentMsgs.map((m) => (m.id === id ? { ...m, lido: true } : m))
    );
    // API call
    api.post(`/mark_lido/${id}`, { lido: true })
       .catch((err) => console.error('Erro ao atualizar status:', err));
  };

  /* ---------- Colunas (lógica mantida) ---------- */
  const cols: GridColDef<Mensagem>[] = [
    {
      field: 'lido', headerName: '', width: 60, sortable: false, hideable: false, filterable: false, align: 'center', headerAlign: 'center',
      renderCell: (params) => (
        <Tooltip title={params.value ? "Lida" : "Marcar como lida"}>
          <Box
            onClick={() => !params.value && handleLidoChange(params.id as number)}
            sx={{
              cursor: params.value ? 'default' : 'pointer',
              width: 12, height: 12, borderRadius: '50%',
              transition: 'all 0.2s ease',
              backgroundColor: params.value ? 'transparent' : '#f1c40f',
              border: params.value ? '2px solid #ccc' : '2px solid #f1c40f',
            }}
          />
        </Tooltip>
      ),
    },
    { field: 'os', headerName: 'OS', width: 90, filterOperators: numericEqualsOperator },
    { field: 'apelido', headerName: 'Empresa', width: 160, filterOperators: stringContainsOperator },
    { field: 'assunto', headerName: 'Assunto', width: 200, filterOperators: stringContainsOperator },
    { field: 'descricao', headerName: 'Descrição', flex: 1, minWidth: 250, filterOperators: stringContainsOperator },
  ];

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">Ocorreu um erro ao buscar as mensagens.</Typography>
        <Typography variant="body1">{String(error)}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <Typography variant="h4" component="h1">
          Mensagens dos Clientes
        </Typography>
        <ToggleButtonGroup
          value={filtro}
          exclusive
          onChange={(_, v) => v && setFiltro(v)}
          aria-label="filtro de mensagens"
        >
          <ToggleButton value="nao_lidas" aria-label="não lidas" sx={{ textTransform:'none', fontWeight:500, '&.Mui-selected':{ backgroundColor:'rgba(241,196,15,.2)', color:'#b28d0b', fontWeight:700, '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' } } }}>Não Lidas</ToggleButton>
          <ToggleButton value="lidas" aria-label="lidas" sx={{ textTransform:'none', fontWeight:500, '&.Mui-selected':{ backgroundColor:'rgba(241,196,15,.2)', color:'#b28d0b', fontWeight:700, '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' } } }}>Lidas</ToggleButton>
          <ToggleButton value="todas" aria-label="todas" sx={{ textTransform:'none', fontWeight:500, '&.Mui-selected':{ backgroundColor:'rgba(241,196,15,.2)', color:'#b28d0b', fontWeight:700, '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' } } }}>Todas</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Paper sx={{ p:2, width:'100%', borderRadius:'12px', boxShadow:3, overflow:'hidden' }}>
        <DataGrid
          autoHeight
          rows={displayedMsgs}
          loading={loading && isInitialLoad.current}
          columns={cols}
          getRowHeight={() => 'auto'}
          getRowClassName={(p) => (p.row.lido ? 'mensagem-lida' : '')}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination:{ paginationModel:{ pageSize:10 } } }}
          disableRowSelectionOnClick
          disableColumnSelector
          localeText={ptBR.components.MuiDataGrid.defaultProps.localeText}
          slotProps={{ filterPanel:{ filterFormProps:{ operatorInputProps:{ sx:{ display:'none' } } } } }}
          sx={{
            border:0,
            '& .mensagem-lida':{ opacity:0.7, fontStyle: 'italic' },
            '& .MuiDataGrid-columnHeaders':{ backgroundColor:'grey.100', color:'grey.800', fontWeight:'bold', borderBottom:'2px solid', borderColor:'#f1c40f', fontSize:'0.8rem' },
            '& .MuiDataGrid-cell':{ borderRight:'none', whiteSpace:'normal', wordWrap:'break-word', lineHeight:1.5, py:1.5, display:'flex', alignItems:'center', fontSize:'0.875rem' },
            '& .MuiDataGrid-row:hover':{ backgroundColor:'rgba(241,196,15,.1)' },
            '& .MuiDataGrid-cell:focus-within':{ outline:'1px solid #f1c40f', outlineOffset:'-1px' },
            '& .MuiDataGrid-footerContainer':{ borderTop:'1px solid', borderColor:'grey.300' },
          }}
        />
      </Paper>
    </Box>
  );
}
