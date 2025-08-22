import { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  Box, Card, CardContent, Typography, Chip, TextField, Button, Container,
  CircularProgress, Stack, Fade, Avatar
} from '@mui/material';
import { green, amber, red, grey } from '@mui/material/colors';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import DownloadIcon from '@mui/icons-material/Download';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';
dayjs.locale('pt-br');

// --- Tipos e Constantes ---
type WorkerState = 'running' | 'idle' | 'down';
type Worker = { state: WorkerState; age: number | null; msg: string };

const API_BASE_URL = 'http://10.0.0.78:8000';
const WORKER_KEYS = ['cloud1', 'cloud2', 'cloud3'];
const FETCH_INTERVAL = 15000;

// --- Card de Status (igual ao seu) ---
interface StatusCardProps { workerName: string; workerData: Worker }
function StatusCard({ workerName, workerData }: StatusCardProps) {
  const palette = {
    running: { label:'OPERANDO',     Icon:CloudDoneIcon,       chip:'success', avatar:green[50], icon:green[600] },
    idle:    { label:'PROCESSANDO',  Icon:HourglassEmptyIcon,  chip:'warning', avatar:amber[50], icon:amber[600] },
    down:    { label:'FORA DO AR',   Icon:CloudOffIcon,        chip:'error',   avatar:red[50],   icon:red[600] },
    default: { label:'DESCONHECIDO', Icon:CloudOffIcon,        chip:'default', avatar:grey[100], icon:grey[500] }
  } as const;

  const { label, Icon, chip, avatar, icon } = palette[workerData.state] ?? palette.default;

  return (
    <Card variant="outlined" sx={{
      borderRadius:4, borderColor:'grey.200', boxShadow:'0 4px 12px rgba(0,0,0,.05)',
      transition:'transform .3s, box-shadow .3s', height:'100%', display:'flex', flexDirection:'column',
      '&:hover':{ transform:'translateY(-4px)', boxShadow:'0 8px 24px rgba(0,0,0,.1)' }
    }}>
      <CardContent sx={{ display:'flex', flexDirection:'column', flexGrow:1, p:3 }}>
        <Stack direction="row" spacing={2} alignItems="center" mb={2}>
          <Avatar sx={{ bgcolor:avatar, width:48, height:48 }}>
            <Icon sx={{ color:icon, fontSize:28 }} />
          </Avatar>
          <Typography variant="h6" fontWeight={600}>{workerName.toUpperCase()}</Typography>
        </Stack>

        <Chip label={label} color={chip as any} size="small"
              sx={{ fontWeight:500, alignSelf:'flex-start', mb:2 }} />

        <Typography variant="body2" color="text.secondary" sx={{ flexGrow:1, minHeight:40 }}>
          {workerData.msg || 'Nenhuma mensagem de status.'}
        </Typography>

        {workerData.age !== null && (
          <Typography variant="caption" color="text.secondary" sx={{ mt:2, textAlign:'right' }}>
            Atualizado há {workerData.age}s
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

// --- Página Principal ---
export default function CloudStatusDashboard() {
  const [status, setStatus] = useState<Record<string, Worker> | null>(null);
  const [exportMonth, setExportMonth] = useState<string>(dayjs().format('YYYY-MM'));

  useEffect(() => {
    document.title = 'Status Cloud';

    const fetchStatus = () => {
      api                                            // 👈 usa Axios em vez de fetch
        .get<Record<string, Worker>>('/status', { withCredentials:true })
        .then(res => setStatus(res.data))
        .catch(console.error);
    };

    fetchStatus();
    const id = setInterval(fetchStatus, FETCH_INTERVAL);
    return () => clearInterval(id);
  }, []);

  const handleExport = () =>
    window.open(`${API_BASE_URL}/export?month=${exportMonth}`, '_blank');

  return (
    <Box sx={{ backgroundColor:'#f7f9fc', minHeight:'100vh', pb:5 }}>
      <Container maxWidth="lg">
        <Stack spacing={4}>
          {/* Cabeçalho */}
          <Box>
            <Typography variant="h4" fontWeight="bold">Status Cloud</Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Acompanhe em tempo real o estado de cada worker.
            </Typography>
          </Box>

          {/* Bloco de exportação */}
          <Box sx={{
            p:{ xs:2, sm:2.5 }, borderRadius:4, backgroundColor:'#fefcf5',
            border:'1px solid', borderColor:amber[100]
          }}>
            <Stack direction={{ xs:'column', md:'row' }} spacing={{ xs:2, md:3 }}
                   alignItems={{ xs:'stretch', md:'center' }} justifyContent="space-between">
              <Stack direction="row" spacing={1.5} alignItems="center">
                <DownloadIcon sx={{ color:amber[800] }} />
                <Typography fontWeight={500}>Exportar relatório de acompanhamento</Typography>
              </Stack>

              <Stack direction="row" spacing={1.5} alignItems="center">
                <TextField
                  label="Mês" type="month" size="small"
                  value={exportMonth} onChange={e=>setExportMonth(e.target.value)}
                  InputLabelProps={{ shrink:true }}
                  sx={{
                    minWidth:150,
                    '& label.Mui-focused':{ color:amber[800] },
                    '& .MuiOutlinedInput-root:hover fieldset':{ borderColor:amber[400] },
                    '& .MuiOutlinedInput-root.Mui-focused fieldset':{ borderColor:'#f1c40f' }
                  }}/>
                <Button variant="contained" onClick={handleExport} startIcon={<DownloadIcon />}
                        sx={{
                          backgroundColor:'#f1c40f', color:'#000', fontWeight:600,
                          boxShadow:'none', '&:hover':{ backgroundColor:'#dab10d', boxShadow:'none' }
                        }}>
                  Exportar
                </Button>
              </Stack>
            </Stack>
          </Box>

          {/* Grid */}
          {!status ? (
            <Box sx={{ display:'flex', justifyContent:'center', p:10 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Fade in timeout={500}>
              <Box sx={{
                display:'grid',
                gridTemplateColumns:{ xs:'1fr', sm:'repeat(2,1fr)', md:'repeat(3,1fr)' },
                gap:3
              }}>
                {WORKER_KEYS.map(key => (
                  <StatusCard key={key} workerName={key} workerData={status[key]} />  // 👈 tipa corretamente
                ))}
              </Box>
            </Fade>
          )}
        </Stack>
      </Container>
    </Box>
  );
}
