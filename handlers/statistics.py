import re
from datetime import datetime, timedelta

import base
import stats

PAT_HOST = re.compile('^[.a-zA-Z0-9]+$')

REDIS_MAX_FIELDS = [
    'used_cpu_sys', 'used_cpu_user', 'connected_clients',
    'total_commands_processed', 'evicted_keys', 'expired_keys',
    'keyspace_misses', 'keyspace_hits',
]
REDIS_AVG_FIELDS = ['used_memory', 'used_memory_rss', 'response_time']
PROXY_MAX_FIELDS = ['connected_clients', 'mem_buffer_alloc',
                    'completed_commands']
PROXY_AVG_FIELDS = ['command_elapse', 'remote_cost']


def init_handlers():
    @base.get('/stats/redis')
    def stats_redis_entry_page(request):
        return request.render('stats-redis.html', host=request.args['host'],
                              port=int(request.args['port']))

    @base.get('/stats/proxy')
    def stats_proxy_entry_page(request):
        return request.render('stats-proxy.html', host=request.args['host'],
                              port=int(request.args['port']))

    def _parse_args(args):
        host = args['host']
        if not PAT_HOST.match(host):
            raise ValueError('Invalid hostname')
        port = int(args['port'])
        limit = min(int(args.get('limit', 100)), 500)
        interval = max(int(args.get('interval', 2)), 1)
        return host, port, limit, interval, timedelta(minutes=limit * interval)

    @base.get_async('/stats/fetchproxy')
    def fetch_proxy_stats(request):
        host, port, limit, interval, span = _parse_args(request.args)
        now = datetime.utcnow()
        node = '%s:%d' % (host, port)
        result = {}

        for field in PROXY_MAX_FIELDS:
            result[field] = stats.client.query(
                node, field, 'max', span, now, interval)
        for field in PROXY_AVG_FIELDS:
            result[field] = stats.client.query(
                node, field, 'mean', span, now, interval)

        return base.json_result(result)

    @base.get_async('/stats/fetchredis')
    def fetch_stats(request):
        host, port, limit, interval, span = _parse_args(request.args)
        now = datetime.utcnow()
        node = '%s:%d' % (host, port)
        result = {}

        for field in REDIS_AVG_FIELDS:
            result[field] = stats.client.query(
                node, field, 'mean', span, now, interval)
        for field in REDIS_AVG_FIELDS:
            result[field] = stats.client.query(
                node, field, 'max', span, now, interval)

        return base.json_result(result)

if stats.client is not None:
    init_handlers()
