import { Outlet } from "react-router";
import { Sidebar } from "@/components/layout/Sidebar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="mx-auto max-w-[1200px] p-8 md:ml-[180px] lg:ml-60 mt-14 md:mt-0">
        <Outlet />
      </main>
    </div>
  );
}
