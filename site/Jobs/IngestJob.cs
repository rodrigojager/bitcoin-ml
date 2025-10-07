using Quartz;
using Microsoft.Extensions.Options;
using TechChallenge.Models;

namespace TechChallenge.Jobs
{
    public class IngestJob : IJob
    {
        private readonly IHttpClientFactory _http;
        private readonly ApiSettings _cfg;

        public IngestJob(IHttpClientFactory http, IOptions<ApiSettings> cfg)
        {
            _http = http;
            _cfg = cfg.Value;
        }

        public async Task Execute(IJobExecutionContext context)
        {
            var client = _http.CreateClient();
            try
            {
                await client.PostAsync($"{_cfg.BaseUrl}/ingest", null);
            }
            catch
            {
            }
        }
    }
}
