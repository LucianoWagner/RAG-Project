import { useHealth } from '../hooks/useHealth';
import { Activity, Database, Cpu, HardDrive } from 'lucide-react';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { cn } from '@/shared/lib/utils';

export function HealthStatus() {
    const { data: health, isLoading } = useHealth();

    if (isLoading) {
        return (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <LoadingSpinner size="sm" />
                <span>Checking status...</span>
            </div>
        );
    }

    if (!health) return null;

    const services = [
        {
            name: 'Ollama',
            isHealthy: health.services.ollama.available,
            icon: Cpu
        },
        {
            name: 'Redis',
            isHealthy: health.services.redis.available,
            icon: Activity
        },
        {
            name: 'MySQL',
            isHealthy: health.services.mysql.available,
            icon: Database
        },
        {
            name: 'Vector Store',
            isHealthy: health.services.vector_store.initialized,
            icon: HardDrive
        }
    ];

    return (
        <div className="space-y-2">
            <h3 className="text-xs font-semibold text-muted-foreground">System Status</h3>
            <div className="space-y-1.5">
                {services.map((service) => {
                    const Icon = service.icon;

                    return (
                        <div key={service.name} className="flex items-center gap-2 text-xs">
                            <div
                                className={cn(
                                    'h-2 w-2 rounded-full',
                                    service.isHealthy ? 'bg-green-500' : 'bg-red-500'
                                )}
                            />
                            <Icon className={cn(
                                'h-3 w-3',
                                service.isHealthy ? 'text-green-600' : 'text-red-600'
                            )} />
                            <span className="text-foreground">{service.name}</span>
                            <span className={cn(
                                'ml-auto',
                                service.isHealthy ? 'text-green-600' : 'text-red-600'
                            )}>
                                {service.isHealthy ? 'Healthy' : 'Down'}
                            </span>
                        </div>
                    );
                })}

                {health.services.vector_store && (
                    <div className="text-xs text-muted-foreground pt-2 border-t border-border mt-2">
                        <div className="flex justify-between">
                            <span>Documents:</span>
                            <span className="text-foreground">
                                {health.services.vector_store.documents}
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
