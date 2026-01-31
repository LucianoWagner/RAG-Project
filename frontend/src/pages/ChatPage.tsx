import { Layout } from '@/shared/components/Layout';
import { ChatInterface } from '@/features/chat/components/ChatInterface';
import { DocumentList } from '@/features/documents/components/DocumentList';
import { HealthStatus } from '@/features/monitoring/components/HealthStatus';

export function ChatPage() {
    return (
        <Layout
            sidebar={
                <div className="h-full flex flex-col">
                    <div className="flex-1 overflow-hidden">
                        <DocumentList />
                    </div>
                    <div className="border-t border-border p-4">
                        <HealthStatus />
                    </div>
                </div>
            }
        >
            <ChatInterface />
        </Layout>
    );
}
