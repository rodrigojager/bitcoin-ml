using Quartz;
using Microsoft.Extensions.Options;
using TechChallenge.Models;

namespace TechChallenge.Jobs
{
    public class TrainJob : IJob
    {
        private readonly IHttpClientFactory _http;
        private readonly ApiSettings _cfg;

        public TrainJob(IHttpClientFactory http, IOptions<ApiSettings> cfg)
        {
            _http = http;
            _cfg = cfg.Value;
        }

        public async Task Execute(IJobExecutionContext context)
        {
            var client = _http.CreateClient();
            try
            {
				// Treino do modelo
                await client.PostAsync($"{_cfg.BaseUrl}/train?days=90", null);
                // Materialização dos dados para gráficos rápidos
                await client.PostAsync($"{_cfg.BaseUrl}/series/rebuild", null);
            }
            catch
            {
            }
        }
    }
}
