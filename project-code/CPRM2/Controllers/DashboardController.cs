using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using CPRM2.Models;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using CPRM2.Data;

namespace CPRM2.Controllers
{
    [Authorize]
    public class DashboardController : Controller
    {
        private readonly CprmDbContext _context;

        public DashboardController(CprmDbContext context)
        {
            _context = context;
        }

        public async Task<IActionResult> Index()
        {
            if (User.IsInRole("Admin"))
            {
                //return RedirectToAction(nameof(AdminDashboard));
            }

            return Ok("Coming soon");
         //   return RedirectToAction(nameof(AgentDashboard));
        }

        //[Authorize(Roles = "Admin")]
        //public async Task<IActionResult> AdminDashboard()
        //{
        //    var viewModel = new AdminDashboardViewModel
        //    {
        //        TotalAgents = await _context.Users.CountAsync(u => u.Role == "Agent"),
        //        PendingVerifications = await _context.Users.CountAsync(u => u.Role == "Agent" && !u.IsVerified),
        //        RecentOrders = await _context.Orders
        //            .Include(o => o.User)
        //            .OrderByDescending(o => o.OrderDate)
        //            .Take(5)
        //            .ToListAsync(),
        //        RecentChatLogs = await _context.ChatbotLogs
        //            .Include(c => c.User)
        //            .OrderByDescending(c => c.Timestamp)
        //            .Take(5)
        //            .ToListAsync()
        //    };

        //    return View(viewModel);
        //}

        //[Authorize(Roles = "Agent")]
        //public async Task<IActionResult> AgentDashboard()
        //{
        //    var userId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;

        //    var viewModel = new AgentDashboardViewModel
        //    {
        //        RecentOrders = await _context.Orders
        //            .Where(o => o.UserId == userId)
        //            .OrderByDescending(o => o.OrderDate)
        //            .Take(5)
        //            .ToListAsync(),
        //        AvailableProducts = await _context.Products
        //            .Where(p => p.IsAvailable)
        //            .Take(5)
        //            .ToListAsync(),
        //        RecentResources = await _context.Resources
        //            .OrderByDescending(r => r.UploadDate)
        //            .Take(5)
        //            .ToListAsync()
        //    };

        //    return View(viewModel);
        //}
  
    }
 
    public class AgentDashboardViewModel
    {
        public List<Order> RecentOrders { get; set; }
        public List<Product> AvailableProducts { get; set; }
        public List<Resource> RecentResources { get; set; }
    }
}