interface HeaderProps {
  subtitle: string;
}

export function Header({ subtitle }: HeaderProps): JSX.Element {
  return (
    <header className="app-header">
      <div className="brand-mark" aria-hidden="true" />
      <div>
        <h1>RE-Storage Model Web Tool</h1>
        <p>{subtitle}</p>
      </div>
    </header>
  );
}
