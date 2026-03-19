import type { ReactNode } from "react";

import { Header } from "./Header";

interface LayoutProps {
  subtitle: string;
  children: ReactNode;
}

export function Layout({ subtitle, children }: LayoutProps): JSX.Element {
  return (
    <div className="app-shell">
      <Header subtitle={subtitle} />
      <main className="app-main">{children}</main>
    </div>
  );
}
