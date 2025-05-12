using System.Diagnostics;
using CPRM2.Areas.Identity.Data;
using CPRM2.Data;
using CPRM2.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using System.Linq;

namespace CPRM2.Controllers
{
    public class HomeController : Controller
    {
        private readonly CprmDbContext _context;
        private readonly UserManager<CPRM2User> _userManager;
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger, CprmDbContext context, UserManager<CPRM2User> userManager)
        {
            _logger = logger;
            _context = context;
            _userManager = userManager;
        }


        public IActionResult Index()
        {
            return View();
        }

        [Authorize(Roles = "Admin")]
        public IActionResult AdminDashboard()
        {
            var dashboardViewModel = new AdminDashboardViewModel
            {
                TotalOrders = _context.Orders.Count(),
                TotalProducts = _context.Products.Count(),
                TotalInventory = _context.Products.Sum(p => p.Quantity).Value,
                TotalAgents = _userManager.GetUsersInRoleAsync("Agent").Result.Count(),
                TotalAdmins = _userManager.GetUsersInRoleAsync("Admin").Result.Count(),
                PendingVerifications = _context.Users.Count(u => !u.EmailConfirmed),
                RecentOrders = _context.Orders
                    .OrderByDescending(o => o.OrderDate)
                    .Take(5)
                    .ToList(),
                LowStockProducts = _context.Products
                    .Where(p => p.Quantity < 10)
                    .OrderBy(p => p.Quantity)
                    .Take(5)
                    .ToList(),
                TotalRevenue = _context.Orders
                    .Where(o => o.OrderStatus == "Processing" || o.OrderStatus == "Dispatched")
                    .Sum(o => o.TotalAmount) ?? 0
            };

            return View(dashboardViewModel);
        }

        [Authorize(Roles = "Agent")]
        public IActionResult AgentDashboard()
        {

            return View();

        }

        public IActionResult Policies()
        {
            return View();
        }
        public IActionResult Trainings()
        {
            return View();
        }
        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
