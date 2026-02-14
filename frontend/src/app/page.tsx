import { Sidebar } from "@/components/pipeline/Sidebar";
import { DealPipeline } from "@/components/pipeline/DealPipeline";

export default function Home() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <DealPipeline />
      </main>
    </div>
  );
}
