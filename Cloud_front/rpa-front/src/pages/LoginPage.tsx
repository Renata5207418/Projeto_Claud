import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, TextField, Typography, Button, Alert, CircularProgress,
  InputAdornment, IconButton, Dialog, DialogActions, DialogContent,
  DialogTitle, Snackbar,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '../auth/AuthContext';
import logo from '../static/img/logosc.png';
import { api } from '../services/api';

// Estilo customizado para os TextFields para seguir a identidade visual
const themedTextFieldSx = {
  '& label.Mui-focused': {
    color: '#b28d0b', // Amarelo mais escuro para o texto do label
  },
  '& .MuiOutlinedInput-root': {
    '&.Mui-focused fieldset': {
      borderColor: '#ffc107', // Borda amarela ao focar
    },
  },
};

// --- Componente para o Modal de Recuperação de Senha ---
const ForgotPasswordDialog = ({ open, onClose }: { open: boolean; onClose: () => void; }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [snackOpen, setSnackOpen] = useState(false);

  const handleSubmit = async () => {
    if (!email) {
      setError('Por favor, insira seu e-mail.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.post("/auth/forgot-password", { email });
      setSnackOpen(true);
      onClose();
    } catch (err) {
      setError('Erro ao enviar e-mail. Verifique o endereço e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogTitle fontWeight="bold">Recuperar Senha</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Digite seu e-mail para receber o link de redefinição.
          </Typography>
          <TextField
            autoFocus
            label="E-mail"
            type="email"
            fullWidth
            margin="dense"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={!!error}
            helperText={error}
            disabled={loading}
            sx={themedTextFieldSx} // Aplicando o estilo
          />
        </DialogContent>
        <DialogActions sx={{ p: '16px 24px' }}>
          {/* Botão Cancelar com cor neutra */}
          <Button onClick={onClose} disabled={loading} sx={{ color: 'grey.700' }}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={loading} sx={{ bgcolor: '#ffc107', color: 'black', '&:hover': { bgcolor: '#ffb300' } }}>
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Enviar'}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={snackOpen} autoHideDuration={6000} onClose={() => setSnackOpen(false)} anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
        <Alert onClose={() => setSnackOpen(false)} severity="info" sx={{ width: '100%' }}>
          Se o e-mail existir, você receberá o link para redefinir a senha.
        </Alert>
      </Snackbar>
    </>
  );
};

// --- Componente para o Modal de Cadastro ---
const RegisterDialog = ({ open, onClose }: { open: boolean; onClose: () => void; }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async () => {
    setError('');
    setSuccess('');
    if (!formData.name || !formData.email || !formData.password) {
      setError('Por favor, preencha todos os campos.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/register', {
        username: formData.name,
        email: formData.email,
        password: formData.password,
      });
      setSuccess('Usuário cadastrado com sucesso!');
      setTimeout(() => {
        onClose();
        setSuccess('');
      }, 2000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao cadastrar usuário.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle fontWeight="bold">Cadastrar Novo Usuário</DialogTitle>
      <DialogContent>
        <TextField autoFocus name="name" label="Usuário" fullWidth margin="dense" value={formData.name} onChange={handleChange} disabled={loading} sx={themedTextFieldSx} />
        <TextField name="email" label="E-mail" type="email" fullWidth margin="dense" value={formData.email} onChange={handleChange} disabled={loading} sx={themedTextFieldSx} />
        <TextField
          name="password"
          label="Senha"
          type={showPassword ? "text" : "password"}
          fullWidth
          margin="dense"
          value={formData.password}
          onChange={handleChange}
          disabled={loading}
          sx={themedTextFieldSx} // Aplicando o estilo
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
      </DialogContent>
      <DialogActions sx={{ p: '16px 24px' }}>
        {/* Botão Cancelar com cor neutra */}
        <Button onClick={onClose} disabled={loading} sx={{ color: 'grey.700' }}>Cancelar</Button>
        <Button onClick={handleRegister} variant="contained" disabled={loading} sx={{ bgcolor: '#ffc107', color: 'black', '&:hover': { bgcolor: '#ffb300' } }}>
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Cadastrar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};


// --- Componente Principal da Página de Login ---
export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [isForgotModalOpen, setForgotModalOpen] = useState(false);
  const [isRegisterModalOpen, setRegisterModalOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Usuário ou senha inválidos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Box sx={{ position: 'fixed', top: 0, left: 0, height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f2f5' }}>
        <Paper elevation={0} variant="outlined" sx={{ padding: { xs: 4, sm: 5 }, width: '100%', maxWidth: 400, borderRadius: 3, borderColor: 'grey.300', backgroundColor: '#ffffff' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <img src={logo} alt="Triagem Cloud Logo" style={{ width: 60 }} />
              <Typography variant="h5" component="h1" sx={{ fontWeight: 600 }}>Triagem Cloud</Typography>
            </Box>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
              Bem-vindo(a), faça seu login!
            </Typography>
          </Box>

          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <TextField label="Usuário" variant="outlined" fullWidth margin="normal" value={username} onChange={(e) => setUsername(e.target.value)} disabled={loading} sx={themedTextFieldSx} />
            <TextField
              label="Senha"
              variant="outlined"
              fullWidth
              margin="normal"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              sx={themedTextFieldSx} // Aplicando o estilo
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            {error && <Alert severity="error" sx={{ mt: 2, width: '100%' }}>{error}</Alert>}

            <Button type="submit" fullWidth variant="contained" disableElevation disabled={loading} sx={{ mt: 2, mb: 2, py: 1.5, fontWeight: 'bold', fontSize: '1rem', borderRadius: 2, bgcolor: '#ffc107', color: 'black', '&:hover': { bgcolor: '#ffb300' } }}>
              {loading ? <CircularProgress size={26} color="inherit" /> : 'Entrar'}
            </Button>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mt: 1 }}>
              <Typography component="span" variant="body2" onClick={() => setForgotModalOpen(true)} sx={{ color: 'text.secondary', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>
                Esqueci minha senha
              </Typography>
              <Typography component="span" variant="body2" onClick={() => setRegisterModalOpen(true)} sx={{ color: 'text.secondary', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>
                Cadastrar novo usuário
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>

      <ForgotPasswordDialog open={isForgotModalOpen} onClose={() => setForgotModalOpen(false)} />
      <RegisterDialog open={isRegisterModalOpen} onClose={() => setRegisterModalOpen(false)} />
    </>
  );
}
