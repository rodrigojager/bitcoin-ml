using Quartz;
using TechChallenge.Models;
using TechChallenge.Services;
using TechChallenge.Jobs;
using static Quartz.Logging.OperationName;

var builder = WebApplication.CreateBuilder(args);

// Adiciona provider de variáveis de ambiente com separador __ (já padrão)
builder.Configuration.AddEnvironmentVariables();

// Registrar MarkdownService com caminho da pasta Docs
builder.Services.AddScoped<MarkdownService>(provider =>
{
    var env = provider.GetRequiredService<IWebHostEnvironment>();
    var logger = provider.GetRequiredService<ILogger<MarkdownService>>();
    var docsPath = Path.Combine(env.ContentRootPath, "Docs");
    return new MarkdownService(docsPath, logger);
});

// Options
builder.Services.Configure<ApiSettings>(builder.Configuration.GetSection("PythonApi"));

builder.Services.AddHttpClient();

// MVC + API
builder.Services.AddControllersWithViews();

// CORS
const string CorsPolicy = "FrontendCors";
builder.Services.AddCors(opts =>
{
    opts.AddPolicy(CorsPolicy, p => p
        // *** EM PRODUÇÃO TROQUE POR .WithOrigins("https://app.seudominio.com") ***
        .AllowAnyOrigin()
        .AllowAnyHeader()
        .AllowAnyMethod()
    );
});

// Quartz
builder.Services.AddQuartz(q =>
{
    q.UseMicrosoftDependencyInjectionJobFactory();

    // Backfill uma vez no startup
    var backfillKey = new JobKey("BackfillJob");
    q.AddJob<BackfillJob>(opts => opts.WithIdentity(backfillKey).StoreDurably());
    q.AddTrigger(t => t.ForJob(backfillKey)
        .WithIdentity("BackfillTrigger")
        .StartNow()
        .WithSimpleSchedule(x => x.WithRepeatCount(0)));

    // Ingest periódico
    var ingestKey = new JobKey("IngestJob");
    q.AddJob<IngestJob>(opts => opts.WithIdentity(ingestKey));
    q.AddTrigger(t => t.ForJob(ingestKey)
        .WithIdentity("IngestTrigger")
        .WithCronSchedule(builder.Configuration["PythonApi:IngestCron"] ?? "0 */5 * * * ?"));

    // Train periódico
    var trainKey = new JobKey("TrainJob");
    q.AddJob<TrainJob>(opts => opts.WithIdentity(trainKey));
    q.AddTrigger(t => t.ForJob(trainKey)
        .WithIdentity("TrainTrigger")
        .WithCronSchedule(builder.Configuration["PythonApi:TrainCron"] ?? "0 */15 * * * ?"));
});
builder.Services.AddQuartzHostedService(q => q.WaitForJobsToComplete = true);


var app = builder.Build();


app.UseDeveloperExceptionPage();


// HTTPS + ARQUIVOS ESTÁTICOS
var enableHttpsRedirect = Environment.GetEnvironmentVariable("ENABLE_HTTPS_REDIRECT");
if (string.Equals(enableHttpsRedirect, "true", StringComparison.OrdinalIgnoreCase))
{
    app.UseHttpsRedirection();
}
app.UseStaticFiles();

// ROTEAMENTO
app.UseRouting();

// CORS
app.UseCors(CorsPolicy);

//--------------------------------------------------------------------------
// 3) ENDPOINTS
//--------------------------------------------------------------------------

// ROTAS MVC CONVENCIONAIS
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Docs}/{action=Index}/{id?}")
    .WithStaticAssets();

// ATRIBUTO ROUTING API CONTROLLERS
app.MapControllers();

// ESTÁTICOS VIA Manifests (se estiver usando)
app.MapStaticAssets();

app.Run();

