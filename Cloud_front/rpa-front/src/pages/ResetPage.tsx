import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  TextField,
  Typography,
  Button,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { api } from "../services/api"; // 1. Importando a instância do Axios
import logo from "../static/img/logosc.png";

// 2. Estilo customizado para os TextFields, para consistência visual
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

// 3. Função para verificar a força da senha (melhora de UX)
const getPasswordStrength = (password: string) => {
  const length = password.length;
  if (length === 0) return null;
  if (length < 6) return { text: 'Fraca (mínimo 6 caracteres)', color: 'error.main' };
  if (length < 8) return { text: 'Média', color: 'warning.main' };
  return { text: 'Forte', color: 'success.main' };
};


const ResetPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const passwordStrength = getPasswordStrength(newPassword);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!token) {
      setError("Token ausente ou inválido. Tente solicitar novamente.");
      return;
    }
    if (newPassword.length < 6) {
      setError("A senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    setLoading(true);
    try {
      // Usando a instância do 'api' para consistência
      await api.post("/auth/reset-password", {
        token,
        new_password: newPassword
      });

      setMessage("Senha redefinida com sucesso! Redirecionando para login...");
      setTimeout(() => navigate("/login"), 2500);

    } catch (err: any) {
      // Tratamento de erro padrão do Axios
      setError(err.response?.data?.detail || "Erro ao redefinir senha.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ position: 'fixed', top: 0, left: 0, height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f2f5' }}>
      <Paper elevation={0} variant="outlined" sx={{ padding: { xs: 4, sm: 5 }, width: '100%', maxWidth: 400, borderRadius: 3, borderColor: 'grey.300', backgroundColor: '#ffffff' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <img src={logo} alt="Triagem Cloud" style={{ width: 60 }} />
            <Typography variant="h5" component="h1" sx={{ fontWeight: 600 }}>Redefinir Senha</Typography>
          </Box>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Insira a nova senha para sua conta.
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
          <TextField
            label="Nova senha"
            variant="outlined"
            fullWidth
            margin="normal"
            type={showNewPassword ? 'text' : 'password'}
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            required
            disabled={loading}
            sx={themedTextFieldSx} // Aplicando estilo
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowNewPassword(!showNewPassword)} edge="end">
                    {showNewPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              )
            }}
          />

          {/* Indicador de força da senha */}
          {passwordStrength && (
            <Typography variant="caption" sx={{ color: passwordStrength.color, ml: 1.5, display: 'block' }}>
              Força da senha: {passwordStrength.text}
            </Typography>
          )}

          <TextField
            label="Confirmar senha"
            variant="outlined"
            fullWidth
            margin="normal"
            type={showConfirmPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            required
            disabled={loading}
            sx={themedTextFieldSx} // Aplicando estilo
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end">
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              )
            }}
          />

          {error && <Alert severity="error" sx={{ mt: 2, width: '100%' }}>{error}</Alert>}
          {message && <Alert severity="success" sx={{ mt: 2, width: '100%' }}>{message}</Alert>}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disableElevation
            disabled={loading || !!message} // Desabilita também após o sucesso
            sx={{ mt: 2, mb: 2, py: 1.5, fontWeight: 'bold', fontSize: '1rem', borderRadius: 2, bgcolor: '#ffc107', color: 'black', '&:hover': { bgcolor: '#ffb300' } }}
          >
            {loading ? <CircularProgress size={26} color="inherit" /> : 'Redefinir senha'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ResetPage;
