import { Linkedin } from "lucide-react";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <p><span>OpsMind2</span> · Responsável pelo projeto: <strong>Willian Douglas</strong></p>
      <a href="https://www.linkedin.com/in/willian-douglas-contato" target="_blank" rel="noreferrer" aria-label="LinkedIn de Willian Douglas (abre em nova aba)">
        <Linkedin size={16} aria-hidden="true" /> LinkedIn
      </a>
    </footer>
  );
}
