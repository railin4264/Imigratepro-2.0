import { ClientAuthProvider } from "@/lib/clientAuth";

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  return <ClientAuthProvider>{children}</ClientAuthProvider>;
}
