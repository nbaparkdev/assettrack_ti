import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, BookOpen, Box, CheckCircle2, ChevronRight, CircleHelp,
  ClipboardCheck, Headphones, Monitor, ShieldCheck, ShoppingCart, Users,
  Wrench,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';

type ManualSection = {
  id: string;
  title: string;
  eyebrow: string;
  description: string;
  icon: React.ElementType;
  roles: string[];
  bullets: string[];
  action?: { label: string; to: string };
};

const roleNames: Record<string, string> = {
  admin: 'Administrador', gerente_ti: 'Gerente de TI', gerente_infra: 'Gerente de Infraestrutura',
  tecnico: 'Técnico', comprador: 'Comprador', rh: 'RH', usuario_comum: 'Usuário',
};

const roleGroups: Record<string, string[]> = {
  admin: ['common', 'staff', 'manager', 'admin', 'purchases', 'rh'],
  gerente_ti: ['common', 'staff', 'manager', 'purchases'],
  gerente_infra: ['common', 'staff', 'manager', 'purchases'],
  tecnico: ['common', 'staff'],
  comprador: ['common', 'purchases'],
  rh: ['common', 'rh'],
  usuario_comum: ['common'],
};

const sections: ManualSection[] = [
  { id: 'inicio', title: 'Primeiros passos', eyebrow: 'Base', description: 'Entenda a navegação, o perfil e os atalhos essenciais do AssetTrack TI.', icon: BookOpen, roles: ['common'], bullets: ['Acesse o sistema com e-mail e senha ou pelo crachá QR + PIN.', 'Use o menu lateral para abrir cada módulo e o botão de ajuda para voltar a este manual.', 'O cabeçalho mostra conexão, notificações, emergência e download do aplicativo Android.'], action: { label: 'Abrir Dashboard', to: '/' } },
  { id: 'ativos', title: 'Ativos & Inventário', eyebrow: 'Patrimônio', description: 'Controle equipamentos, localização, responsável e histórico de movimentações.', icon: Box, roles: ['common', 'staff', 'manager', 'purchases'], bullets: ['Pesquise por E-Patrimônio, número de série, categoria, status e localização.', 'O campo de posse indica quem está com o equipamento em uso.', 'Use o Scanner QR para abrir a ficha do ativo e consultar seu histórico.'], action: { label: 'Abrir Ativos', to: '/assets' } },
  { id: 'suporte', title: 'Chamados e atendimento', eyebrow: 'Service Desk', description: 'Abra solicitações, acompanhe a timeline e mantenha toda a comunicação registrada.', icon: Headphones, roles: ['common', 'staff', 'manager'], bullets: ['Crie um chamado com serviço, prioridade, descrição e anexos.', 'A equipe acompanha status, técnico atribuído, interações e solução.', 'Alertas relacionados a chamados levam diretamente ao ticket correspondente.'], action: { label: 'Abrir Central de Suporte', to: '/servicos' } },
  { id: 'manutencao', title: 'Manutenção', eyebrow: 'Operação', description: 'Registre falhas, acompanhe equipamentos em reparo e confirme a devolução.', icon: Wrench, roles: ['common', 'staff', 'manager'], bullets: ['Solicite reparo para um ativo que esteja sob sua responsabilidade.', 'Técnicos assumem, executam e concluem a manutenção com histórico.', 'O recebimento pode ser confirmado pelo QR Code do usuário.'], action: { label: 'Abrir Manutenções', to: '/manutencoes' } },
  { id: 'monitoramento', title: 'Sala de monitoramento TV', eyebrow: 'Tempo real', description: 'Painel operacional para administradores, gerentes e técnicos acompanharem a operação em uma TV.', icon: Monitor, roles: ['staff', 'manager', 'admin'], bullets: ['Exibe chamados ativos, status, técnico atribuído, solicitações de ativos, manutenções e alertas.', 'Os dados são atualizados automaticamente a cada 5 segundos.', 'Novos eventos usam o som configurado; alertas emergenciais abrem o modal vermelho existente.', 'Use Tela cheia para operação contínua na sala de monitoramento.'], action: { label: 'Abrir monitoramento', to: '/monitoramento' } },
  { id: 'emergencia', title: 'Alertas emergenciais', eyebrow: 'Prioridade crítica', description: 'Acione e receba incidentes urgentes com transmissão imediata para a equipe responsável.', icon: ShieldCheck, roles: ['common', 'staff', 'manager'], bullets: ['Usuários podem acionar emergência pelo botão vermelho e informar o motivo.', 'Administração, gerência e técnicos recebem o modal, o alarme e os dados do colaborador.', 'O equipamento em uso é identificado automaticamente pelo vínculo atual do ativo.', 'Marque Ciente para registrar quem assumiu o atendimento.'], action: { label: 'Abrir Alertas', to: '/alertas' } },
  { id: 'compras', title: 'Compras e suprimentos', eyebrow: 'Suprimentos', description: 'Acompanhe solicitações, cotações, pedidos, contratos e recebimentos.', icon: ShoppingCart, roles: ['purchases', 'manager', 'admin'], bullets: ['Solicitações podem nascer de um chamado, manutenção ou do módulo de compras.', 'Compradores gerenciam fornecedores, cotações, ordens de compra e recebimento.', 'Itens recebidos podem gerar ativos patrimoniais automaticamente.'], action: { label: 'Abrir Compras', to: '/compras' } },
  { id: 'rh', title: 'RH e termos', eyebrow: 'Pessoas', description: 'Controle termos de responsabilidade e o ciclo de entrega de equipamentos.', icon: Users, roles: ['rh', 'admin'], bullets: ['O RH visualiza entregas pendentes e gerencia aceite dos termos.', 'Documentos assinados podem ser anexados para manter o comprovante digital.', 'O acesso é simplificado para mostrar apenas as tarefas relevantes ao perfil.'], action: { label: 'Abrir Portal RH', to: '/rh' } },
  { id: 'admin', title: 'Administração e segurança', eyebrow: 'Governança', description: 'Configure módulos, usuários, acessos, backups e integrações.', icon: ClipboardCheck, roles: ['admin'], bullets: ['Gerencie usuários, setores, permissões e configurações globais.', 'Use Backup & Restore para proteger e recuperar a base e os arquivos.', 'Os menus são controlados por perfil e o administrador mantém acesso garantido.'], action: { label: 'Abrir Configurações', to: '/configuracoes' } },
];

export const ManualPage: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const role = user?.role?.toLowerCase() || 'usuario_comum';
  const [showAll, setShowAll] = useState(false);
  const allowedGroups = roleGroups[role] || ['common'];
  const visibleSections = useMemo(() => showAll ? sections : sections.filter((section) => section.roles.some((item) => allowedGroups.includes(item))), [allowedGroups, showAll]);

  return (
    <div className="mx-auto max-w-[1500px] space-y-7 pb-8">
      <section className="relative overflow-hidden rounded-[28px] border border-[#b8d7ef] bg-[#0b2944] px-6 py-8 text-white shadow-[0_20px_60px_rgba(9,30,66,.18)] sm:px-10 sm:py-11">
        <div className="pointer-events-none absolute -right-24 -top-28 h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="relative grid items-center gap-8 lg:grid-cols-[1fr_390px]">
          <div><div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[.2em] text-cyan-200"><CircleHelp size={14} /> Manual completo</div><h1 className="max-w-2xl text-3xl font-bold tracking-tight sm:text-5xl">Operação clara. <span className="text-cyan-300">TI no controle.</span></h1><p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">Um guia visual para usar o AssetTrack TI com segurança, rapidez e o nível certo de informação para cada perfil.</p><div className="mt-6 flex flex-wrap items-center gap-3"><span className="rounded-xl bg-white/10 px-3 py-2 text-xs text-slate-200">Seu perfil: <strong className="text-white">{roleNames[role] || role}</strong></span><button onClick={() => setShowAll((current) => !current)} className="rounded-xl border border-white/20 px-3 py-2 text-xs font-semibold text-white transition hover:bg-white/10">{showAll ? 'Ver apenas meu perfil' : 'Ver todos os módulos'}</button></div></div>
          <div className="hidden lg:block"><svg viewBox="0 0 390 240" role="img" aria-label="Ilustração de painel técnico" className="w-full"><rect x="27" y="20" width="336" height="199" rx="18" fill="#123c5f" stroke="#4dd8f2" strokeOpacity=".5"/><rect x="51" y="47" width="116" height="10" rx="5" fill="#8defff" fillOpacity=".8"/><rect x="51" y="75" width="90" height="62" rx="10" fill="#0e2b48" stroke="#315a7d"/><rect x="153" y="75" width="90" height="62" rx="10" fill="#0e2b48" stroke="#315a7d"/><rect x="255" y="75" width="83" height="62" rx="10" fill="#0e2b48" stroke="#315a7d"/><path d="M62 120h16l8-19 11 28 10-16 13 7h18" fill="none" stroke="#57e0f0" strokeWidth="3"/><circle cx="198" cy="107" r="19" fill="#173f62" stroke="#ffd166" strokeWidth="5"/><path d="M198 96v22M187 107h22" stroke="#ffd166" strokeWidth="4"/><path d="M276 112h40M276 122h27" stroke="#ff7d8f" strokeWidth="4" strokeLinecap="round"/><rect x="51" y="158" width="287" height="37" rx="10" fill="#0e2b48" stroke="#315a7d"/><circle cx="69" cy="177" r="6" fill="#63e6be"/><path d="M84 173h150M84 182h104" stroke="#7899b7" strokeWidth="4" strokeLinecap="round"/></svg></div>
        </div>
      </section>

      <div className="flex items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.22em] text-brand-primary">Roteiro operacional</p><h2 className="mt-1 text-2xl font-bold text-brand-text">O que você precisa saber</h2></div><p className="hidden text-right text-xs text-brand-muted sm:block">{visibleSections.length} módulos disponíveis<br />para este perfil</p></div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{visibleSections.map((section, index) => { const Icon = section.icon; return <article key={section.id} className="group flex flex-col rounded-2xl border border-brand-border bg-white/70 p-5 shadow-[0_8px_24px_rgba(9,30,66,.06)] transition hover:-translate-y-1 hover:border-brand-primary/40 hover:bg-white"><div className="flex items-start justify-between"><div className="grid h-11 w-11 place-items-center rounded-xl bg-[#dff6fb] text-[#087e9a]"><Icon size={21} /></div><span className="font-mono text-xs text-brand-muted">{String(index + 1).padStart(2, '0')}</span></div><p className="mt-5 text-[10px] font-bold uppercase tracking-[.18em] text-brand-primary">{section.eyebrow}</p><h3 className="mt-1 text-xl font-bold text-brand-text">{section.title}</h3><p className="mt-2 text-sm leading-6 text-brand-muted">{section.description}</p><ul className="mt-4 space-y-2 text-xs leading-5 text-brand-text">{section.bullets.map((bullet) => <li key={bullet} className="flex gap-2"><CheckCircle2 size={15} className="mt-0.5 shrink-0 text-emerald-500" /> <span>{bullet}</span></li>)}</ul>{section.action && <Link to={section.action.to} className="mt-5 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-primary transition group-hover:gap-3">{section.action.label}<ArrowRight size={15} /></Link>}</article>; })}</div>

      <section className="rounded-2xl border border-brand-border bg-[#f0f7fb] p-5 sm:p-7"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-[.2em] text-brand-primary">Atalhos de segurança</p><h2 className="mt-1 text-xl font-bold text-brand-text">Precisa de ajuda agora?</h2><p className="mt-1 text-sm text-brand-muted">Abra o suporte para registrar um chamado ou volte ao painel principal.</p></div><div className="flex flex-wrap gap-2"><Link to="/servicos" className="inline-flex items-center gap-2 rounded-xl bg-brand-primary px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:brightness-105"><Headphones size={15} /> Abrir chamado</Link><Link to="/" className="inline-flex items-center gap-2 rounded-xl border border-brand-border bg-white px-4 py-2.5 text-xs font-bold text-brand-text hover:bg-white/80"><ChevronRight size={15} /> Dashboard</Link></div></div></section>
    </div>
  );
};
