import { ClientAuthProvider } from "@/lib/clientAuth";
import { ThemeProvider } from "@/components/ThemeProvider";

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <ClientAuthProvider>{children}</ClientAuthProvider>
    </ThemeProvider>
  );
}
