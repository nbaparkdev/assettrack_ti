import React, { useState, useRef, useEffect } from 'react';
import { User, Key, Camera, Loader2, Save } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { profileApi } from '../api/profile';
import { toApiFileUrl } from '../api/client';

export const ProfilePage: React.FC = () => {
  const { user, logout, checkAuth } = useAuthStore();
  
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [matricula, setMatricula] = useState('');
  
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      setNome(user.nome || '');
      setEmail(user.email || '');
      setMatricula(user.matricula || '');
    }
  }, [user]);

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await profileApi.updateProfile({ nome, email, matricula });
      alert('Perfil atualizado com sucesso!');
      checkAuth(); // Refresh user state
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao atualizar perfil');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert('As senhas não coincidem!');
      return;
    }
    setSavingPassword(true);
    try {
      await profileApi.changePassword({ current_password: currentPassword, new_password: newPassword });
      alert('Senha alterada com sucesso! Você será desconectado.');
      logout();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Erro ao alterar senha');
    } finally {
      setSavingPassword(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const processAndUploadAvatar = (file: File) => {
    setUploadingAvatar(true);
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (event) => {
      const img = new Image();
      img.src = event.target?.result as string;
      img.onload = async () => {
        const canvas = document.createElement('canvas');
        const maxSize = 256;
        const width = img.width;
        const height = img.height;

        // Crop square center
        const size = Math.min(width, height);
        const sx = (width - size) / 2;
        const sy = (height - size) / 2;

        canvas.width = maxSize;
        canvas.height = maxSize;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        ctx.drawImage(img, sx, sy, size, size, 0, 0, maxSize, maxSize);
        
        canvas.toBlob(async (blob) => {
          if (!blob) {
            setUploadingAvatar(false);
            return;
          }
          const compressedFile = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
          try {
            await profileApi.uploadAvatar(compressedFile);
            await checkAuth(); // Refresh user avatar
          } catch (err) {
            alert('Erro ao enviar foto de perfil');
          } finally {
            setUploadingAvatar(false);
          }
        }, 'image/jpeg', 0.8);
      };
    };
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processAndUploadAvatar(file);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (!user) return null;

  const avatarUrl = toApiFileUrl(user.avatar_url);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0 flex items-center">
          <User className="mr-3 text-brand-primary" size={28} />
          Meu Perfil
        </h1>
        <p className="text-brand-muted text-sm mt-1">Gerencie suas informações pessoais, avatar e senha de acesso</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Avatar & Basic Info */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-brand-card border border-brand-border p-6 flex flex-col items-center">
            <div 
              className="relative w-32 h-32 rounded-full overflow-hidden border-2 border-brand-primary/50 group cursor-pointer bg-brand-dark flex items-center justify-center mb-4"
              onClick={handleAvatarClick}
            >
              {uploadingAvatar ? (
                <Loader2 className="animate-spin text-brand-primary" size={32} />
              ) : avatarUrl ? (
                <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <span className="text-4xl font-mono text-brand-primary/50">{user.nome.substring(0,2).toUpperCase()}</span>
              )}
              
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Camera className="text-white" size={24} />
              </div>
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept="image/png, image/jpeg, image/webp" 
                onChange={handleFileChange}
              />
            </div>
            
            <h2 className="text-lg font-bold text-brand-text text-center">{user.nome}</h2>
            <p className="text-sm text-brand-primary font-mono uppercase tracking-wider text-center mt-1">{user.role.replace('_', ' ')}</p>
            <p className="text-xs text-brand-muted mt-1 text-center">{user.cargo || 'Cargo não definido'}</p>
          </div>
        </div>

        {/* Right Column: Forms */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Profile Details Form */}
          <div className="bg-brand-card border border-brand-border">
            <div className="p-4 border-b border-brand-border flex items-center">
              <User className="mr-2 text-brand-primary" size={18} />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text m-0">Dados Pessoais</h3>
            </div>
            <form onSubmit={handleProfileUpdate} className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">Nome Completo</label>
                  <input
                    type="text"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    required
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">E-mail Corporativo</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">Matrícula</label>
                  <input
                    type="text"
                    value={matricula}
                    onChange={(e) => setMatricula(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={savingProfile}
                  className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs flex items-center hover:bg-brand-primary/90 disabled:opacity-50"
                >
                  <Save size={16} className="mr-2" />
                  {savingProfile ? 'Salvando...' : 'Salvar Alterações'}
                </button>
              </div>
            </form>
          </div>

          {/* Password Form */}
          <div className="bg-brand-card border border-brand-border">
            <div className="p-4 border-b border-brand-border flex items-center">
              <Key className="mr-2 text-brand-primary" size={18} />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text m-0">Alterar Senha</h3>
            </div>
            <form onSubmit={handlePasswordUpdate} className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">Senha Atual</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">Nova Senha</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={4}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-brand-muted mb-1 uppercase">Confirmar Nova Senha</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={4}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={savingPassword || !currentPassword || !newPassword || !confirmPassword}
                  className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs flex items-center hover:bg-brand-primary/90 disabled:opacity-50"
                >
                  <Key size={16} className="mr-2" />
                  {savingPassword ? 'Alterando...' : 'Alterar Senha'}
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
};
