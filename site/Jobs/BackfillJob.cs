using Quartz;
using Microsoft.Extensions.Options;
using System.Net.Http.Json;
using TechChallenge.Models;

namespace TechChallenge.Jobs
{
    public class BackfillJob : IJob
    {
        private readonly IHttpClientFactory _http;
        private readonly ApiSettings _cfg;

        public BackfillJob(IHttpClientFactory http, IOptions<ApiSettings> cfg)
        {
            _http = http;
            _cfg = cfg.Value;
        }

        public async Task Execute(IJobExecutionContext context)
        {
            if (!_cfg.RunBackfillOnStartup) return;

            var client = _http.CreateClient();

            try
            {
                // 1) Checa cobertura simples via /series
                int days = Math.Min(_cfg.BackfillDays, 90);
                var series = await client.GetFromJsonAsync<SeriesResponse>($"{_cfg.BaseUrl}/series?fallback_days={days}");

                // Aprox: 90d de 5m ~ 25.920 pontos
                int expected = 25920 * days / 90;
                int got = series?.points?.Count ?? 0;
                double ratio = expected > 0 ? (double)got / expected : 0;

                if (ratio < _cfg.ExpectedCoverageRatio)
                {
                    await client.PostAsync($"{_cfg.BaseUrl}/init/backfill", null);
                    await client.PostAsync($"{_cfg.BaseUrl}/train?days={days}", null);
                }
            }
            catch
            {

            }
        }

        // Tipos p/ desserializar parcialmente o /series
        public class SeriesResponse { public List<PointItem> points { get; set; } = new(); }
        public class PointItem { public RealItem real { get; set; } = default!; }
        public class RealItem { public string time { get; set; } = ""; }
    }
}
