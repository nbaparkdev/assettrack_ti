import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, ArrowLeftRight, QrCode, Menu } from 'lucide-react';

interface BottomNavProps {
  onOpenDrawer: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ onOpenDrawer }) => {
  const navItems = [
    { name: 'Início', path: '/', icon: LayoutDashboard },
    { name: 'Suporte', path: '/servicos', icon: MessageSquare },
    { name: 'Empréstimos', path: '/emprestimos', icon: ArrowLeftRight },
    { name: 'Meu Crachá', path: '/badge', icon: QrCode },
  ];

  return (
    <nav
      aria-label="Navegação móvel"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#edf5fa]/95 border-t border-white/60 backdrop-blur-lg shadow-[0_-4px_20px_rgba(9,30,66,.12)]"
      style={{ paddingBottom: 'max(env(safe-area-inset-bottom, 0px), 6px)' }}
    >
      <div className="flex items-center justify-around px-2 py-1.5">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center min-w-[56px] py-1 px-2 rounded-xl transition-all duration-150 active:scale-95 ${
                isActive
                  ? 'text-[#0c66e4] font-bold'
                  : 'text-[#5e6c84] hover:text-[#172b4d]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div
                  className={`p-1 rounded-lg transition-colors ${
                    isActive ? 'bg-[#0c66e4]/15' : 'bg-transparent'
                  }`}
                >
                  <item.icon size={20} />
                </div>
                <span className="text-[10px] tracking-tight mt-0.5">{item.name}</span>
              </>
            )}
          </NavLink>
        ))}

        {/* Button to open full Drawer */}
        <button
          type="button"
          onClick={onOpenDrawer}
          className="flex flex-col items-center justify-center min-w-[56px] py-1 px-2 rounded-xl text-[#5e6c84] hover:text-[#172b4d] active:scale-95 transition-all cursor-pointer"
          title="Abrir menu completo"
          aria-label="Abrir menu completo"
        >
          <div className="p-1 rounded-lg bg-transparent">
            <Menu size={20} />
          </div>
          <span className="text-[10px] tracking-tight mt-0.5">Mais</span>
        </button>
      </div>
    </nav>
  );
};
