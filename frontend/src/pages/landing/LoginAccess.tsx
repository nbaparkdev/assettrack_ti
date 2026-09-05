import { useRef } from 'react';
import { ArrowUpRight } from 'lucide-react';

export function LoginAccess() {
  const dialog = useRef<HTMLDialogElement>(null);

  return <>
    <button type="button" className="login-access-button" onClick={() => dialog.current?.showModal()}>
      Acessar aplicação <ArrowUpRight size={18} aria-hidden="true" />
    </button>
    <dialog ref={dialog} className="login-redirect-dialog" aria-labelledby="redirect-title" aria-describedby="redirect-description">
      <h2 id="redirect-title">Você será redirecionado</h2>
      <p id="redirect-description">Você vai acessar a tela de login do AssetTrack TI desta instalação. Entre com suas credenciais da aplicação para continuar.</p>
      <div className="login-actions">
        <form method="dialog"><button type="submit" className="login-cancel" autoFocus>Cancelar</button></form>
        <a className="login-continue" href="/login">Continuar para o login <ArrowUpRight size={17} aria-hidden="true" /></a>
      </div>
    </dialog>
  </>;
}
