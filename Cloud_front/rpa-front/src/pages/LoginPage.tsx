import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Snackbar from '@mui/material/Snackbar';
import {
  Box,
  Paper,
  TextField,
  Typography,
  Button,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '../auth/AuthContext';
import logo from '../static/img/logosc.png';
import { api } from '../services/api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [snackOpen, setSnackOpen] = useState(false);
  const [snackMsg, setSnackMsg] = useState('');

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Estados do modal de esqueci a senha
  const [openModal, setOpenModal] = useState(false);
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState<string | null>(null);

  // Estados do modal de cadastro
  const [openRegister, setOpenRegister] = useState(false);
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState<string | null>(null);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);

  // Login
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Usuário ou senha inválidos');
    } finally {
      setLoading(false);
    }
  };

  // Modal Esqueci a Senha
  const handleForgotPassword = () => setOpenModal(true);
  const handleCloseModal = () => {
    setOpenModal(false);
    setEmail('');
    setEmailError(null);
  };
  const handleSubmitEmail = async () => {
  if (!email) {
    setEmailError('Por favor, insira seu e‑mail');
    return;
  }
  try {
    await api.post("/auth/forgot-password", { email });
    setSnackMsg('Se o e‑mail existir, você receberá o link para redefinir a senha.');
    setSnackOpen(true);
    handleCloseModal();
  } catch (err) {
    setEmailError('Erro ao enviar e‑mail, tente novamente.');
  }
};

  // Modal Cadastro
  const handleOpenRegister = () => setOpenRegister(true);
  const handleCloseRegister = () => {
    setOpenRegister(false);
    setRegisterName('');
    setRegisterEmail('');
    setRegisterPassword('');
    setRegisterError(null);
    setRegisterSuccess(null);
  };
  const handleRegister = async () => {
    setRegisterError(null);
    setRegisterSuccess(null);
    if (!registerName || !registerEmail || !registerPassword) {
      setRegisterError('Preencha todos os campos');
      return;
    }
    try {
      await api.post('/auth/register', {
        username: registerName,
        email: registerEmail,
        password: registerPassword,
      });
      setRegisterSuccess('Usuário cadastrado com sucesso!');
      setTimeout(() => {
        handleCloseRegister();
      }, 1800);
    } catch (err: any) {
      if (err?.response?.data?.detail) {
        setRegisterError(err.response.data.detail);
      } else {
        setRegisterError('Erro ao cadastrar usuário');
      }
    }
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100%',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f0f2f5',
      }}
    >
      <Paper
        elevation={0}
        variant="outlined"
        sx={{
          padding: { xs: 4, sm: 5 },
          width: '100%',
          maxWidth: 400,
          borderRadius: 3,
          borderColor: 'grey.300',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          backgroundColor: '#ffffff',
        }}
      >
        {/* Caixa para agrupar o cabeçalho e garantir o espaçamento inferior */}
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>

          {/* Linha 1: Logo + Título */}
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  component="img"
                  src={logo}
                  alt="Triagem Cloud"
                  sx={{ width: 60, mr: 1 }}
                />
                <Typography variant="h5" component="h1" sx={{ fontWeight: 600 }}>
                  Triagem Cloud
                </Typography>
            </Box>

          {/* Linha 2: Subtítulo (centralizado) */}
          <Typography variant="body1" color="text.secondary">
            Bem-vindo(a), faça seu login
          </Typography>

        </Box>

        <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
          <TextField
            label="Usuário"
            variant="outlined"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />

          <TextField
            label="Senha"
            variant="outlined"
            fullWidth
            margin="normal"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disableElevation
            disabled={loading}
            sx={{
              mt: 2,
              mb: 2,
              py: 1.5,
              fontWeight: 'bold',
              fontSize: '0.9rem',
              borderRadius: 2,
              bgcolor: '#ffc107',
              color: 'black',
              '&:hover': {
                bgcolor: '#ffb300',
              },
            }}
          >
            {loading ? <CircularProgress size={26} color="inherit" /> : 'Entrar'}
          </Button>
          <Snackbar
              open={snackOpen}
              autoHideDuration={4000}
              onClose={() => setSnackOpen(false)}
              anchorOrigin={{ vertical: 'top', horizontal: 'center' }} // exemplo de posição
            >
              <Alert severity="info" sx={{ width: '100%' }}>
                {snackMsg}
              </Alert>
          </Snackbar>

          {/* NOVO: Box para alinhar links lado a lado */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mt: 1 }}>
            <Typography
              component="span"
              variant="body2"
              sx={{
                color: 'text.secondary',
                cursor: 'pointer',
                '&:hover': { textDecoration: 'underline' },
              }}
              onClick={handleForgotPassword}
            >
              Esqueci minha senha
            </Typography>

            <Typography
              component="span"
              variant="body2"
              sx={{
                color: 'text.secondary',
                cursor: 'pointer',
                '&:hover': { textDecoration: 'underline' },
              }}
              onClick={handleOpenRegister}
            >
              Cadastrar novo usuário
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Modal para recuperar senha */}
      <Dialog open={openModal} onClose={handleCloseModal}>
        <DialogTitle>Recuperar Senha</DialogTitle>
        <DialogContent>
          <TextField
            label="Digite seu e-mail"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={!!emailError}
            helperText={emailError}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseModal} color="primary">Cancelar</Button>
          <Button onClick={handleSubmitEmail} color="primary">Enviar</Button>
        </DialogActions>
      </Dialog>

      {/* Modal para cadastro de usuário */}
      <Dialog open={openRegister} onClose={handleCloseRegister}>
        <DialogTitle>Cadastrar Novo Usuário</DialogTitle>
        <DialogContent>
          <TextField
            label="Usuário"
            fullWidth
            margin="normal"
            value={registerName}
            onChange={(e) => setRegisterName(e.target.value)}
          />
          <TextField
            label="E-mail"
            type="email"
            fullWidth
            margin="normal"
            value={registerEmail}
            onChange={(e) => setRegisterEmail(e.target.value)}
          />
          <TextField
            label="Senha"
            type={showRegisterPassword ? "text" : "password"}
            fullWidth
            margin="normal"
            value={registerPassword}
            onChange={(e) => setRegisterPassword(e.target.value)}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                    edge="end"
                  >
                    {showRegisterPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          {registerError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {registerError}
            </Alert>
          )}
          {registerSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {registerSuccess}
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ p: '16px 24px' }}>
          <Button onClick={handleCloseRegister} sx={{ color: '#ffb300', fontWeight: 'bold' }}>
            Cancelar
          </Button>
          <Button
            onClick={handleRegister}
            variant="contained"
            sx={{
              bgcolor: '#ffc107',
              color: 'black',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: '#ffb300',
              },
            }}
          >
            Cadastrar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}