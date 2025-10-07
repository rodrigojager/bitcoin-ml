namespace TechChallenge.Models
{
    public class ApiSettings
    {
        public string BaseUrl { get; set; } = "http://pyapi:8000";
        public string IngestCron { get; set; } = "0 */5 * * * ?";
        public string TrainCron { get; set; } = "0 */15 * * * ?";
        public bool RunBackfillOnStartup { get; set; } = true;
        public int BackfillDays { get; set; } = 90;
        public double ExpectedCoverageRatio { get; set; } = 0.80;
        public int BackfillSleepMs { get; set; } = 500;
        public int BackfillLimit { get; set; } = 1000;
    }
}
