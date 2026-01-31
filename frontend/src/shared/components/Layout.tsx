import { ReactNode } from 'react';
import { FileText, LogOut } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { useAuthStore } from '@/features/auth/store/authStore';

interface LayoutProps {
    children: ReactNode;
    sidebar?: ReactNode;
}

export function Layout({ children, sidebar }: LayoutProps) {
    const { user, logout } = useAuthStore();

    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    return (
        <div className="h-screen flex flex-col bg-background text-foreground">
            {/* Header */}
            <header className="border-b border-border bg-background">
                <div className="h-14 px-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        <h1 className="font-semibold text-lg">RAG PDF System</h1>
                    </div>

                    {user && (
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-muted-foreground">{user.email}</span>
                            <Button variant="ghost" size="sm" onClick={handleLogout}>
                                <LogOut className="h-4 w-4 mr-1" />
                                Logout
                            </Button>
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                {sidebar && (
                    <aside className="w-80 border-r border-border bg-background overflow-hidden">
                        {sidebar}
                    </aside>
                )}

                {/* Content */}
                <main className="flex-1 overflow-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
}
