using System.Diagnostics;
using DrugAlertSystem.Data;
using DrugAlertSystem.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Controllers
{

    [Authorize]
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly DrugsDbContext _context;

        public HomeController(ILogger<HomeController> logger, DrugsDbContext context)
        {
            _logger = logger;
            _context = context;
        }

        public async Task<IActionResult> Index()
        {
            // Fetch counts in a single query
            var reportCounts = await _context.Reports
                .GroupBy(r => 1) // Groups everything into one row
                .Select(g => new
                {
                    Total = g.Count(),
                    Active = g.Count(r => r.Status == "Pending" ),
                    UnderInvestigation = g.Count(r => r.Status == "Under Investigation"),
                    Resolved = g.Count(r => r.Status == "Resolved")
                })
                .FirstOrDefaultAsync();

            var totalReports = reportCounts?.Total ?? 0;
            var activeCases = reportCounts?.Active ?? 0;
            var underInvestigation = reportCounts?.UnderInvestigation ?? 0;
            var resolvedCases = reportCounts?.Resolved ?? 0;

            // Identify hotspots (locations with 3+ reports)
            var hotspots = await _context.Reports
                .GroupBy(r => new { r.Latitude, r.Longitude })
                .Where(g => g.Count() >= 3)
                .CountAsync();

            // Fetch recent reports (latest 3)
            var recentReports = await _context.Reports
                .OrderByDescending(r => r.CreatedAt)
                .Take(3)
                .Select(r => new RecentReportDto
                {
                    ReportId = "#" + r.Id.ToString().Substring(0, 6),
                    ReportType = r.ReportType,
                    Location = "Unknown", // Placeholder, needs geocoding if addresses are stored
                    Status = r.Status,
                    ReportedAt = r.CreatedAt.Value.ToString("yyyy-MM-dd hh:mm tt")
                })
                .ToListAsync();

            // Map data (load reports with location)
            var mapIncidents = await _context.Reports
                .Select(r => new MapIncidentDto
                {
                    Latitude = r.Latitude,
                    Longitude = r.Longitude,
                    Type = r.ReportType,
                    Color = r.Status == "Pending" ? "yellow" :
                            r.Status == "Resolved" ? "green" :
                            r.Status == "Under Investigation" ? "red" : "blue"
                })
                .ToListAsync();

            var dashboardModel = new DashboardViewModel
            {
                TotalReports = totalReports,
                ActiveCases = activeCases,
                UnderInvestigation = underInvestigation,
                ResolvedCases = resolvedCases,
                Hotspots = hotspots,
                RecentReports = recentReports,
                MapIncidents = mapIncidents
            };

            return View(dashboardModel);
        }

[AllowAnonymous]
        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }


        // DTO for Recent Reports Table
        public class RecentReportDto
        {
            public string ReportId { get; set; }
            public string ReportType { get; set; }
            public string Location { get; set; }
            public string Status { get; set; }
            public string ReportedAt { get; set; }
        }

        // DTO for Map Data
        public class MapIncidentDto
        {
            public double Latitude { get; set; }
            public double Longitude { get; set; }
            public string Type { get; set; }
            public string Color { get; set; }
        }

    }
}
