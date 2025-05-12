using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using CPRM2.Models;
using System;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using CPRM2.Data;

namespace CPRM2.Controllers
{
    [Authorize]
    public class ChatbotController : Controller
    {
        private readonly CprmDbContext _context;

        public ChatbotController(CprmDbContext context)
        {
            _context = context;
        }

        public IActionResult Index()
        {
            var userId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            var chatHistory = _context.ChatbotLogs
                .Where(c => c.UserId == userId)
                .OrderByDescending(c => c.Timestamp)
                .Take(50)
                .ToList();
            return View(chatHistory);
        }

        [HttpPost]
        public async Task<IActionResult> SendMessage(string message)
        {
            if (string.IsNullOrEmpty(message))
                return BadRequest("Message cannot be empty");

            var userId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            var response = GenerateResponse(message);

            var chatLog = new ChatbotLog
            {
                UserId = userId,
                Question = message,
                Answer = response,
                Timestamp = DateTime.UtcNow
            };

            _context.ChatbotLogs.Add(chatLog);
            await _context.SaveChangesAsync();

            return Json(new { response });
        }

        private string GenerateResponse(string message)
        {
            // Simple response generation logic - can be enhanced with AI/ML later
            message = message.ToLower();

            if (message.Contains("hello") || message.Contains("hi"))
                return "Hello! How can I help you today?";

            if (message.Contains("product") || message.Contains("catalog"))
                return "You can find our product catalog in the Products section. Would you like me to guide you there?";

            if (message.Contains("order") || message.Contains("purchase"))
                return "To place an order, please visit the Products section and click on the items you wish to purchase.";

            if (message.Contains("payment") || message.Contains("pay"))
                return "We accept various payment methods including mobile payments. You can complete your payment during checkout.";

            if (message.Contains("training") || message.Contains("resource"))
                return "Training materials and resources are available in the Resource Center. Would you like me to show you how to access them?";

            return "I'm not sure I understand. Could you please rephrase your question? You can ask me about products, orders, payments, or training materials.";
        }
    }
}