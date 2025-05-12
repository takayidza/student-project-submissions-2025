using static DrugAlertSystem.Controllers.HomeController;

namespace DrugAlertSystem.Models
{

    public class DashboardViewModel
    {
        public int TotalReports { get; set; }
        public int ActiveCases { get; set; }
        public int UnderInvestigation { get; set; }
        public int ResolvedCases { get; set; }
        public int Hotspots { get; set; }
        public List<RecentReportDto> RecentReports { get; set; }
        public List<MapIncidentDto> MapIncidents { get; set; }
    }
}
