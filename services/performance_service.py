"""
Performance Optimization Service for Brightpath Ascend FCRA Platform

Provides:
- Request performance tracking and metrics
- In-memory caching with TTL support
- Database query optimization analysis
- Connection pool monitoring
"""

import time
import threading
import hashlib
import json
import re
import statistics
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple, Callable
from flask import request, g


_cache_store: Dict[str, Dict] = {}
_cache_lock = threading.RLock()


_request_metrics: Dict[str, List[Dict]] = defaultdict(list)
_metrics_lock = threading.RLock()
_MAX_METRICS_PER_ENDPOINT = 1000


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0
        self._stats: Dict[str, Dict] = defaultdict(lambda: {'hits': 0, 'misses': 0})
    
    def get(self, key: str) -> Tuple[Any, bool]:
        """Get value from cache. Returns (value, hit) tuple."""
        with self._lock:
            if key not in self._store:
                self._miss_count += 1
                self._stats[key]['misses'] += 1
                return None, False
            
            entry = self._store[key]
            if entry['expires_at'] and datetime.utcnow() > entry['expires_at']:
                del self._store[key]
                self._miss_count += 1
                self._stats[key]['misses'] += 1
                return None, False
            
            entry['hit_count'] += 1
            entry['last_accessed'] = datetime.utcnow()
            self._hit_count += 1
            self._stats[key]['hits'] += 1
            return entry['value'], True
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL (default 5 minutes)"""
        with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None
            self._store[key] = {
                'value': value,
                'ttl_seconds': ttl_seconds,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'last_accessed': datetime.utcnow(),
                'hit_count': 0
            }
    
    def delete(self, key: str) -> bool:
        """Delete a specific key from cache"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    def clear(self, pattern: str = None) -> int:
        """Clear cache entries matching pattern (or all if no pattern)"""
        with self._lock:
            if pattern is None:
                count = len(self._store)
                self._store.clear()
                return count
            
            regex = re.compile(pattern.replace('*', '.*'))
            keys_to_delete = [k for k in self._store.keys() if regex.match(k)]
            for key in keys_to_delete:
                del self._store[key]
            return len(keys_to_delete)
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                k for k, v in self._store.items()
                if v['expires_at'] and now > v['expires_at']
            ]
            for key in expired_keys:
                del self._store[key]
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
            
            entries = []
            for key, entry in self._store.items():
                is_expired = entry['expires_at'] and datetime.utcnow() > entry['expires_at']
                entries.append({
                    'key': key,
                    'ttl_seconds': entry['ttl_seconds'],
                    'created_at': entry['created_at'].isoformat(),
                    'expires_at': entry['expires_at'].isoformat() if entry['expires_at'] else None,
                    'hit_count': entry['hit_count'],
                    'is_expired': is_expired,
                    'size_estimate': len(str(entry['value']))
                })
            
            return {
                'total_entries': len(self._store),
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_rate': round(hit_rate, 2),
                'entries': entries[:50],
                'memory_estimate_kb': sum(len(str(e['value'])) for e in self._store.values()) / 1024
            }
    
    def reset_stats(self) -> None:
        """Reset hit/miss counters"""
        with self._lock:
            self._hit_count = 0
            self._miss_count = 0
            self._stats.clear()


app_cache = InMemoryCache()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()


def cached(ttl: int = 300, key_prefix: str = None):
    """
    Decorator to cache function results with TTL
    
    Usage:
        @cached(ttl=60, key_prefix='clients')
        def get_client_list():
            return db.query(Client).all()
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            prefix = key_prefix or f.__name__
            cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
            
            value, hit = app_cache.get(cache_key)
            if hit:
                g.cache_hit = True
                return value
            
            g.cache_hit = False
            result = f(*args, **kwargs)
            app_cache.set(cache_key, result, ttl)
            return result
        
        wrapper.cache_key_prefix = key_prefix or f.__name__
        wrapper.invalidate = lambda: app_cache.clear(f"{key_prefix or f.__name__}:*")
        return wrapper
    return decorator


def invalidate_cache(patterns: List[str]) -> int:
    """Invalidate cache entries matching any of the patterns"""
    total_cleared = 0
    for pattern in patterns:
        total_cleared += app_cache.clear(pattern)
    return total_cleared


class PerformanceService:
    """Service for tracking and analyzing application performance"""
    
    def __init__(self, db=None):
        self.db = db
        self._request_buffer: List[Dict] = []
        self._buffer_lock = threading.Lock()
        self._flush_interval = 60
        self._last_flush = datetime.utcnow()
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status: int,
        cache_hit: bool = False,
        error_message: str = None
    ) -> None:
        """Record a request for performance tracking"""
        with _metrics_lock:
            key = f"{method}:{endpoint}"
            
            metrics = _request_metrics[key]
            if len(metrics) >= _MAX_METRICS_PER_ENDPOINT:
                metrics.pop(0)
            
            metrics.append({
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': status,
                'cache_hit': cache_hit,
                'error': error_message,
                'is_error': status >= 400
            })
    
    def get_endpoint_metrics(self, endpoint: str = None, method: str = None) -> Dict:
        """Get performance metrics for an endpoint"""
        with _metrics_lock:
            if endpoint and method:
                key = f"{method}:{endpoint}"
                metrics = _request_metrics.get(key, [])
                return self._calculate_metrics(key, metrics)
            
            all_metrics = {}
            for key, metrics in _request_metrics.items():
                all_metrics[key] = self._calculate_metrics(key, metrics)
            return all_metrics
    
    def _calculate_metrics(self, key: str, metrics: List[Dict]) -> Dict:
        """Calculate performance statistics from raw metrics"""
        if not metrics:
            return {
                'endpoint': key,
                'request_count': 0,
                'avg_response_time_ms': 0,
                'p50_time': 0,
                'p95_time': 0,
                'p99_time': 0,
                'error_count': 0,
                'error_rate': 0,
                'cache_hit_count': 0,
                'cache_hit_rate': 0
            }
        
        durations = [m['duration_ms'] for m in metrics]
        sorted_durations = sorted(durations)
        
        error_count = sum(1 for m in metrics if m['is_error'])
        cache_hits = sum(1 for m in metrics if m['cache_hit'])
        
        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] + (data[c] - data[f]) * (k - f)
        
        return {
            'endpoint': key,
            'request_count': len(metrics),
            'avg_response_time_ms': round(statistics.mean(durations), 2),
            'min_response_time_ms': round(min(durations), 2),
            'max_response_time_ms': round(max(durations), 2),
            'p50_time': round(percentile(sorted_durations, 50), 2),
            'p95_time': round(percentile(sorted_durations, 95), 2),
            'p99_time': round(percentile(sorted_durations, 99), 2),
            'error_count': error_count,
            'error_rate': round(error_count / len(metrics) * 100, 2),
            'cache_hit_count': cache_hits,
            'cache_hit_rate': round(cache_hits / len(metrics) * 100, 2),
            'last_request': metrics[-1]['timestamp'].isoformat() if metrics else None
        }
    
    def get_slow_endpoints(self, threshold_ms: float = 100) -> List[Dict]:
        """Identify endpoints with average response time above threshold"""
        with _metrics_lock:
            slow_endpoints = []
            
            for key, metrics in _request_metrics.items():
                if not metrics:
                    continue
                
                stats = self._calculate_metrics(key, metrics)
                if stats['avg_response_time_ms'] > threshold_ms:
                    method, endpoint = key.split(':', 1)
                    
                    recommendations = []
                    if stats['cache_hit_rate'] < 50:
                        recommendations.append("Consider adding caching to this endpoint")
                    if stats['p99_time'] > stats['avg_response_time_ms'] * 3:
                        recommendations.append("High p99 variance - check for occasional slow queries")
                    if stats['error_rate'] > 5:
                        recommendations.append("High error rate - investigate error causes")
                    if stats['request_count'] > 100:
                        recommendations.append("High traffic endpoint - prioritize optimization")
                    
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'method': method,
                        'avg_response_time_ms': stats['avg_response_time_ms'],
                        'p95_time': stats['p95_time'],
                        'p99_time': stats['p99_time'],
                        'request_count': stats['request_count'],
                        'error_rate': stats['error_rate'],
                        'cache_hit_rate': stats['cache_hit_rate'],
                        'severity': 'critical' if stats['avg_response_time_ms'] > 500 else 
                                   'warning' if stats['avg_response_time_ms'] > 200 else 'info',
                        'recommendations': recommendations
                    })
            
            return sorted(slow_endpoints, key=lambda x: x['avg_response_time_ms'], reverse=True)
    
    def get_performance_summary(self, period_minutes: int = 60) -> Dict:
        """Get aggregated performance summary for a time period"""
        cutoff = datetime.utcnow() - timedelta(minutes=period_minutes)
        
        with _metrics_lock:
            all_requests = []
            endpoint_stats = []
            
            for key, metrics in _request_metrics.items():
                recent = [m for m in metrics if m['timestamp'] > cutoff]
                if recent:
                    all_requests.extend(recent)
                    stats = self._calculate_metrics(key, recent)
                    endpoint_stats.append(stats)
            
            total_requests = len(all_requests)
            total_errors = sum(1 for r in all_requests if r['is_error'])
            total_cache_hits = sum(1 for r in all_requests if r['cache_hit'])
            all_durations = [r['duration_ms'] for r in all_requests]
            
            return {
                'period_minutes': period_minutes,
                'period_start': cutoff.isoformat(),
                'period_end': datetime.utcnow().isoformat(),
                'total_requests': total_requests,
                'requests_per_minute': round(total_requests / period_minutes, 2) if period_minutes > 0 else 0,
                'avg_response_time_ms': round(statistics.mean(all_durations), 2) if all_durations else 0,
                'total_errors': total_errors,
                'error_rate': round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
                'cache_hit_rate': round(total_cache_hits / total_requests * 100, 2) if total_requests > 0 else 0,
                'unique_endpoints': len(endpoint_stats),
                'slowest_endpoints': sorted(endpoint_stats, key=lambda x: x['avg_response_time_ms'], reverse=True)[:5],
                'most_active_endpoints': sorted(endpoint_stats, key=lambda x: x['request_count'], reverse=True)[:5],
                'highest_error_endpoints': sorted(endpoint_stats, key=lambda x: x['error_rate'], reverse=True)[:5]
            }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return app_cache.get_stats()
    
    def clear_cache(self, pattern: str = None) -> Dict:
        """Clear cache entries matching pattern"""
        cleared = app_cache.clear(pattern)
        return {
            'success': True,
            'cleared_count': cleared,
            'pattern': pattern or '*'
        }
    
    def optimize_query(self, query_string: str) -> Dict:
        """Analyze a query string for optimization opportunities"""
        recommendations = []
        issues = []
        
        query_lower = query_string.lower()
        
        if 'select *' in query_lower:
            issues.append("Using SELECT * - specify needed columns instead")
            recommendations.append("Replace SELECT * with specific column names")
        
        if ' like ' in query_lower and '%' in query_string:
            if query_lower.count("'%") > 0:
                issues.append("LIKE with leading wildcard prevents index usage")
                recommendations.append("Consider full-text search or restructure query")
        
        if 'order by' in query_lower and 'limit' not in query_lower:
            issues.append("ORDER BY without LIMIT may sort entire table")
            recommendations.append("Add LIMIT clause if not all results needed")
        
        if query_lower.count(' join ') > 3:
            issues.append("Multiple JOINs can be slow")
            recommendations.append("Consider breaking into subqueries or using temp tables")
        
        if 'where' not in query_lower and ('update' in query_lower or 'delete' in query_lower):
            issues.append("UPDATE/DELETE without WHERE affects all rows")
            recommendations.append("Add WHERE clause to limit affected rows")
        
        if 'in (' in query_lower:
            in_values = re.findall(r'in\s*\([^)]+\)', query_lower)
            for in_clause in in_values:
                if in_clause.count(',') > 100:
                    issues.append("Large IN clause with many values")
                    recommendations.append("Consider using a temporary table or subquery")
        
        if 'or' in query_lower and 'where' in query_lower:
            issues.append("OR in WHERE clause may prevent index usage")
            recommendations.append("Consider using UNION or restructuring condition")
        
        return {
            'query': query_string[:500],
            'issues_found': len(issues),
            'issues': issues,
            'recommendations': recommendations,
            'optimization_score': max(0, 100 - (len(issues) * 15))
        }
    
    def get_database_stats(self) -> Dict:
        """Get database connection pool and performance stats"""
        try:
            from database import engine
            pool = engine.pool
            
            pool_stats = {
                'pool_size': pool.size(),
                'checked_out_connections': pool.checkedout(),
                'checked_in_connections': pool.checkedin(),
                'overflow': pool.overflow(),
                'invalid_connections': pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0
            }
            
            db_stats = {}
            if self.db:
                try:
                    result = self.db.execute("SELECT pg_database_size(current_database()) as size").fetchone()
                    if result:
                        db_stats['database_size_mb'] = round(result[0] / (1024 * 1024), 2)
                except:
                    pass
                
                try:
                    result = self.db.execute("""
                        SELECT state, count(*) as count 
                        FROM pg_stat_activity 
                        WHERE datname = current_database() 
                        GROUP BY state
                    """).fetchall()
                    db_stats['connection_states'] = {row[0] or 'null': row[1] for row in result}
                except:
                    pass
                
                try:
                    result = self.db.execute("""
                        SELECT 
                            relname as table_name,
                            n_live_tup as row_count,
                            n_dead_tup as dead_rows,
                            last_vacuum,
                            last_autovacuum
                        FROM pg_stat_user_tables
                        ORDER BY n_live_tup DESC
                        LIMIT 10
                    """).fetchall()
                    db_stats['top_tables'] = [
                        {
                            'table': row[0],
                            'rows': row[1],
                            'dead_rows': row[2],
                            'last_vacuum': row[3].isoformat() if row[3] else None,
                            'last_autovacuum': row[4].isoformat() if row[4] else None
                        }
                        for row in result
                    ]
                except:
                    pass
            
            return {
                'pool': pool_stats,
                'database': db_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'pool': {},
                'database': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_index_recommendations(self) -> List[Dict]:
        """Get recommendations for missing indices"""
        recommendations = []
        
        common_index_patterns = [
            {'table': 'clients', 'column': 'email', 'reason': 'Frequently queried for lookups'},
            {'table': 'clients', 'column': 'phone', 'reason': 'Used in search queries'},
            {'table': 'dispute_items', 'column': 'status', 'reason': 'Filtered by status frequently'},
            {'table': 'audit_logs', 'column': 'timestamp', 'reason': 'Time-range queries common'},
            {'table': 'cases', 'column': 'attorney_id', 'reason': 'Joined/filtered by attorney'},
            {'table': 'cases', 'column': 'status', 'reason': 'Pipeline stage filtering'},
            {'table': 'analyses', 'column': 'client_id', 'reason': 'Client lookup common'},
            {'table': 'credit_reports', 'column': 'client_id', 'reason': 'Client lookup common'}
        ]
        
        if self.db:
            try:
                result = self.db.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                """).fetchall()
                
                existing_indices = set()
                for row in result:
                    for col in common_index_patterns:
                        if col['table'] == row[1] and col['column'] in row[3].lower():
                            existing_indices.add(f"{col['table']}.{col['column']}")
                
                for pattern in common_index_patterns:
                    key = f"{pattern['table']}.{pattern['column']}"
                    if key not in existing_indices:
                        recommendations.append({
                            'table': pattern['table'],
                            'column': pattern['column'],
                            'reason': pattern['reason'],
                            'sql': f"CREATE INDEX CONCURRENTLY idx_{pattern['table']}_{pattern['column']} ON {pattern['table']}({pattern['column']});"
                        })
            except Exception as e:
                for pattern in common_index_patterns:
                    recommendations.append({
                        'table': pattern['table'],
                        'column': pattern['column'],
                        'reason': pattern['reason'],
                        'sql': f"CREATE INDEX CONCURRENTLY idx_{pattern['table']}_{pattern['column']} ON {pattern['table']}({pattern['column']});",
                        'note': 'Could not verify existing indices'
                    })
        
        return recommendations
    
    def clear_old_metrics(self, max_age_minutes: int = 60) -> int:
        """Clear metrics older than max_age_minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        cleared = 0
        
        with _metrics_lock:
            for key in list(_request_metrics.keys()):
                original_len = len(_request_metrics[key])
                _request_metrics[key] = [
                    m for m in _request_metrics[key] 
                    if m['timestamp'] > cutoff
                ]
                cleared += original_len - len(_request_metrics[key])
                
                if not _request_metrics[key]:
                    del _request_metrics[key]
        
        return cleared


_performance_service_instance = None


def get_performance_service(db=None) -> PerformanceService:
    """Get or create performance service singleton"""
    global _performance_service_instance
    if _performance_service_instance is None:
        _performance_service_instance = PerformanceService(db)
    elif db:
        _performance_service_instance.db = db
    return _performance_service_instance


def request_timing_middleware(app):
    """Flask middleware to track request timing and performance"""
    
    @app.before_request
    def before_request():
        g.request_start_time = time.time()
        g.cache_hit = False
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'request_start_time'):
            duration_ms = (time.time() - g.request_start_time) * 1000
            
            service = get_performance_service()
            service.record_request(
                endpoint=request.path,
                method=request.method,
                duration_ms=duration_ms,
                status=response.status_code,
                cache_hit=getattr(g, 'cache_hit', False)
            )
            
            if duration_ms > 100:
                print(f"⚠️  SLOW REQUEST: {request.method} {request.path} took {duration_ms:.2f}ms")
            
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            if getattr(g, 'cache_hit', False):
                response.headers['X-Cache'] = 'HIT'
        
        return response
    
    return app
