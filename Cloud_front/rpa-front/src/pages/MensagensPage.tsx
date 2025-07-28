import { useEffect, useState } from 'react';
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
} from '@mui/material';

/* ---------- tipos ---------- */
type Mensagem = {
  id: number;
  os: number;
  apelido: string;
  assunto: string;
  descricao: string;
  lido: boolean;
};

/* ---------- operadores de filtro ---------- */
const stringContainsOperator = getGridStringOperators().filter(
  (op) => op.value === 'contains'
);
const numericEqualsOperator = getGridNumericOperators().filter(
  (op) => op.value === '='
);

export default function MensagensPage() {
  const [msgs, setMsgs] = useState<Mensagem[]>([]);
  const [displayedMsgs, setDisplayedMsgs] = useState<Mensagem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState<'todas' | 'nao_lidas' | 'lidas'>(
    'nao_lidas'
  );

  useEffect(() => {
    document.title = 'Mensagens dos Clientes';
  }, []);

  /* ---------- carregar mensagens ---------- */
  useEffect(() => {
    api
      .get<Array<any>>('/mensagens')
      .then(({ data }) => {
        const mensagensComConteudo = data.filter(
          (m) => m.apelido || m.assunto || m.descricao
        );

        const inicial: Mensagem[] = mensagensComConteudo.map((m) => ({
          id: m.os_id,
          os: m.os_id,
          apelido: m.apelido,
          assunto: m.assunto,
          descricao: m.descricao,
          lido: Boolean(m.lido),
        }));
        setMsgs(inicial);
      })
      .catch((err) => console.error('Erro ao carregar mensagens:', err))
      .finally(() => setLoading(false));
  }, []);

  /* ---------- filtro local ---------- */
  useEffect(() => {
    let filtradas: Mensagem[];
    if (filtro === 'lidas') filtradas = msgs.filter((m) => m.lido);
    else if (filtro === 'nao_lidas') filtradas = msgs.filter((m) => !m.lido);
    else filtradas = msgs;

    setDisplayedMsgs(filtradas);
  }, [msgs, filtro]);

  /* ---------- marcar como lida ---------- */
  const handleLidoChange = (id: number) => {
    setMsgs((ms) => ms.map((m) => (m.id === id ? { ...m, lido: true } : m)));

    api
      .post(`/mark_lido/${id}`, { lido: true })
      .catch((err) => console.error('Erro ao atualizar status:', err));
  };

  /* ---------- colunas ---------- */
  const cols: GridColDef[] = [
    {
      field: 'lido',
      headerName: '',
      width: 60,
      sortable: false,
      hideable: false,
      filterable: false,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => (
        <Box
          onClick={() => handleLidoChange(params.id as number)}
          sx={{
            cursor: 'pointer',
            width: 12,
            height: 12,
            borderRadius: '50%',
            transition: 'all 0.2s ease',
            backgroundColor: params.value ? 'transparent' : '#f1c40f',
            border: params.value ? '2px solid #ccc' : '2px solid #f1c40f',
          }}
        />
      ),
    },
    { field: 'os', headerName: 'OS', width: 90, filterOperators: numericEqualsOperator },
    { field: 'apelido', headerName: 'Empresa', width: 160, filterOperators: stringContainsOperator },
    { field: 'assunto', headerName: 'Assunto', width: 200, filterOperators: stringContainsOperator },
    { field: 'descricao', headerName: 'Descrição', flex: 1, minWidth: 250, filterOperators: stringContainsOperator },
  ];

  if (loading) return <p>Carregando…</p>;

  return (
    <Box>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <Typography variant="h4" component="h1">
          Mensagens dos Clientes
        </Typography>
        <ToggleButtonGroup
          value={filtro}
          exclusive
          onChange={(_, v) => v && setFiltro(v as any)}
          aria-label="filtro de mensagens"
        >
          <ToggleButton
            value="nao_lidas"
            aria-label="não lidas"
            sx={{
              textTransform:'none',
              fontWeight:500,
              '&.Mui-selected':{
                backgroundColor:'rgba(241,196,15,.2)',
                color:'#b28d0b',
                fontWeight:700,
                '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' }
              },
            }}
          >
            Não Lidas
          </ToggleButton>
          <ToggleButton
            value="lidas"
            aria-label="lidas"
            sx={{
              textTransform:'none',
              fontWeight:500,
              '&.Mui-selected':{
                backgroundColor:'rgba(241,196,15,.2)',
                color:'#b28d0b',
                fontWeight:700,
                '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' }
              },
            }}
          >
            Lidas
          </ToggleButton>
          <ToggleButton
            value="todas"
            aria-label="todas"
            sx={{
              textTransform:'none',
              fontWeight:500,
              '&.Mui-selected':{
                backgroundColor:'rgba(241,196,15,.2)',
                color:'#b28d0b',
                fontWeight:700,
                '&:hover':{ backgroundColor:'rgba(241,196,15,.3)' }
              },
            }}
          >
            Todas
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Paper sx={{ p:2, width:'100%', borderRadius:'12px', boxShadow:3, overflow:'hidden' }}>
        <DataGrid
          autoHeight
          rows={displayedMsgs}
          columns={cols}
          getRowHeight={() => 'auto'}
          getRowClassName={(p) => (p.row.lido ? 'mensagem-lida' : '')}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination:{ paginationModel:{ pageSize:10 } } }}
          disableRowSelectionOnClick
          disableColumnSelector
          localeText={ptBR.components.MuiDataGrid.defaultProps.localeText}
          slotProps={{
            filterPanel:{
              filterFormProps:{
                operatorInputProps:{ sx:{ display:'none' } }
              }
            }
          }}
          sx={{
            border:0,
            '& .mensagem-lida':{ opacity:0.7 },
            '& .MuiDataGrid-columnHeaders':{
              backgroundColor:'grey.100',
              color:'grey.800',
              fontWeight:'bold',
              borderBottom:'2px solid',
              borderColor:'#f1c40f',
              fontSize:'0.8rem',
            },
            '& .MuiDataGrid-cell':{
              borderRight:'none',
              whiteSpace:'normal',
              wordWrap:'break-word',
              lineHeight:1.5,
              py:1.5,
              display:'flex',
              alignItems:'center',
              fontSize:'0.875rem',
            },
            '& .MuiDataGrid-row:hover':{
              backgroundColor:'rgba(241,196,15,.1)',
            },
            '& .MuiDataGrid-cell:focus-within':{
              outline:'1px solid #f1c40f',
              outlineOffset:'-1px',
            },
            '& .MuiDataGrid-footerContainer':{
              borderTop:'1px solid',
              borderColor:'grey.300',
            },
          }}
        />
      </Paper>
    </Box>
  );
}
